import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest


REPOSITORY_ROOT = Path(__file__).parents[2]
REMEMBER_ENABLED_ENV = "MNEMOSYNE_MEMORY_REMEMBER_ENABLED"
MEMORY_ROOT_ENV = "MNEMOSYNE_MEMORY_ROOT"

STARTUP_PROBE = """
import json

from mnemosyne.mcp.methods import handle_message


def request(message):
    response = handle_message(message)
    return json.loads(response.body)


tools_list = request({"id": "tools", "method": "tools/list"})
list_tools = request(
    {
        "id": "list-tool",
        "method": "tools/call",
        "params": {"name": "list_tools", "arguments": {}},
    }
)
inspect = request(
    {
        "id": "inspect",
        "method": "tools/call",
        "params": {
            "name": "memory_inspect",
            "arguments": {
                "reference": {
                    "schema_version": 1,
                    "scope": "project",
                    "id": "missing"
                }
            },
        },
    }
)
remember = request(
    {
        "id": "remember",
        "method": "tools/call",
        "params": {"name": "memory_remember", "arguments": {}},
    }
)
print(
    json.dumps(
        {
            "tool_names": [
                tool["name"] for tool in tools_list["result"]["tools"]
            ],
            "list_tools_text": list_tools["result"]["content"][0]["text"],
            "inspect": inspect,
            "remember": remember,
        },
        sort_keys=True,
    )
)
"""

STARTUP_FIXED_PROBE = """
import json
from pathlib import Path

from mnemosyne.mcp.methods import handle_message


def tool_names():
    response = handle_message({"id": "tools", "method": "tools/list"})
    body = json.loads(response.body)
    return [tool["name"] for tool in body["result"]["tools"]]


before = tool_names()
(Path.home() / ".mnemosyne" / "config.toml").write_text(
    "[memory]\\nremember_enabled = false\\n",
    encoding="utf-8",
)
after = tool_names()
print(json.dumps({"before": before, "after": after}, sort_keys=True))
"""


def _write_settings(home: Path, source: str) -> Path:
    application_directory = home / ".mnemosyne"
    application_directory.mkdir(mode=0o700)
    application_directory.chmod(0o700)
    settings_path = application_directory / "config.toml"
    settings_path.write_text(source, encoding="utf-8")
    settings_path.chmod(0o600)
    return settings_path


def _isolated_environment(
    home: Path,
    *,
    remember_override: str | None = None,
) -> dict[str, str]:
    environment = os.environ.copy()
    environment["HOME"] = str(home)
    environment.pop(MEMORY_ROOT_ENV, None)
    environment.pop(REMEMBER_ENABLED_ENV, None)
    if remember_override is not None:
        environment[REMEMBER_ENABLED_ENV] = remember_override
    existing_python_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(REPOSITORY_ROOT)
    if existing_python_path:
        environment["PYTHONPATH"] += os.pathsep + existing_python_path
    return environment


def _run_probe(
    home: Path,
    *,
    remember_override: str | None = None,
    probe: str = STARTUP_PROBE,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", probe],
        cwd=REPOSITORY_ROOT,
        env=_isolated_environment(
            home,
            remember_override=remember_override,
        ),
        capture_output=True,
        text=True,
        check=False,
    )


def _probe_result(process: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    assert process.returncode == 0, process.stderr
    return json.loads(process.stdout)


def test_file_enabled_startup_exposes_discovery_and_dispatch_without_writes(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    settings_path = _write_settings(
        home,
        "[memory]\nremember_enabled = true\n",
    )

    result = _probe_result(_run_probe(home))

    assert result["tool_names"] == [
        "list_tools",
        "memory_recall",
        "memory_inspect",
        "memory_remember",
    ]
    assert result["list_tools_text"] == (
        "Available tools: list_tools, memory_recall, memory_inspect, memory_remember"
    )
    inspect_result = result["inspect"]["result"]
    assert inspect_result["isError"] is True
    assert json.loads(inspect_result["content"][0]["text"])["code"] == "not_found"
    remember_result = result["remember"]["result"]
    assert remember_result["isError"] is True
    assert json.loads(remember_result["content"][0]["text"])["code"] == (
        "invalid_origin"
    )
    assert settings_path.read_text(encoding="utf-8") == (
        "[memory]\nremember_enabled = true\n"
    )
    assert not (home / ".mnemosyne" / "memory").exists()


@pytest.mark.parametrize("file_state", ["missing", "false"])
def test_disabled_startup_omits_remember_and_creates_no_paths(
    file_state: str,
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    if file_state == "false":
        _write_settings(home, "[memory]\nremember_enabled = false\n")

    result = _probe_result(_run_probe(home))

    assert result["tool_names"] == [
        "list_tools",
        "memory_recall",
        "memory_inspect",
    ]
    assert result["list_tools_text"] == (
        "Available tools: list_tools, memory_recall, memory_inspect"
    )
    inspect_result = result["inspect"]["result"]
    assert inspect_result["isError"] is True
    assert json.loads(inspect_result["content"][0]["text"])["code"] == "not_found"
    assert result["remember"]["error"] == {
        "code": -32602,
        "message": "Unknown tool: memory_remember",
    }
    if file_state == "missing":
        assert not (home / ".mnemosyne").exists()
    assert not (home / ".mnemosyne" / "memory").exists()


@pytest.mark.parametrize(
    ("file_source", "environment_value", "remember_available"),
    [
        ("[memory]\nremember_enabled = true\n", "false", False),
        ("private-invalid-file-content", "true", True),
    ],
)
def test_startup_environment_override_precedes_the_file(
    file_source: str,
    environment_value: str,
    remember_available: bool,
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    _write_settings(home, file_source)

    result = _probe_result(
        _run_probe(home, remember_override=environment_value)
    )

    assert ("memory_remember" in result["tool_names"]) is remember_available
    assert "private-invalid-file-content" not in result["list_tools_text"]
    assert not (home / ".mnemosyne" / "memory").exists()


def test_invalid_file_fails_startup_without_exposing_content(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    marker = "private-invalid-file-content"
    settings_path = _write_settings(home, f"[memory\n# {marker}\n")

    process = _run_probe(home)

    output = process.stdout + process.stderr
    assert process.returncode != 0
    assert "Mnemosyne settings file is not valid TOML" in output
    assert marker not in output
    assert str(settings_path) not in output
    assert not (home / ".mnemosyne" / "memory").exists()


def test_invalid_environment_fails_before_reading_a_valid_file(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    marker = "private-invalid-environment-value"
    _write_settings(home, "[memory]\nremember_enabled = true\n")

    process = _run_probe(home, remember_override=marker)

    output = process.stdout + process.stderr
    assert process.returncode != 0
    assert (
        "MNEMOSYNE_MEMORY_REMEMBER_ENABLED must be 'true' or 'false'"
        in output
    )
    assert marker not in output
    assert not (home / ".mnemosyne" / "memory").exists()


def test_registry_selection_remains_fixed_until_a_fresh_startup(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    _write_settings(home, "[memory]\nremember_enabled = true\n")

    fixed_result = _probe_result(
        _run_probe(home, probe=STARTUP_FIXED_PROBE)
    )

    assert fixed_result["before"] == [
        "list_tools",
        "memory_recall",
        "memory_inspect",
        "memory_remember",
    ]
    assert fixed_result["after"] == fixed_result["before"]

    restarted_result = _probe_result(_run_probe(home))
    assert restarted_result["tool_names"] == [
        "list_tools",
        "memory_recall",
        "memory_inspect",
    ]
    assert not (home / ".mnemosyne" / "memory").exists()

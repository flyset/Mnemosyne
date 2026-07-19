import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest


REPOSITORY_ROOT = Path(__file__).parents[2]
REMEMBER_ENABLED_ENV = "MNEMOSYNE_MEMORY_REMEMBER_ENABLED"
ARCHIVE_RESTORE_ENABLED_ENV = "MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED"
FORGET_ENABLED_ENV = "MNEMOSYNE_MEMORY_FORGET_ENABLED"
REVISE_ENABLED_ENV = "MNEMOSYNE_MEMORY_REVISE_ENABLED"
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
listing = request(
    {
        "id": "list",
        "method": "tools/call",
        "params": {
            "name": "memory_list",
            "arguments": {"scope": "project"},
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
archive = request(
    {
        "id": "archive",
        "method": "tools/call",
        "params": {"name": "memory_archive", "arguments": {}},
    }
)
restore = request(
    {
        "id": "restore",
        "method": "tools/call",
        "params": {"name": "memory_restore", "arguments": {}},
    }
)
revise = request(
    {
        "id": "revise",
        "method": "tools/call",
        "params": {"name": "memory_revise", "arguments": {}},
    }
)
forget = request(
    {
        "id": "forget",
        "method": "tools/call",
        "params": {"name": "memory_forget", "arguments": {}},
    }
)
print(
    json.dumps(
        {
            "tool_names": [
                tool["name"] for tool in tools_list["result"]["tools"]
            ],
            "list_tools_text": list_tools["result"]["content"][0]["text"],
            "listing": listing,
            "inspect": inspect,
            "remember": remember,
            "archive": archive,
            "restore": restore,
            "revise": revise,
            "forget": forget,
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
    "[memory]\\nremember_enabled = false\\narchive_restore_enabled = false\\nforget_enabled = false\\nrevise_enabled = false\\n",
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
    archive_restore_override: str | None = None,
    forget_override: str | None = None,
    revise_override: str | None = None,
) -> dict[str, str]:
    environment = os.environ.copy()
    environment["HOME"] = str(home)
    environment.pop(MEMORY_ROOT_ENV, None)
    environment.pop(REMEMBER_ENABLED_ENV, None)
    environment.pop(ARCHIVE_RESTORE_ENABLED_ENV, None)
    environment.pop(FORGET_ENABLED_ENV, None)
    environment.pop(REVISE_ENABLED_ENV, None)
    if remember_override is not None:
        environment[REMEMBER_ENABLED_ENV] = remember_override
    if archive_restore_override is not None:
        environment[ARCHIVE_RESTORE_ENABLED_ENV] = archive_restore_override
    if forget_override is not None:
        environment[FORGET_ENABLED_ENV] = forget_override
    if revise_override is not None:
        environment[REVISE_ENABLED_ENV] = revise_override
    existing_python_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(REPOSITORY_ROOT)
    if existing_python_path:
        environment["PYTHONPATH"] += os.pathsep + existing_python_path
    return environment


def _run_probe(
    home: Path,
    *,
    remember_override: str | None = None,
    archive_restore_override: str | None = None,
    forget_override: str | None = None,
    revise_override: str | None = None,
    probe: str = STARTUP_PROBE,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", probe],
        cwd=REPOSITORY_ROOT,
        env=_isolated_environment(
            home,
            remember_override=remember_override,
            archive_restore_override=archive_restore_override,
            forget_override=forget_override,
            revise_override=revise_override,
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
        "memory_list",
        "memory_inspect",
        "memory_remember",
    ]
    assert result["list_tools_text"] == (
        "Server: mnemosyne 0.1.1. Available tools: "
        "list_tools, memory_recall, memory_list, "
        "memory_inspect, memory_remember"
    )
    assert json.loads(result["listing"]["result"]["content"][0]["text"])[
        "status"
    ] == "ok"
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
        "memory_list",
        "memory_inspect",
    ]
    assert result["list_tools_text"] == (
        "Server: mnemosyne 0.1.1. Available tools: "
        "list_tools, memory_recall, memory_list, memory_inspect"
    )
    assert json.loads(result["listing"]["result"]["content"][0]["text"])[
        "status"
    ] == "ok"
    inspect_result = result["inspect"]["result"]
    assert inspect_result["isError"] is True
    assert json.loads(inspect_result["content"][0]["text"])["code"] == "not_found"
    assert result["remember"]["error"] == {
        "code": -32602,
        "message": "Unknown tool: memory_remember",
    }
    assert result["archive"]["error"]["message"] == "Unknown tool: memory_archive"
    assert result["restore"]["error"]["message"] == "Unknown tool: memory_restore"
    assert result["revise"]["error"]["message"] == "Unknown tool: memory_revise"
    assert result["forget"]["error"]["message"] == "Unknown tool: memory_forget"
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
        _run_probe(
            home,
            remember_override=environment_value,
            archive_restore_override=(
                "false" if file_source == "private-invalid-file-content" else None
            ),
            forget_override=(
                "false" if file_source == "private-invalid-file-content" else None
            ),
            revise_override=(
                "false" if file_source == "private-invalid-file-content" else None
            ),
        )
    )

    assert ("memory_remember" in result["tool_names"]) is remember_available
    assert "private-invalid-file-content" not in result["list_tools_text"]
    assert not (home / ".mnemosyne" / "memory").exists()


@pytest.mark.parametrize("source", ["file", "environment"])
def test_archive_restore_enablement_exposes_both_discovery_surfaces_and_dispatch(
    source: str,
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    override = None
    if source == "file":
        _write_settings(home, "[memory]\narchive_restore_enabled = true\n")
    else:
        override = "true"

    result = _probe_result(
        _run_probe(home, archive_restore_override=override)
    )

    assert result["tool_names"] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
        "memory_archive",
        "memory_restore",
    ]
    assert result["list_tools_text"] == (
        "Server: mnemosyne 0.1.1. Available tools: "
        "list_tools, memory_recall, memory_list, "
        "memory_inspect, memory_archive, memory_restore"
    )
    for operation in ("archive", "restore"):
        tool_result = result[operation]["result"]
        assert tool_result["isError"] is True
        assert json.loads(tool_result["content"][0]["text"])["code"] == (
            "invalid_reference"
        )
    assert result["remember"]["error"]["message"] == (
        "Unknown tool: memory_remember"
    )
    assert not (home / ".mnemosyne" / "memory").exists()


def test_archive_restore_and_remember_enablement_are_independent(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    _write_settings(
        home,
        "[memory]\nremember_enabled = true\narchive_restore_enabled = true\n",
    )

    result = _probe_result(_run_probe(home))

    assert result["tool_names"] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
        "memory_archive",
        "memory_restore",
        "memory_remember",
    ]


@pytest.mark.parametrize("source", ["file", "environment"])
def test_revise_enablement_exposes_both_discovery_surfaces_and_dispatch(
    source: str,
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    override = None
    if source == "file":
        _write_settings(home, "[memory]\nrevise_enabled = true\n")
    else:
        override = "true"

    result = _probe_result(_run_probe(home, revise_override=override))

    assert result["tool_names"] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
        "memory_revise",
    ]
    assert result["list_tools_text"] == (
        "Server: mnemosyne 0.1.1. Available tools: "
        "list_tools, memory_recall, memory_list, "
        "memory_inspect, memory_revise"
    )
    revise_result = result["revise"]["result"]
    assert revise_result["isError"] is True
    assert json.loads(revise_result["content"][0]["text"])["code"] == (
        "invalid_reference"
    )
    for operation in ("remember", "archive", "restore", "forget"):
        assert result[operation]["error"]["message"] == (
            f"Unknown tool: memory_{operation}"
        )
    assert not (home / ".mnemosyne" / "memory").exists()


@pytest.mark.parametrize("source", ["file", "environment"])
def test_forget_enablement_exposes_both_discovery_surfaces_and_dispatch(
    source: str,
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    override = None
    if source == "file":
        _write_settings(home, "[memory]\nforget_enabled = true\n")
    else:
        override = "true"

    result = _probe_result(_run_probe(home, forget_override=override))

    assert result["tool_names"] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
        "memory_forget",
    ]
    assert result["list_tools_text"] == (
        "Server: mnemosyne 0.1.1. Available tools: "
        "list_tools, memory_recall, memory_list, "
        "memory_inspect, memory_forget"
    )
    forget_result = result["forget"]["result"]
    assert forget_result["isError"] is True
    assert json.loads(forget_result["content"][0]["text"])["code"] == (
        "invalid_reference"
    )
    assert result["remember"]["error"]["message"] == (
        "Unknown tool: memory_remember"
    )
    assert result["archive"]["error"]["message"] == "Unknown tool: memory_archive"
    assert result["restore"]["error"]["message"] == "Unknown tool: memory_restore"
    assert not (home / ".mnemosyne" / "memory").exists()


def test_all_mutation_enablement_is_independent_and_forget_is_last(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    _write_settings(
        home,
        "[memory]\nremember_enabled = true\narchive_restore_enabled = true\nforget_enabled = true\nrevise_enabled = true\n",
    )

    result = _probe_result(_run_probe(home))

    assert result["tool_names"] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
        "memory_archive",
        "memory_restore",
        "memory_remember",
        "memory_revise",
        "memory_forget",
    ]


def test_invalid_archive_restore_environment_fails_before_file_access(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    marker = "private-invalid-archive-restore-value"
    _write_settings(home, "private-invalid-file-content")

    process = _run_probe(home, archive_restore_override=marker)

    output = process.stdout + process.stderr
    assert process.returncode != 0
    assert (
        "MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED must be 'true' or 'false'"
        in output
    )
    assert marker not in output
    assert "private-invalid-file-content" not in output


def test_invalid_forget_environment_fails_before_file_access(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    marker = "private-invalid-forget-value"
    _write_settings(home, "private-invalid-file-content")

    process = _run_probe(home, forget_override=marker)

    output = process.stdout + process.stderr
    assert process.returncode != 0
    assert "MNEMOSYNE_MEMORY_FORGET_ENABLED must be 'true' or 'false'" in output
    assert marker not in output
    assert "private-invalid-file-content" not in output


def test_invalid_revise_environment_fails_before_file_access(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    marker = "private-invalid-revise-value"
    _write_settings(home, "private-invalid-file-content")

    process = _run_probe(home, revise_override=marker)

    output = process.stdout + process.stderr
    assert process.returncode != 0
    assert "MNEMOSYNE_MEMORY_REVISE_ENABLED must be 'true' or 'false'" in output
    assert marker not in output
    assert "private-invalid-file-content" not in output


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
        "memory_list",
        "memory_inspect",
        "memory_remember",
    ]
    assert fixed_result["after"] == fixed_result["before"]

    restarted_result = _probe_result(_run_probe(home))
    assert restarted_result["tool_names"] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
    ]
    assert not (home / ".mnemosyne" / "memory").exists()


def test_archive_restore_registry_selection_remains_fixed_until_restart(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    _write_settings(home, "[memory]\narchive_restore_enabled = true\n")

    fixed_result = _probe_result(
        _run_probe(home, probe=STARTUP_FIXED_PROBE)
    )

    assert fixed_result["before"] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
        "memory_archive",
        "memory_restore",
    ]
    assert fixed_result["after"] == fixed_result["before"]

    restarted_result = _probe_result(_run_probe(home))
    assert restarted_result["tool_names"] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
    ]
    assert not (home / ".mnemosyne" / "memory").exists()


def test_forget_registry_selection_remains_fixed_until_restart(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    _write_settings(home, "[memory]\nforget_enabled = true\n")

    fixed_result = _probe_result(
        _run_probe(home, probe=STARTUP_FIXED_PROBE)
    )

    assert fixed_result["before"] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
        "memory_forget",
    ]
    assert fixed_result["after"] == fixed_result["before"]

    restarted_result = _probe_result(_run_probe(home))
    assert restarted_result["tool_names"] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
    ]
    assert not (home / ".mnemosyne" / "memory").exists()


def test_revise_registry_selection_remains_fixed_until_restart(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    _write_settings(home, "[memory]\nrevise_enabled = true\n")

    fixed_result = _probe_result(_run_probe(home, probe=STARTUP_FIXED_PROBE))

    assert fixed_result["before"] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
        "memory_revise",
    ]
    assert fixed_result["after"] == fixed_result["before"]

    restarted_result = _probe_result(_run_probe(home))
    assert restarted_result["tool_names"] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
    ]
    assert not (home / ".mnemosyne" / "memory").exists()

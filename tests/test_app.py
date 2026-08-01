import os
from pathlib import Path
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

import mymcp.app as app_module
from mymcp.app import create_app
from mymcp.host import bootstrap
from mymcp.host.configuration import HostConfiguration
from mymcp.mcp.tool_registry import ToolRegistration, ToolRegistry
from mymcp.settings import PROTOCOL_VERSION, SERVER_NAME, SERVER_VERSION


@dataclass(frozen=True)
class SyntheticRuntime:
    registry: ToolRegistry


def _runtime(name: str, calls: list[dict[str, Any]]) -> SyntheticRuntime:
    def handler(arguments: dict[str, Any]) -> dict[str, Any]:
        calls.append(arguments)
        return {"content": [], "runtime": name}

    return SyntheticRuntime(
        ToolRegistry(
            (
                ToolRegistration(
                    tool={
                        "name": name,
                        "description": f"Synthetic {name} Tool.",
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                    handler=handler,
                ),
            )
        )
    )


def test_two_apps_use_only_their_explicit_runtime() -> None:
    first_calls: list[dict[str, Any]] = []
    second_calls: list[dict[str, Any]] = []
    first = TestClient(create_app(_runtime("first", first_calls)))
    second = TestClient(create_app(_runtime("second", second_calls)))

    assert first.post("/mcp", json={"id": 1, "method": "tools/list"}).json()[
        "result"
    ]["tools"][0]["name"] == "first"
    assert second.post("/mcp", json={"id": 2, "method": "tools/list"}).json()[
        "result"
    ]["tools"][0]["name"] == "second"
    assert first.post(
        "/mcp",
        json={
            "id": 3,
            "method": "tools/call",
            "params": {"name": "first", "arguments": {"value": 1}},
        },
    ).json()["result"] == {"content": [], "runtime": "first"}
    assert second.post(
        "/mcp",
        json={
            "id": 4,
            "method": "tools/call",
            "params": {"name": "first", "arguments": {}},
        },
    ).json()["error"]["code"] == -32602
    assert first_calls == [{"value": 1}]
    assert second_calls == []


def test_explicit_runtime_app_preserves_operational_routes() -> None:
    client = TestClient(create_app(_runtime("first", [])))

    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/version").json() == {
        "name": SERVER_NAME,
        "version": SERVER_VERSION,
        "protocolVersion": PROTOCOL_VERSION,
    }


def test_create_app_requires_runtime_and_module_exports_no_global_app() -> None:
    with pytest.raises(TypeError):
        create_app()  # type: ignore[call-arg]

    assert not hasattr(app_module, "app")


def test_production_app_uses_injected_configuration_without_loading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = _runtime("production", [])
    application = object()
    configuration = HostConfiguration.default()
    bootstrap_calls = 0
    app_calls: list[object] = []

    def build_runtime(selected_configuration):
        nonlocal bootstrap_calls
        bootstrap_calls += 1
        assert selected_configuration is configuration
        return runtime

    def build_app(selected_runtime):
        app_calls.append(selected_runtime)
        return application

    monkeypatch.setattr(bootstrap, "build_production_runtime", build_runtime)
    monkeypatch.setattr(app_module, "create_app", build_app)
    monkeypatch.setattr(
        app_module,
        "load_host_configuration",
        lambda: pytest.fail("injected configuration must bypass loading"),
    )

    assert app_module.create_production_app(configuration) is application
    assert bootstrap_calls == 1
    assert app_calls == [runtime]


def test_production_app_loads_configuration_once_when_not_injected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = _runtime("production", [])
    application = object()
    configuration = HostConfiguration.default()
    loader_calls = 0

    def load_configuration():
        nonlocal loader_calls
        loader_calls += 1
        return configuration

    monkeypatch.setattr(app_module, "load_host_configuration", load_configuration)
    monkeypatch.setattr(
        bootstrap,
        "build_production_runtime",
        lambda selected: runtime if selected is configuration else pytest.fail(),
    )
    monkeypatch.setattr(app_module, "create_app", lambda selected: application)

    assert app_module.create_production_app() is application
    assert loader_calls == 1


def test_runtime_requests_never_reload_host_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = _runtime("production", [])
    configuration = HostConfiguration.default()
    loader_calls = 0

    def load_configuration():
        nonlocal loader_calls
        loader_calls += 1
        if loader_calls > 1:
            pytest.fail("runtime request reloaded host configuration")
        return configuration

    monkeypatch.setattr(app_module, "load_host_configuration", load_configuration)
    monkeypatch.setattr(bootstrap, "build_production_runtime", lambda selected: runtime)
    client = TestClient(app_module.create_production_app())

    assert client.get("/health").status_code == 200
    assert client.post("/mcp", json={"id": 1, "method": "tools/list"}).status_code == 200
    assert loader_calls == 1


def test_existing_application_is_stable_after_configuration_file_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "xdg"
    application_directory = selected / "mymcp"
    application_directory.mkdir(mode=0o700, parents=True)
    application_directory.chmod(0o700)
    configuration_path = application_directory / "config.toml"
    configuration_path.write_text("schema_version = 1\n", encoding="utf-8")
    configuration_path.chmod(0o600)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))
    monkeypatch.setenv("MNEMOSYNE_MEMORY_REMEMBER_ENABLED", "false")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED", "false")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_REVISE_ENABLED", "false")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_FORGET_ENABLED", "false")

    client = TestClient(app_module.create_production_app())
    configuration_path.write_text(
        'schema_version = 1\n[[plugins]]\nid = "external"\nenabled = true\n',
        encoding="utf-8",
    )
    configuration_path.chmod(0o600)

    response = client.post("/mcp", json={"id": 1, "method": "tools/list"})
    assert response.status_code == 200
    assert [tool["name"] for tool in response.json()["result"]["tools"]] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
    ]


def test_ordinary_imports_do_not_read_invalid_host_configuration(
    tmp_path: Path,
) -> None:
    selected = tmp_path / "xdg"
    application_directory = selected / "mymcp"
    application_directory.mkdir(mode=0o700, parents=True)
    application_directory.chmod(0o700)
    configuration_path = application_directory / "config.toml"
    configuration_path.write_text("invalid = [", encoding="utf-8")
    configuration_path.chmod(0o600)
    environment = dict(os.environ)
    environment["XDG_CONFIG_HOME"] = str(selected)

    completed = subprocess.run(
        [sys.executable, "-c", "import mymcp.app; import mymcp.cli"],
        cwd=Path(__file__).parents[1],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""

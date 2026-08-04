import os
import logging
import json
from pathlib import Path
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

import mymcp.app as app_module
import mymcp.host.authentication as host_authentication
from mymcp.app import create_app
from mymcp.authentication.router import compose_authenticator
from mymcp.host import bootstrap
from mymcp.host.configuration import HostConfiguration, parse_host_configuration_toml
from mymcp.host.authentication import HostAuthenticationCompositionError
from mymcp.mcp.tool_registry import ToolRegistration, ToolRegistry
from mymcp.settings import PROTOCOL_VERSION, SERVER_NAME, SERVER_VERSION


CONFIGURATION_LOGGER = "mymcp.host.configuration"
BOOTSTRAP_LOGGER = "mymcp.host.bootstrap"


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

    headers = {"MCP-Protocol-Version": PROTOCOL_VERSION}
    assert first.post("/mcp", headers=headers, json={"id": 1, "method": "tools/list"}).json()[
        "result"
    ]["tools"][0]["name"] == "first"
    assert second.post("/mcp", headers=headers, json={"id": 2, "method": "tools/list"}).json()[
        "result"
    ]["tools"][0]["name"] == "second"
    assert first.post(
        "/mcp",
        headers=headers, json={
            "id": 3,
            "method": "tools/call",
            "params": {"name": "first", "arguments": {"value": 1}},
        },
    ).json()["result"] == {"content": [], "runtime": "first"}
    assert second.post(
        "/mcp",
        headers=headers, json={
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


def test_create_app_accepts_explicit_authenticator() -> None:
    application = create_app(
        _runtime("first", []),
        compose_authenticator((), anonymous_enabled=False),
    )

    response = TestClient(application).post(
        "/mcp", content=b"invalid-json"
    )

    assert response.status_code == 401
    assert response.content == b""


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

    def build_app(selected_runtime, selected_authenticator):
        app_calls.append((selected_runtime, selected_authenticator))
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
    assert app_calls[0][0] is runtime
    assert app_calls[0][1].anonymous_enabled is True


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
    monkeypatch.setattr(
        app_module,
        "create_app",
        lambda selected, authenticator: application,
    )

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
    assert client.post(
        "/mcp", headers={"MCP-Protocol-Version": PROTOCOL_VERSION}, json={"id": 1, "method": "tools/list"}
    ).status_code == 200
    assert loader_calls == 1


def test_production_app_rejects_enabled_unavailable_adapter_before_publication() -> None:
    configuration = parse_host_configuration_toml(
        """
schema_version = 3
[authentication]
anonymous_enabled = true
[[authentication.adapters]]
id = "unavailable"
type = "synthetic"
enabled = true
route = {source = "authorization", scheme = "bearer"}
"""
    )

    with pytest.raises(
        HostAuthenticationCompositionError,
        match="^enabled authentication adapter type is unavailable$",
    ):
        app_module.create_production_app(configuration)


def test_unavailable_authentication_rejects_before_runtime_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = parse_host_configuration_toml(
        """
schema_version = 3
[authentication]
anonymous_enabled = true
[[authentication.adapters]]
id = "unavailable"
type = "synthetic"
enabled = true
route = {source = "authorization", scheme = "bearer"}
"""
    )
    monkeypatch.setattr(
        bootstrap,
        "build_production_runtime",
        lambda _configuration: pytest.fail(
            "runtime composition must follow Authentication composition"
        ),
    )

    with pytest.raises(HostAuthenticationCompositionError):
        app_module.create_production_app(configuration)


def test_production_app_ignores_disabled_adapter_and_applies_anonymous_setting() -> None:
    configuration = parse_host_configuration_toml(
        """
schema_version = 3
[authentication]
anonymous_enabled = false
[[authentication.adapters]]
id = "unavailable"
type = "synthetic"
enabled = false
route = {source = "authorization", scheme = "bearer"}
"""
    )

    response = TestClient(app_module.create_production_app(configuration)).post(
        "/mcp", content=b"not-json"
    )

    assert response.status_code == 401
    assert response.content == b""


def test_direct_and_reload_worker_factory_emits_one_event_and_requests_emit_none(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    selected = tmp_path / "xdg"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))
    monkeypatch.setenv("MNEMOSYNE_MEMORY_REMEMBER_ENABLED", "false")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED", "false")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_REVISE_ENABLED", "false")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_FORGET_ENABLED", "false")

    with caplog.at_level(logging.INFO):
        client = TestClient(app_module.create_production_app())
        client.get("/health")
        client.post("/mcp", json={"id": 1, "method": "tools/list"})
        client.post(
            "/mcp",
            json={
                "id": 2,
                "method": "tools/call",
                "params": {"name": "list_tools", "arguments": {}},
            },
        )

    assert [record.getMessage() for record in caplog.records if record.name in {
        CONFIGURATION_LOGGER,
        BOOTSTRAP_LOGGER,
    }] == [
        "host_configuration outcome=absent_defaults schema_version=1 "
        "address=127.0.0.1 port=8000 declarations=0 enabled=0",
        "runtime_composition outcome=loaded bundled=1 external=0 capabilities=3",
    ]


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

    response = client.post(
        "/mcp", headers={"MCP-Protocol-Version": PROTOCOL_VERSION}, json={"id": 1, "method": "tools/list"}
    )
    assert response.status_code == 200
    assert [tool["name"] for tool in response.json()["result"]["tools"]] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
    ]


def test_running_external_application_does_not_reread_changed_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "xdg"
    application_directory = selected / "mymcp"
    application_directory.mkdir(mode=0o700, parents=True)
    application_directory.chmod(0o700)
    manifest = tmp_path / "external-manifest.json"
    manifest.write_text(
        """{
  "manifest_version": 1,
  "id": "external",
  "title": "External",
  "description": "An external plugin.",
  "version": "1.0.0",
  "requires": {"host_api": {"min": 1, "max": 1}},
  "capabilities": [{"kind": "tool", "id": "external_tool", "version": "1.0.0", "read_only": true, "destructive": false, "idempotent": true, "open_world": false, "consent": "none"}],
  "configuration": {"schema_version": 1, "schema": {"type": "object", "properties": {}, "required": [], "additionalProperties": false}},
  "secret_references": [],
  "data_schema_version": 1,
  "authority": {"filesystem": [], "network": false}
}""",
        encoding="utf-8",
    )
    configuration_path = application_directory / "config.toml"
    configuration_path.write_text(
        "schema_version = 2\n[[plugins]]\n"
        'id = "external"\nenabled = true\n'
        f'manifest_path = "{manifest}"\n'
        'module = "tests.host.fixtures.operator_plugins.valid"\n',
        encoding="utf-8",
    )
    configuration_path.chmod(0o600)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(selected))
    monkeypatch.setenv("MNEMOSYNE_MEMORY_REMEMBER_ENABLED", "false")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED", "false")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_REVISE_ENABLED", "false")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_FORGET_ENABLED", "false")

    client = TestClient(app_module.create_production_app())
    manifest.write_bytes(b"{")

    assert client.post(
        "/mcp", headers={"MCP-Protocol-Version": PROTOCOL_VERSION}, json={"id": 1, "method": "tools/list"}
    ).status_code == 200
    with pytest.raises(bootstrap.ExternalPluginLoadError) as captured:
        app_module.create_production_app()
    assert captured.value.code == "external_manifest_invalid"


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


def _schema_v4_operator_configuration(verifier_path: str, *, enabled: bool = True) -> Any:
    return parse_host_configuration_toml(
        f"""
schema_version = 4
[authentication]
anonymous_enabled = true
[[authentication.adapters]]
id = "local-client"
type = "operator-bearer-v1"
enabled = {str(enabled).lower()}
route = {{source = "authorization", scheme = "bearer"}}
[authentication.operator_bearer]
verifier_path = "{verifier_path}"
"""
    )


def _verifier_digest_text() -> str:
    import base64
    import hashlib

    return (
        base64.urlsafe_b64encode(hashlib.sha256(bytes(range(32))).digest())
        .rstrip(b"=")
        .decode("ascii")
    )


def test_production_app_loads_verifier_source_before_runtime_construction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verifier = tmp_path / "verifier.json"
    verifier.write_text(
        json.dumps(
            {
                "format_version": 1,
                "credentials": [
                    {
                        "id": "a" * 32,
                        "subject": "stable-subject",
                        "digest": _verifier_digest_text(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    verifier.chmod(0o600)
    configuration = _schema_v4_operator_configuration(str(verifier))
    calls: list[str] = []
    original_loader = host_authentication.load_operator_bearer_verifier_source

    def recording_loader(path):
        calls.append("source")
        return original_loader(path)

    monkeypatch.setattr(
        host_authentication,
        "load_operator_bearer_verifier_source",
        recording_loader,
    )
    monkeypatch.setattr(
        bootstrap,
        "build_production_runtime",
        lambda _configuration: calls.append("runtime") or object(),
    )
    monkeypatch.setattr(
        app_module,
        "create_app",
        lambda _runtime, _authenticator: object(),
    )

    application = app_module.create_production_app(configuration)

    assert application is not None
    assert calls == ["source", "runtime"]


def test_production_app_verifier_failure_rejects_before_runtime_composition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing = tmp_path / "missing.json"
    configuration = _schema_v4_operator_configuration(str(missing))
    monkeypatch.setattr(
        bootstrap,
        "build_production_runtime",
        lambda _configuration: pytest.fail(
            "runtime composition must follow Authentication composition"
        ),
    )

    with pytest.raises(HostAuthenticationCompositionError) as captured:
        app_module.create_production_app(configuration)

    assert captured.value.code == "verifier_source"
    assert str(captured.value) == "operator bearer verifier source is unavailable"

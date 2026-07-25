from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

import mymcp.app as app_module
from mymcp.app import create_app
from mymcp.host import bootstrap
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


def test_production_app_bootstraps_once_and_delegates_to_create_app(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = _runtime("production", [])
    application = object()
    bootstrap_calls = 0
    app_calls: list[object] = []

    def build_runtime():
        nonlocal bootstrap_calls
        bootstrap_calls += 1
        return runtime

    def build_app(selected_runtime):
        app_calls.append(selected_runtime)
        return application

    monkeypatch.setattr(bootstrap, "build_production_runtime", build_runtime)
    monkeypatch.setattr(app_module, "create_app", build_app)

    assert app_module.create_production_app() is application
    assert bootstrap_calls == 1
    assert app_calls == [runtime]

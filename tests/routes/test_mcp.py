import json
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mnemosyne.app import app
from mnemosyne.settings import PROTOCOL_VERSION, SERVER_NAME, SERVER_VERSION


client = TestClient(app)


def test_mcp_logs_compact_success_events(caplog) -> None:
    caplog.set_level(logging.INFO, logger="mcp")

    response = client.post("/mcp", json={"id": "r1", "method": "initialize"})

    assert response.status_code == 200
    assert "request id=r1 method=initialize" in caplog.messages
    assert any(
        message.startswith("response id=r1 method=initialize outcome=ok duration_ms=")
        for message in caplog.messages
    )


def test_mcp_logs_compact_error_events_without_arguments(caplog) -> None:
    caplog.set_level(logging.INFO, logger="mcp")
    secret = "do-not-log-this"

    response = client.post(
        "/mcp",
        json={
            "id": "r1",
            "method": "tools/call",
            "params": {"name": "missing", "arguments": {"token": secret}},
        },
    )

    assert response.status_code == 200
    assert "request id=r1 method=tools/call" in caplog.messages
    assert any(
        message.startswith(
            "response id=r1 method=tools/call outcome=error code=-32602 duration_ms="
        )
        for message in caplog.messages
    )
    assert all(secret not in message for message in caplog.messages)


def test_mcp_cancellation_notification_returns_no_content() -> None:
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "notifications/cancelled",
            "params": {"requestId": "r1"},
        },
    )

    assert response.status_code == 202
    assert response.content == b""


def test_mcp_cancellation_notification_is_quiet_at_info_level(caplog) -> None:
    caplog.set_level(logging.INFO, logger="mcp")

    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "notifications/cancelled",
            "params": {"requestId": "r1"},
        },
    )

    assert response.status_code == 202
    assert caplog.messages == []


def test_mcp_initialized_notification_returns_no_content() -> None:
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
    )

    assert response.status_code == 202
    assert response.content == b""


def test_mcp_initialize_returns_server_capabilities() -> None:
    response = client.post("/mcp", json={"id": "r1", "method": "initialize"})

    assert response.status_code == 200
    assert response.json() == {
        "jsonrpc": "2.0",
        "id": "r1",
        "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        },
    }


def test_mcp_returns_method_not_found_for_unknown_methods() -> None:
    response = client.post("/mcp", json={"id": "r1", "method": "missing"})

    assert response.status_code == 200
    assert response.json() == {
        "jsonrpc": "2.0",
        "id": "r1",
        "error": {"code": -32601, "message": "Unknown method: missing"},
    }


def test_mcp_tools_list_exposes_the_registered_tools() -> None:
    response = client.post("/mcp", json={"id": "r1", "method": "tools/list"})

    assert response.status_code == 200
    tool_names = [tool["name"] for tool in response.json()["result"]["tools"]]
    assert tool_names[:3] == [
        "list_tools",
        "memory_recall",
        "memory_inspect",
    ]
    assert tool_names[3:] in (
        [],
        ["memory_archive", "memory_restore"],
        ["memory_remember"],
        ["memory_archive", "memory_restore", "memory_remember"],
    )


def test_mcp_tools_call_returns_memory_recall_no_matches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    response = client.post(
        "/mcp",
        json={
            "id": "r1",
            "method": "tools/call",
            "params": {
                "name": "memory_recall",
                "arguments": {
                    "query": "preferred response style",
                    "scope": "preference",
                    "tags": ["response-style"],
                },
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "jsonrpc": "2.0",
        "id": "r1",
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": '{"status":"no_matches","memories":[]}',
                }
            ]
        },
    }


def test_mcp_tools_call_returns_matching_memory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory_path = tmp_path / "preference" / "leisure" / "rainy.json"
    memory_path.parent.mkdir(parents=True)
    memory_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "rainy-day",
                "content": "The user prefers museums on rainy days.",
                "tags": ["leisure", "rainy-day"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    response = client.post(
        "/mcp",
        json={
            "id": "r1",
            "method": "tools/call",
            "params": {
                "name": "memory_recall",
                "arguments": {
                    "query": "rainy leisure activities",
                    "scope": "preference",
                    "tags": ["leisure", "rainy-day"],
                },
            },
        },
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert json.loads(result["content"][0]["text"]) == {
        "status": "ok",
        "memories": [
            {
                "reference": {
                    "schema_version": 1,
                    "scope": "preference",
                    "id": "rainy-day",
                },
                "id": "rainy-day",
                "scope": "preference",
                "title": None,
                "content": "The user prefers museums on rainy days.",
                "tags": ["leisure", "rainy-day"],
                "match": {
                    "terms": ["leisure", "rainy"],
                    "tags": ["leisure", "rainy-day"],
                },
            }
        ],
    }


def test_mcp_tools_call_returns_one_exact_inspected_memory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory_path = tmp_path / "preference" / "legacy" / "rainy.json"
    memory_path.parent.mkdir(parents=True)
    memory_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "rainy-day",
                "content": "The user prefers museums on rainy days.",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    response = client.post(
        "/mcp",
        json={
            "id": "r1",
            "method": "tools/call",
            "params": {
                "name": "memory_inspect",
                "arguments": {
                    "reference": {
                        "schema_version": 1,
                        "scope": "preference",
                        "id": "rainy-day",
                    }
                },
            },
        },
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert json.loads(result["content"][0]["text"]) == {
        "status": "ok",
        "memory": {
            "reference": {
                "schema_version": 1,
                "scope": "preference",
                "id": "rainy-day",
            },
            "schema_version": 1,
            "id": "rainy-day",
            "title": None,
            "content": "The user prefers museums on rainy days.",
            "tags": [],
        },
    }
    assert "path" not in result["content"][0]["text"]


def test_mcp_tools_call_reports_hello_as_an_unknown_tool() -> None:
    response = client.post(
        "/mcp",
        json={"id": "r1", "method": "tools/call", "params": {"name": "hello"}},
    )

    assert response.status_code == 200
    assert response.json() == {
        "jsonrpc": "2.0",
        "id": "r1",
        "error": {"code": -32602, "message": "Unknown tool: hello"},
    }


def test_mcp_rejects_non_object_request_envelopes() -> None:
    response = client.post("/mcp", json=[])

    assert response.status_code == 200
    assert response.json() == {
        "jsonrpc": "2.0",
        "id": None,
        "error": {"code": -32600, "message": "Invalid Request"},
    }


def test_mcp_rejects_non_object_params() -> None:
    response = client.post("/mcp", json={"id": "r1", "method": "ping", "params": []})

    assert response.status_code == 200
    assert response.json() == {
        "jsonrpc": "2.0",
        "id": "r1",
        "error": {"code": -32602, "message": "Invalid params"},
    }

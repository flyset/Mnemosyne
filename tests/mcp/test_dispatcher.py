from dataclasses import dataclass
from typing import Any

import pytest

from mymcp.mcp.dispatcher import MCPDispatcher
from mymcp.mcp.tool_registry import ToolRegistration, ToolRegistry
from mymcp.settings import PROTOCOL_VERSION, SERVER_NAME, SERVER_VERSION


@dataclass(frozen=True)
class SyntheticRuntime:
    registry: ToolRegistry


def _runtime(name: str, received: list[dict[str, Any]]) -> SyntheticRuntime:
    tool = {
        "name": name,
        "description": f"Synthetic {name} Tool.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "count": {"type": "integer"},
                "text": {"type": "string"},
            },
        },
    }

    def handler(arguments: dict[str, Any]) -> dict[str, Any]:
        received.append(arguments)
        return {"content": [], "arguments": arguments}

    return SyntheticRuntime(
        ToolRegistry((ToolRegistration(tool=tool, handler=handler),))
    )


def test_dispatchers_use_only_their_supplied_runtime() -> None:
    first_received: list[dict[str, Any]] = []
    second_received: list[dict[str, Any]] = []
    first = MCPDispatcher(_runtime("first", first_received))
    second = MCPDispatcher(_runtime("second", second_received))

    assert first.dispatch({"id": 1, "method": "tools/list"}) == {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"tools": [
            {
                "name": "first",
                "description": "Synthetic first Tool.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "text": {"type": "string"},
                    },
                },
            }
        ]},
    }
    assert second.dispatch({"id": 2, "method": "tools/list"})["result"][
        "tools"
    ][0]["name"] == "second"
    assert first.dispatch(
        {
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "first",
                "arguments": {"count": "2", "text": "null"},
            },
        }
    ) == {
        "jsonrpc": "2.0",
        "id": 3,
        "result": {
            "content": [],
            "arguments": {"count": 2, "text": "null"},
        },
    }
    assert second.dispatch(
        {"id": 4, "method": "tools/call", "params": {"name": "first"}}
    ) == {
        "jsonrpc": "2.0",
        "id": 4,
        "error": {"code": -32602, "message": "Unknown tool: first"},
    }
    assert first_received == [{"count": 2, "text": "null"}]
    assert second_received == []


def test_dispatcher_preserves_initialize_and_ping_contracts() -> None:
    dispatcher = MCPDispatcher(_runtime("first", []))

    assert dispatcher.dispatch({"id": "init", "method": "initialize"}) == {
        "jsonrpc": "2.0",
        "id": "init",
        "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        },
    }
    assert dispatcher.dispatch({"id": "ping", "method": "ping"}) == {
        "jsonrpc": "2.0",
        "id": "ping",
        "result": {},
    }


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        (
            [],
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "Invalid Request"},
            },
        ),
        (
            {"id": "bad", "method": "ping", "params": []},
            {
                "jsonrpc": "2.0",
                "id": "bad",
                "error": {"code": -32602, "message": "Invalid params"},
            },
        ),
        (
            {
                "id": "bad-arguments",
                "method": "tools/call",
                "params": {"name": "first", "arguments": []},
            },
            {
                "jsonrpc": "2.0",
                "id": "bad-arguments",
                "error": {"code": -32602, "message": "Invalid params"},
            },
        ),
        (
            {"id": "missing", "method": "missing"},
            {
                "jsonrpc": "2.0",
                "id": "missing",
                "error": {"code": -32601, "message": "Unknown method: missing"},
            },
        ),
    ],
)
def test_dispatcher_preserves_bounded_protocol_errors(
    message: Any,
    expected: dict[str, Any],
) -> None:
    assert MCPDispatcher(_runtime("first", [])).dispatch(message) == expected


@pytest.mark.parametrize(
    "message",
    [
        {"method": "notifications/initialized"},
        {"method": "notifications/cancelled", "params": {"requestId": "r1"}},
        {"method": "ping"},
        {
            "method": "tools/call",
            "params": {"name": "first", "arguments": {"count": "2"}},
        },
    ],
)
def test_dispatcher_returns_none_for_notifications(message: dict[str, Any]) -> None:
    received: list[dict[str, Any]] = []

    assert MCPDispatcher(_runtime("first", received)).dispatch(message) is None
    assert received == []


def test_explicit_null_id_remains_response_bearing() -> None:
    assert MCPDispatcher(_runtime("first", [])).dispatch(
        {"id": None, "method": "ping"}
    ) == {"jsonrpc": "2.0", "id": None, "result": {}}

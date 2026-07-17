from fastapi.testclient import TestClient

from mnemosyne.app import app
from mnemosyne.settings import PROTOCOL_VERSION, SERVER_NAME, SERVER_VERSION


client = TestClient(app)


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


def test_mcp_tools_list_excludes_the_retired_hello_tool() -> None:
    response = client.post("/mcp", json={"id": "r1", "method": "tools/list"})

    assert response.status_code == 200
    assert [tool["name"] for tool in response.json()["result"]["tools"]] == [
        "list_tools"
    ]


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

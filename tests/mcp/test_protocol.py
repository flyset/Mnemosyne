import json

from mnemosyne.mcp.protocol import mcp_error, mcp_result


def test_mcp_result_returns_a_json_rpc_success_response() -> None:
    response = mcp_result("r1", {"value": "ok"})

    assert json.loads(response.body) == {
        "jsonrpc": "2.0",
        "id": "r1",
        "result": {"value": "ok"},
    }


def test_mcp_error_returns_a_json_rpc_error_response() -> None:
    response = mcp_error("r1", -32601, "Unknown method: missing")

    assert json.loads(response.body) == {
        "jsonrpc": "2.0",
        "id": "r1",
        "error": {
            "code": -32601,
            "message": "Unknown method: missing",
        },
    }

import json

from mymcp.mcp.methods import handle_message


def test_handle_message_rejects_non_object_params_with_request_id() -> None:
    response = handle_message(
        {"id": "r1", "method": "ping", "params": []}
    )

    assert json.loads(response.body) == {
        "jsonrpc": "2.0",
        "id": "r1",
        "error": {
            "code": -32602,
            "message": "Invalid params",
        },
    }


def test_handle_message_rejects_non_object_request_envelopes() -> None:
    response = handle_message([])

    assert json.loads(response.body) == {
        "jsonrpc": "2.0",
        "id": None,
        "error": {
            "code": -32600,
            "message": "Invalid Request",
        },
    }


def test_handle_tools_call_rejects_non_object_arguments_with_request_id() -> None:
    response = handle_message(
        {
            "id": "r1",
            "method": "tools/call",
            "params": {"name": "memory_list", "arguments": []},
        }
    )

    assert json.loads(response.body) == {
        "jsonrpc": "2.0",
        "id": "r1",
        "error": {
            "code": -32602,
            "message": "Invalid params",
        },
    }

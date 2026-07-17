from mnemosyne.mcp.messages import MCPMessage, parse_message


def test_parse_message_preserves_object_fields() -> None:
    assert parse_message(
        {"id": "r1", "method": "ping", "params": {"key": "value"}}
    ) == MCPMessage(
        request_id="r1",
        method="ping",
        params={"key": "value"},
        params_valid=True,
    )


def test_parse_message_defaults_missing_params_to_an_empty_object() -> None:
    assert parse_message({"id": 1, "method": "initialize"}) == MCPMessage(
        request_id=1,
        method="initialize",
        params={},
        params_valid=True,
    )

from mnemosyne.mcp.tools.registry import call_tool


def test_call_tool_returns_none_for_an_unknown_tool() -> None:
    assert call_tool("missing", {}) is None


def test_call_tool_dispatches_memory_recall() -> None:
    assert call_tool(
        "memory_recall",
        {"query": "current project", "scope": "project"},
    ) == {
        "content": [
            {
                "type": "text",
                "text": '{"status":"retrieval_unavailable"}',
            }
        ]
    }

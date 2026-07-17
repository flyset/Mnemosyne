from mnemosyne.mcp.tools.list_tools import handle


def test_list_tools_formats_the_supplied_tool_names() -> None:
    assert handle({}, [{"name": "one"}, {"name": "two"}]) == {
        "content": [{"type": "text", "text": "Available tools: one, two"}]
    }

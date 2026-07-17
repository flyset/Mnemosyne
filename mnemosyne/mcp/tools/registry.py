from typing import Any

from mnemosyne.mcp.tools import hello, list_tools

TOOLS = [hello.TOOL, list_tools.TOOL]

TOOL_HANDLERS = {
    hello.TOOL["name"]: hello.handle,
    list_tools.TOOL["name"]: lambda arguments: list_tools.handle(arguments, TOOLS),
}


def call_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any] | None:
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return None

    return handler(arguments)

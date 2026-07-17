from typing import Any

TOOL = {
    "name": "list_tools",
    "description": "Returns the list of tools exposed by this MCP server.",
    "inputSchema": {
        "type": "object",
        "properties": {},
    },
}


def handle(arguments: dict[str, Any], tools: list[dict[str, Any]]) -> dict[str, Any]:
    tool_names = [tool["name"] for tool in tools]
    return {
        "content": [
            {
                "type": "text",
                "text": "Available tools: " + ", ".join(tool_names),
            }
        ]
    }

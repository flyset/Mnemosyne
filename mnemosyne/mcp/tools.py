from typing import Any

TOOLS = [
    {
        "name": "hello",
        "description": "Returns a greeting for the given name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name to greet.",
                }
            },
            "required": ["name"],
        },
    },
    {
        "name": "list_tools",
        "description": "Returns the list of tools exposed by this MCP server.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    }
]


def call_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any] | None:
    if tool_name == "hello":
        name = arguments.get("name", "world")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Hello, {name}!",
                }
            ]
        }

    if tool_name == "list_tools":
        tool_names = [tool["name"] for tool in TOOLS]
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Available tools: " + ", ".join(tool_names),
                }
            ]
        }

    return None

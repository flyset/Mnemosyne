from typing import Any

TOOL = {
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
}


def handle(arguments: dict[str, Any]) -> dict[str, Any]:
    name = arguments.get("name", "world")
    return {
        "content": [
            {
                "type": "text",
                "text": f"Hello, {name}!",
            }
        ]
    }

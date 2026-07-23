from typing import Any

import pytest

from mymcp.mcp.composition import compose_tool_registry
from mymcp.mcp.tool_registry import ToolRegistration
from mymcp.settings import SERVER_NAME, SERVER_VERSION


FIRST_TOOL = {
    "name": "first",
    "description": "First synthetic integration Tool.",
    "inputSchema": {"type": "object", "properties": {}},
}
SECOND_TOOL = {
    "name": "second",
    "description": "Second synthetic integration Tool.",
    "inputSchema": {"type": "object", "properties": {}},
}


def _result(arguments: dict[str, Any]) -> dict[str, Any]:
    return {"content": [], "arguments": arguments}


def test_host_composition_aggregates_static_integrations_in_order() -> None:
    composition_order: list[str] = []

    def first_integration() -> tuple[ToolRegistration, ...]:
        composition_order.append("first")
        return (ToolRegistration(tool=FIRST_TOOL, handler=_result),)

    def second_integration() -> tuple[ToolRegistration, ...]:
        composition_order.append("second")
        return (ToolRegistration(tool=SECOND_TOOL, handler=_result),)

    registry = compose_tool_registry((first_integration, second_integration))

    assert composition_order == ["first", "second"]
    assert [tool["name"] for tool in registry.tools] == [
        "list_tools",
        "first",
        "second",
    ]
    assert registry.call_tool("second", {"value": 2}) == {
        "content": [],
        "arguments": {"value": 2},
    }
    assert registry.call_tool("list_tools", {}) == {
        "content": [
            {
                "type": "text",
                "text": (
                    f"Server: {SERVER_NAME} {SERVER_VERSION}. Available tools: "
                    "list_tools, first, second"
                ),
            }
        ]
    }


@pytest.mark.parametrize("duplicate_name", ["shared", "list_tools"])
def test_host_composition_rejects_duplicate_names_across_integrations(
    duplicate_name: str,
) -> None:
    first_name = "shared" if duplicate_name == "shared" else "first"
    first_tool = {
        "name": first_name,
        "description": "First synthetic integration Tool.",
        "inputSchema": {"type": "object", "properties": {}},
    }
    duplicate_tool = {
        "name": duplicate_name,
        "description": "Colliding synthetic integration Tool.",
        "inputSchema": {"type": "object", "properties": {}},
    }

    def first_integration() -> tuple[ToolRegistration, ...]:
        return (ToolRegistration(tool=first_tool, handler=_result),)

    def second_integration() -> tuple[ToolRegistration, ...]:
        return (ToolRegistration(tool=duplicate_tool, handler=_result),)

    with pytest.raises(
        ValueError,
        match=f"^duplicate tool registration: {duplicate_name}$",
    ):
        compose_tool_registry((first_integration, second_integration))

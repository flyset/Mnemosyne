import ast
from pathlib import Path

import pytest

from mymcp.mcp.tool_registry import ToolRegistration, ToolRegistry


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_MODULE = PROJECT_ROOT / "mymcp" / "mcp" / "tool_registry.py"
FIRST_TOOL = {
    "name": "first",
    "description": "First synthetic Tool.",
    "inputSchema": {
        "type": "object",
        "properties": {"count": {"type": "integer"}},
    },
}
SECOND_TOOL = {
    "name": "second",
    "description": "Second synthetic Tool.",
    "inputSchema": {"type": "object", "properties": {}},
}


def _empty_result(arguments: dict[str, object]) -> dict[str, object]:
    return {"content": [], "arguments": arguments}


def test_generic_registry_module_imports_no_mnemosyne_tools_or_settings() -> None:
    tree = ast.parse(REGISTRY_MODULE.read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert all(
        not imported.startswith(("mymcp.mcp.tools", "mymcp.memory"))
        for imported in imports
    )
    assert "mymcp.settings" not in imports


def test_registry_requires_complete_explicit_registrations() -> None:
    with pytest.raises(TypeError):
        ToolRegistration(tool=FIRST_TOOL)  # type: ignore[call-arg]

    with pytest.raises(ValueError, match="^invalid tool registration$"):
        ToolRegistry(
            (ToolRegistration(tool=FIRST_TOOL, handler=None),)  # type: ignore[arg-type]
        )


def test_registry_preserves_order_and_immutable_discovery() -> None:
    registrations = [
        ToolRegistration(tool=FIRST_TOOL, handler=_empty_result),
        ToolRegistration(tool=SECOND_TOOL, handler=_empty_result),
    ]

    registry = ToolRegistry(registrations)
    registrations.reverse()
    discovered = registry.tools
    discovered[0]["name"] = "changed"
    discovered[0]["inputSchema"]["properties"].clear()

    assert [tool["name"] for tool in registry.tools] == ["first", "second"]
    assert registry.tools[0]["inputSchema"]["properties"] == {
        "count": {"type": "integer"}
    }
    with pytest.raises(TypeError):
        registry.handlers["third"] = _empty_result  # type: ignore[index]


def test_registry_rejects_duplicate_tool_names() -> None:
    with pytest.raises(ValueError, match="^duplicate tool registration: first$"):
        ToolRegistry(
            (
                ToolRegistration(tool=FIRST_TOOL, handler=_empty_result),
                ToolRegistration(tool=FIRST_TOOL, handler=_empty_result),
            )
        )


def test_registry_returns_none_for_unknown_tools() -> None:
    registry = ToolRegistry(
        (ToolRegistration(tool=FIRST_TOOL, handler=_empty_result),)
    )

    assert registry.call_tool("missing", {}) is None


def test_registry_normalizes_arguments_from_the_registered_schema() -> None:
    received: list[dict[str, object]] = []

    def capture(arguments: dict[str, object]) -> dict[str, object]:
        received.append(arguments)
        return {"content": []}

    registry = ToolRegistry((ToolRegistration(tool=FIRST_TOOL, handler=capture),))
    arguments = {"count": "2"}

    assert registry.call_tool("first", arguments) == {"content": []}
    assert received == [{"count": 2}]
    assert arguments == {"count": "2"}

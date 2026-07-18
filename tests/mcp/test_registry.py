from pathlib import Path

import pytest

from mnemosyne.mcp.tools.registry import (
    build_startup_tool_registry,
    build_tool_registry,
    call_tool,
)


REMEMBER_TOOL = {
    "name": "memory_remember",
    "description": "Synthetic registration for registry tests.",
    "inputSchema": {"type": "object", "properties": {}},
}
INSPECT_TOOL = {
    "name": "memory_inspect",
    "description": "Synthetic inspection registration for registry tests.",
    "inputSchema": {"type": "object", "properties": {}},
}


def _remember(arguments: dict[str, object]) -> dict[str, object]:
    return {
        "content": [
            {
                "type": "text",
                "text": f"remembered:{arguments.get('value')}",
            }
        ]
    }


def _inspect(arguments: dict[str, object]) -> dict[str, object]:
    return {
        "content": [
            {
                "type": "text",
                "text": f"inspected:{arguments.get('value')}",
            }
        ]
    }


def test_call_tool_returns_none_for_an_unknown_tool() -> None:
    assert call_tool("missing", {}) is None


def test_call_tool_dispatches_memory_recall(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    assert call_tool(
        "memory_recall",
        {"query": "current project", "scope": "project"},
    ) == {
        "content": [
            {
                "type": "text",
                "text": '{"status":"no_matches","memories":[]}',
            }
        ]
    }


def test_call_tool_dispatches_memory_inspect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "missing" / "memory"
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(root))

    result = call_tool(
        "memory_inspect",
        {
            "reference": {
                "schema_version": 1,
                "scope": "project",
                "id": "missing",
            }
        },
    )

    assert result is not None
    assert result["isError"] is True
    assert result["content"][0]["text"] == (
        '{"status":"not_found","code":"not_found",'
        '"message":"memory was not found"}'
    )
    assert not (tmp_path / "missing").exists()


def test_registry_omits_disabled_remember_from_discovery_and_dispatch() -> None:
    registry = build_tool_registry(
        False,
        memory_remember_tool=REMEMBER_TOOL,
        memory_remember_handler=_remember,
    )

    assert [tool["name"] for tool in registry.tools] == [
        "list_tools",
        "memory_recall",
    ]
    assert registry.call_tool("memory_remember", {"value": "safe"}) is None
    assert registry.call_tool("list_tools", {}) == {
        "content": [
            {
                "type": "text",
                "text": "Available tools: list_tools, memory_recall",
            }
        ]
    }


def test_registry_connects_inspect_discovery_and_dispatch_together() -> None:
    registry = build_tool_registry(
        False,
        memory_inspect_tool=INSPECT_TOOL,
        memory_inspect_handler=_inspect,
    )

    assert [tool["name"] for tool in registry.tools] == [
        "list_tools",
        "memory_recall",
        "memory_inspect",
    ]
    assert registry.call_tool("memory_inspect", {"value": "safe"}) == {
        "content": [{"type": "text", "text": "inspected:safe"}]
    }
    assert registry.call_tool("list_tools", {}) == {
        "content": [
            {
                "type": "text",
                "text": "Available tools: list_tools, memory_recall, memory_inspect",
            }
        ]
    }


@pytest.mark.parametrize(
    "registration",
    [
        {"memory_inspect_tool": INSPECT_TOOL},
        {"memory_inspect_handler": _inspect},
    ],
)
def test_registry_fails_closed_for_incomplete_inspect_registration(
    registration: dict[str, object],
) -> None:
    with pytest.raises(
        ValueError,
        match="^memory inspect registration is unavailable$",
    ):
        build_tool_registry(False, **registration)


def test_registry_enables_remember_discovery_and_dispatch_together() -> None:
    registry = build_tool_registry(
        True,
        memory_remember_tool=REMEMBER_TOOL,
        memory_remember_handler=_remember,
    )

    assert [tool["name"] for tool in registry.tools] == [
        "list_tools",
        "memory_recall",
        "memory_remember",
    ]
    assert registry.call_tool("memory_remember", {"value": "safe"}) == {
        "content": [{"type": "text", "text": "remembered:safe"}]
    }
    assert registry.call_tool("list_tools", {}) == {
        "content": [
            {
                "type": "text",
                "text": (
                    "Available tools: list_tools, memory_recall, memory_remember"
                ),
            }
        ]
    }


def test_registry_fails_closed_when_enabled_registration_is_unavailable() -> None:
    with pytest.raises(
        ValueError,
        match="^memory remember registration is unavailable$",
    ):
        build_tool_registry(True)


def test_startup_registry_connects_inspect_and_real_remember_only_when_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    arguments = {
        "scope": "project",
        "namespace": {"kind": "project", "id": "mnemosyne", "label": None},
        "collection": None,
        "kind": "decision",
        "language": "en",
        "title": None,
        "content": "The startup registry enables one approved memory Tool.",
        "tags": [],
        "origin": "user_approved_proposal",
    }

    disabled = build_startup_tool_registry(False)
    enabled = build_startup_tool_registry(True)
    inspect_arguments = {
        "reference": {
            "schema_version": 1,
            "scope": "project",
            "id": "missing",
        }
    }

    assert [tool["name"] for tool in disabled.tools] == [
        "list_tools",
        "memory_recall",
        "memory_inspect",
    ]
    disabled_inspect = disabled.call_tool("memory_inspect", inspect_arguments)
    assert disabled_inspect is not None
    assert '"code":"not_found"' in disabled_inspect["content"][0]["text"]
    assert disabled.call_tool("memory_remember", arguments) is None
    assert [tool["name"] for tool in enabled.tools] == [
        "list_tools",
        "memory_recall",
        "memory_inspect",
        "memory_remember",
    ]
    enabled_inspect = enabled.call_tool("memory_inspect", inspect_arguments)
    assert enabled_inspect is not None
    assert '"code":"not_found"' in enabled_inspect["content"][0]["text"]
    result = enabled.call_tool("memory_remember", arguments)
    assert result is not None
    assert '"status":"remembered"' in result["content"][0]["text"]
    assert len(list(tmp_path.rglob("*.json"))) == 1

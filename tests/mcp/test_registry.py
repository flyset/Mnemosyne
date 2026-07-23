from pathlib import Path

import pytest

from mymcp.mcp.composition import compose_tool_registry
from mymcp.mcp.integrations.mnemosyne import build_mnemosyne_registrations
from mymcp.mcp.startup import REGISTRY as STARTUP_REGISTRY
from mymcp.mcp.tool_registry import ToolRegistration, ToolRegistry
from mymcp.mcp.tools.memory_revise import TOOL as MEMORY_REVISE_TOOL


def _registry(
    memory_remember_enabled: bool,
    memory_archive_restore_enabled: bool = False,
    memory_forget_enabled: bool = False,
    *,
    memory_revise_enabled: bool = False,
) -> ToolRegistry:
    def mnemosyne_test_integration() -> tuple[ToolRegistration, ...]:
        return build_mnemosyne_registrations(
            memory_remember_enabled,
            memory_archive_restore_enabled=memory_archive_restore_enabled,
            memory_forget_enabled=memory_forget_enabled,
            memory_revise_enabled=memory_revise_enabled,
        )

    return compose_tool_registry((mnemosyne_test_integration,))


def test_call_tool_returns_none_for_an_unknown_tool() -> None:
    assert STARTUP_REGISTRY.call_tool("missing", {}) is None


def test_call_tool_dispatches_memory_recall(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    assert STARTUP_REGISTRY.call_tool(
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

    result = STARTUP_REGISTRY.call_tool(
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


def test_call_tool_dispatches_memory_list_without_initializing_the_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "missing" / "memory"
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(root))

    result = STARTUP_REGISTRY.call_tool(
        "memory_list",
        {"scope": "project", "page_size": "2"},
    )

    assert result is not None
    assert result.get("isError") is not True
    assert '"status":"ok"' in result["content"][0]["text"]
    assert '"total_count":0' in result["content"][0]["text"]
    assert not (tmp_path / "missing").exists()


def test_call_tool_normalizes_stringified_inspect_reference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "missing" / "memory"
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(root))

    result = STARTUP_REGISTRY.call_tool(
        "memory_inspect",
        {
            "reference": (
                '{"schema_version": 1, "scope": "project", '
                '"id": "missing"}'
            )
        },
    )

    assert result is not None
    assert '"code":"not_found"' in result["content"][0]["text"]
    assert not (tmp_path / "missing").exists()


def test_startup_registry_exposes_forget_only_when_independently_enabled() -> None:
    disabled = _registry(False, False, False)
    enabled = _registry(False, False, True)

    assert "memory_forget" not in [tool["name"] for tool in disabled.tools]
    assert disabled.call_tool("memory_forget", {}) is None
    assert [tool["name"] for tool in enabled.tools] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
        "memory_forget",
    ]
    result = enabled.call_tool("memory_forget", {})
    assert result is not None
    assert '"code":"invalid_reference"' in result["content"][0]["text"]


def test_startup_registry_exposes_revise_only_when_independently_enabled() -> None:
    disabled = _registry(False)
    enabled = _registry(False, memory_revise_enabled=True)

    assert disabled.call_tool("memory_revise", {}) is None
    assert [tool["name"] for tool in enabled.tools] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
        "memory_revise",
    ]
    result = enabled.call_tool("memory_revise", {})
    assert result is not None
    assert '"code":"invalid_reference"' in result["content"][0]["text"]


def test_startup_registry_orders_forget_after_other_mutations() -> None:
    registry = _registry(
        True,
        True,
        True,
        memory_revise_enabled=True,
    )

    assert [tool["name"] for tool in registry.tools] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
        "memory_archive",
        "memory_restore",
        "memory_remember",
        "memory_revise",
        "memory_forget",
    ]


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

    disabled = _registry(False)
    enabled = _registry(True)
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
        "memory_list",
        "memory_inspect",
    ]
    disabled_inspect = disabled.call_tool("memory_inspect", inspect_arguments)
    assert disabled_inspect is not None
    assert '"code":"not_found"' in disabled_inspect["content"][0]["text"]
    assert disabled.call_tool("memory_remember", arguments) is None
    assert [tool["name"] for tool in enabled.tools] == [
        "list_tools",
        "memory_recall",
        "memory_list",
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


def test_startup_registry_accepts_captured_stringified_remember_arguments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    registry = _registry(True)
    arguments = {
        "scope": "project",
        "namespace": (
            '{"kind": "project", "id": "mnemosyne", '
            '"label": "Mnemosyne"}'
        ),
        "collection": '{"id": "checkpoints", "label": "Checkpoints"}',
        "kind": "state",
        "language": "en",
        "title": "Stringified argument compatibility",
        "content": "Synthetic registry compatibility test.",
        "tags": '["test", "validation"]',
        "origin": "user_approved_proposal",
    }

    result = registry.call_tool("memory_remember", arguments)

    assert result is not None
    assert '"status":"remembered"' in result["content"][0]["text"]
    assert len(list(tmp_path.rglob("*.json"))) == 1


def test_startup_registry_exposes_archive_and_restore_only_as_an_enabled_pair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    disabled = _registry(False, False)
    enabled = _registry(False, True)

    assert [tool["name"] for tool in disabled.tools] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
    ]
    assert disabled.call_tool("memory_archive", {}) is None
    assert disabled.call_tool("memory_restore", {}) is None
    assert [tool["name"] for tool in enabled.tools] == [
        "list_tools",
        "memory_recall",
        "memory_list",
        "memory_inspect",
        "memory_archive",
        "memory_restore",
    ]
    archive = enabled.call_tool("memory_archive", {})
    restore = enabled.call_tool("memory_restore", {})
    assert archive is not None
    assert restore is not None
    assert '"code":"invalid_reference"' in archive["content"][0]["text"]
    assert '"code":"invalid_reference"' in restore["content"][0]["text"]

    valid_arguments = {
        "reference": {
            "schema_version": 2,
            "scope": "project",
            "namespace_id": "mnemosyne",
            "collection_id": None,
            "id": "mem_0123456789abcdef0123456789abcdef",
        },
        "expected_revision": 1,
    }
    valid_archive = enabled.call_tool("memory_archive", valid_arguments)
    valid_restore = enabled.call_tool("memory_restore", valid_arguments)
    assert valid_archive is not None
    assert valid_restore is not None
    assert '"code":"not_found"' in valid_archive["content"][0]["text"]
    assert '"code":"not_found"' in valid_restore["content"][0]["text"]


def test_startup_registry_normalizes_stringified_lifecycle_arguments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    registry = _registry(False, True)
    reference = (
        '{"schema_version": 2, "scope": "project", '
        '"namespace_id": "mnemosyne", "collection_id": null, '
        '"id": "mem_0123456789abcdef0123456789abcdef"}'
    )

    result = registry.call_tool(
        "memory_archive",
        {"reference": reference, "expected_revision": "1"},
    )

    assert result is not None
    assert '"code":"not_found"' in result["content"][0]["text"]


def test_startup_registry_normalizes_stringified_revise_arguments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "missing" / "memory"
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(root))
    registry = _registry(False, memory_revise_enabled=True)
    arguments = {
        "reference": (
            '{"schema_version": 2, "scope": "project", '
            '"namespace_id": "mnemosyne", "collection_id": null, '
            '"id": "mem_0123456789abcdef0123456789abcdef"}'
        ),
        "expected_revision": "3",
        "namespace_label": None,
        "collection_label": None,
        "title": "Revision compatibility",
        "content": "Synthetic revision compatibility test.",
        "tags": '["test", "validation"]',
    }
    original = dict(arguments)

    result = registry.call_tool("memory_revise", arguments)

    assert result is not None
    assert '"code":"not_found"' in result["content"][0]["text"]
    assert arguments == original
    assert not (tmp_path / "missing").exists()


def test_registry_delivers_claude_style_revise_arguments_with_typed_structure() -> None:
    observed: list[dict[str, object]] = []
    registry = ToolRegistry(
        (
            ToolRegistration(
                tool=MEMORY_REVISE_TOOL,
                handler=lambda arguments: (
                    observed.append(arguments)
                    or {"content": [{"type": "text", "text": "captured"}]}
                ),
            ),
        )
    )
    arguments = {
        "reference": (
            '{"schema_version": 2, "scope": "relationship", '
            '"namespace_id": "stakeholders", "collection_id": null, '
            '"id": "mem_0123456789abcdef0123456789abcdef"}'
        ),
        "expected_revision": "1",
        "namespace_label": "Stakeholders",
        "title": "Stakeholder summary",
        "content": "Synthetic transport compatibility content.",
        "tags": '["work", "stakeholders"]',
    }

    result = registry.call_tool("memory_revise", arguments)

    assert result == {"content": [{"type": "text", "text": "captured"}]}
    assert observed == [
        {
            "reference": {
                "schema_version": 2,
                "scope": "relationship",
                "namespace_id": "stakeholders",
                "collection_id": None,
                "id": "mem_0123456789abcdef0123456789abcdef",
            },
            "expected_revision": 1,
            "namespace_label": "Stakeholders",
            "title": "Stakeholder summary",
            "content": "Synthetic transport compatibility content.",
            "tags": ["work", "stakeholders"],
        }
    ]

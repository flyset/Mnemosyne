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
ARCHIVE_TOOL = {
    "name": "memory_archive",
    "description": "Synthetic archive registration for registry tests.",
    "inputSchema": {"type": "object", "properties": {}},
}
RESTORE_TOOL = {
    "name": "memory_restore",
    "description": "Synthetic restore registration for registry tests.",
    "inputSchema": {"type": "object", "properties": {}},
}
REVISE_TOOL = {
    "name": "memory_revise",
    "description": "Synthetic revision registration for registry tests.",
    "inputSchema": {"type": "object", "properties": {}},
}
FORGET_TOOL = {
    "name": "memory_forget",
    "description": "Synthetic forget registration for registry tests.",
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


def _archive(arguments: dict[str, object]) -> dict[str, object]:
    return {
        "content": [{"type": "text", "text": f"archived:{arguments.get('value')}"}]
    }


def _restore(arguments: dict[str, object]) -> dict[str, object]:
    return {
        "content": [{"type": "text", "text": f"restored:{arguments.get('value')}"}]
    }


def _revise(arguments: dict[str, object]) -> dict[str, object]:
    return {
        "content": [{"type": "text", "text": f"revised:{arguments.get('value')}"}]
    }


def _forget(arguments: dict[str, object]) -> dict[str, object]:
    return {
        "content": [{"type": "text", "text": f"forgotten:{arguments.get('value')}"}]
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


def test_call_tool_normalizes_stringified_inspect_reference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "missing" / "memory"
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(root))

    result = call_tool(
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


def test_registry_normalizes_schema_declared_arguments_before_dispatch() -> None:
    received: list[dict[str, object]] = []
    tool = {
        **REMEMBER_TOOL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "object", "properties": {}},
                "tags": {"type": "array", "items": {"type": "string"}},
                "content": {"type": "string"},
            },
        },
    }

    def capture(arguments: dict[str, object]) -> dict[str, object]:
        received.append(arguments)
        return {"content": []}

    registry = build_tool_registry(
        True,
        memory_remember_tool=tool,
        memory_remember_handler=capture,
    )
    arguments = {
        "namespace": '{"kind": "project"}',
        "tags": '["test"]',
        "content": '["remains", "text"]',
    }

    assert registry.call_tool("memory_remember", arguments) == {"content": []}
    assert received == [
        {
            "namespace": {"kind": "project"},
            "tags": ["test"],
            "content": '["remains", "text"]',
        }
    ]
    assert arguments["namespace"] == '{"kind": "project"}'


def test_registry_fails_closed_when_enabled_registration_is_unavailable() -> None:
    with pytest.raises(
        ValueError,
        match="^memory remember registration is unavailable$",
    ):
        build_tool_registry(True)


def test_registry_omits_disabled_archive_restore_pair() -> None:
    registry = build_tool_registry(
        False,
        memory_archive_restore_enabled=False,
        memory_archive_tool=ARCHIVE_TOOL,
        memory_archive_handler=_archive,
        memory_restore_tool=RESTORE_TOOL,
        memory_restore_handler=_restore,
    )

    assert [tool["name"] for tool in registry.tools] == [
        "list_tools",
        "memory_recall",
    ]
    assert registry.call_tool("memory_archive", {"value": "safe"}) is None
    assert registry.call_tool("memory_restore", {"value": "safe"}) is None


def test_registry_enables_archive_restore_discovery_and_dispatch_as_one_pair() -> None:
    registry = build_tool_registry(
        False,
        memory_archive_restore_enabled=True,
        memory_archive_tool=ARCHIVE_TOOL,
        memory_archive_handler=_archive,
        memory_restore_tool=RESTORE_TOOL,
        memory_restore_handler=_restore,
    )

    assert [tool["name"] for tool in registry.tools] == [
        "list_tools",
        "memory_recall",
        "memory_archive",
        "memory_restore",
    ]
    assert registry.call_tool("memory_archive", {"value": "safe"}) == {
        "content": [{"type": "text", "text": "archived:safe"}]
    }
    assert registry.call_tool("memory_restore", {"value": "safe"}) == {
        "content": [{"type": "text", "text": "restored:safe"}]
    }
    assert registry.call_tool("list_tools", {}) == {
        "content": [
            {
                "type": "text",
                "text": (
                    "Available tools: list_tools, memory_recall, "
                    "memory_archive, memory_restore"
                ),
            }
        ]
    }


@pytest.mark.parametrize(
    "registration",
    [
        {},
        {"memory_archive_tool": ARCHIVE_TOOL},
        {"memory_archive_handler": _archive},
        {
            "memory_archive_tool": ARCHIVE_TOOL,
            "memory_archive_handler": _archive,
        },
        {
            "memory_restore_tool": RESTORE_TOOL,
            "memory_restore_handler": _restore,
        },
    ],
)
def test_registry_fails_closed_for_incomplete_enabled_archive_restore_pair(
    registration: dict[str, object],
) -> None:
    with pytest.raises(
        ValueError,
        match="^memory archive/restore registration is unavailable$",
    ):
        build_tool_registry(
            False,
            memory_archive_restore_enabled=True,
            **registration,
        )


def test_registry_omits_disabled_revise_from_discovery_and_dispatch() -> None:
    registry = build_tool_registry(
        False,
        memory_revise_enabled=False,
        memory_revise_tool=REVISE_TOOL,
        memory_revise_handler=_revise,
    )

    assert [tool["name"] for tool in registry.tools] == [
        "list_tools",
        "memory_recall",
    ]
    assert registry.call_tool("memory_revise", {"value": "safe"}) is None


def test_registry_injects_revise_discovery_and_dispatch_together() -> None:
    registry = build_tool_registry(
        False,
        memory_revise_enabled=True,
        memory_revise_tool=REVISE_TOOL,
        memory_revise_handler=_revise,
    )

    assert [tool["name"] for tool in registry.tools] == [
        "list_tools",
        "memory_recall",
        "memory_revise",
    ]
    assert registry.call_tool("memory_revise", {"value": "safe"}) == {
        "content": [{"type": "text", "text": "revised:safe"}]
    }


@pytest.mark.parametrize(
    "registration",
    [
        {},
        {"memory_revise_tool": REVISE_TOOL},
        {"memory_revise_handler": _revise},
    ],
)
def test_registry_fails_closed_for_incomplete_enabled_revise_registration(
    registration: dict[str, object],
) -> None:
    with pytest.raises(
        ValueError,
        match="^memory revise registration is unavailable$",
    ):
        build_tool_registry(
            False,
            memory_revise_enabled=True,
            **registration,
        )


def test_registry_orders_revise_after_remember_and_before_forget() -> None:
    registry = build_tool_registry(
        True,
        memory_revise_enabled=True,
        memory_forget_enabled=True,
        memory_remember_tool=REMEMBER_TOOL,
        memory_remember_handler=_remember,
        memory_revise_tool=REVISE_TOOL,
        memory_revise_handler=_revise,
        memory_forget_tool=FORGET_TOOL,
        memory_forget_handler=_forget,
    )

    assert [tool["name"] for tool in registry.tools] == [
        "list_tools",
        "memory_recall",
        "memory_remember",
        "memory_revise",
        "memory_forget",
    ]


def test_registry_omits_disabled_forget_from_discovery_and_dispatch() -> None:
    registry = build_tool_registry(
        False,
        memory_forget_enabled=False,
        memory_forget_tool=FORGET_TOOL,
        memory_forget_handler=_forget,
    )

    assert [tool["name"] for tool in registry.tools] == [
        "list_tools",
        "memory_recall",
    ]
    assert registry.call_tool("memory_forget", {"value": "safe"}) is None


def test_registry_injects_forget_discovery_and_dispatch_together() -> None:
    registry = build_tool_registry(
        False,
        memory_forget_enabled=True,
        memory_forget_tool=FORGET_TOOL,
        memory_forget_handler=_forget,
    )

    assert [tool["name"] for tool in registry.tools] == [
        "list_tools",
        "memory_recall",
        "memory_forget",
    ]
    assert registry.call_tool("memory_forget", {"value": "safe"}) == {
        "content": [{"type": "text", "text": "forgotten:safe"}]
    }


@pytest.mark.parametrize(
    "registration",
    [
        {},
        {"memory_forget_tool": FORGET_TOOL},
        {"memory_forget_handler": _forget},
    ],
)
def test_registry_fails_closed_for_incomplete_enabled_forget_registration(
    registration: dict[str, object],
) -> None:
    with pytest.raises(
        ValueError,
        match="^memory forget registration is unavailable$",
    ):
        build_tool_registry(
            False,
            memory_forget_enabled=True,
            **registration,
        )


def test_startup_registry_exposes_forget_only_when_independently_enabled() -> None:
    disabled = build_startup_tool_registry(False, False, False)
    enabled = build_startup_tool_registry(False, False, True)

    assert "memory_forget" not in [tool["name"] for tool in disabled.tools]
    assert disabled.call_tool("memory_forget", {}) is None
    assert [tool["name"] for tool in enabled.tools] == [
        "list_tools",
        "memory_recall",
        "memory_inspect",
        "memory_forget",
    ]
    result = enabled.call_tool("memory_forget", {})
    assert result is not None
    assert '"code":"invalid_reference"' in result["content"][0]["text"]


def test_startup_registry_exposes_revise_only_when_independently_enabled() -> None:
    disabled = build_startup_tool_registry(False)
    enabled = build_startup_tool_registry(False, memory_revise_enabled=True)

    assert disabled.call_tool("memory_revise", {}) is None
    assert [tool["name"] for tool in enabled.tools] == [
        "list_tools",
        "memory_recall",
        "memory_inspect",
        "memory_revise",
    ]
    result = enabled.call_tool("memory_revise", {})
    assert result is not None
    assert '"code":"invalid_reference"' in result["content"][0]["text"]


def test_startup_registry_orders_forget_after_other_mutations() -> None:
    registry = build_startup_tool_registry(
        True,
        True,
        True,
        memory_revise_enabled=True,
    )

    assert [tool["name"] for tool in registry.tools] == [
        "list_tools",
        "memory_recall",
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


def test_startup_registry_accepts_captured_stringified_remember_arguments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    registry = build_startup_tool_registry(True)
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
    disabled = build_startup_tool_registry(False, False)
    enabled = build_startup_tool_registry(False, True)

    assert [tool["name"] for tool in disabled.tools] == [
        "list_tools",
        "memory_recall",
        "memory_inspect",
    ]
    assert disabled.call_tool("memory_archive", {}) is None
    assert disabled.call_tool("memory_restore", {}) is None
    assert [tool["name"] for tool in enabled.tools] == [
        "list_tools",
        "memory_recall",
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
    registry = build_startup_tool_registry(False, True)
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
    registry = build_startup_tool_registry(False, memory_revise_enabled=True)
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

import json
import logging
import stat
from pathlib import Path
from typing import Any

import pytest

from mnemosyne.mcp.tools.memory_list import TOOL, handle
from mnemosyne.mcp.tools.memory_list import handler as handler_module
from mnemosyne.mcp.tools.memory_list.definition import TOOL as DEFINED_TOOL
from mnemosyne.memory.errors import (
    CandidateLimitExceeded,
    InvalidMemoryListCursor,
    MemorySourceUnavailable,
    StaleMemoryListCursor,
    UnsafeMemoryPath,
)
from mnemosyne.memory.listing import (
    CollectionSelectionMode,
    MemoryCollectionSelector,
    MemoryInspectability,
    MemoryListItem,
    MemoryListPage,
    MemoryListResult,
    MemoryListSelector,
)
from mnemosyne.memory.records import (
    LegacyMemoryRecordV1,
    MemoryRecordV2,
    parse_memory_record,
)
from mnemosyne.memory.scopes import MemoryScope, SCOPE_DEFINITIONS
from mnemosyne.memory.store import StoredMemory


CANONICAL_ID = "mem_0123456789abcdef0123456789abcdef"


def _payload(result: dict[str, Any]) -> dict[str, Any]:
    return json.loads(result["content"][0]["text"])


def _empty_result() -> MemoryListResult:
    return MemoryListResult(
        memories=(),
        page=MemoryListPage(
            number=1,
            count=0,
            total_count=0,
            total_pages=0,
            truncated=False,
            next_cursor=None,
        ),
    )


def _legacy(
    *,
    inspectability: MemoryInspectability = MemoryInspectability.EXACT,
) -> MemoryListItem:
    return MemoryListItem(
        memory=StoredMemory(
            record=LegacyMemoryRecordV1(
                id="rainy-weekend",
                title="Rainy weekends",
                content="Private legacy content",
                tags=("private-legacy-tag",),
            ),
            scope=MemoryScope.PREFERENCE,
            relative_path="preference/private/rainy.json",
            fingerprint="private-legacy-fingerprint",
        ),
        inspectability=inspectability,
    )


def _canonical(*, state: str = "archived") -> MemoryListItem:
    record = parse_memory_record(
        {
            "schema_version": 2,
            "id": CANONICAL_ID,
            "scope": "project",
            "namespace": {
                "kind": "project",
                "id": "mnemosyne",
                "label": "Private namespace label",
            },
            "collection": {
                "id": "decisions",
                "label": "Private collection label",
            },
            "kind": "decision",
            "language": "en",
            "title": "Discovery contract",
            "content": "Private canonical content",
            "tags": ["private-canonical-tag"],
            "provenance": {
                "origin": "explicit_user_statement",
                "recorded_via": "memory_remember",
            },
            "lifecycle": {"state": state, "revision": 7},
            "created_at": "2026-07-19T12:00:00Z",
            "updated_at": "2026-07-19T13:00:00Z",
        }
    )
    assert isinstance(record, MemoryRecordV2)
    return MemoryListItem(
        memory=StoredMemory(
            record=record,
            scope=MemoryScope.PROJECT,
            relative_path=f"project/mnemosyne/decisions/{CANONICAL_ID}.json",
            fingerprint="private-canonical-fingerprint",
        ),
        inspectability=MemoryInspectability.EXACT,
    )


def _snapshot(root: Path) -> dict[str, tuple[bytes, int, int]]:
    return {
        path.relative_to(root).as_posix(): (
            path.read_bytes(),
            stat.S_IMODE(path.stat().st_mode),
            path.stat().st_mtime_ns,
        )
        for path in sorted(root.rglob("*.json"))
    }


def test_memory_list_exposes_portable_properties_and_four_strict_variants() -> None:
    assert TOOL["name"] == "memory_list"
    assert "read-only" in TOOL["description"]
    assert "content" in TOOL["description"]
    schema = TOOL["inputSchema"]
    assert set(schema) == {
        "type",
        "properties",
        "required",
        "additionalProperties",
        "oneOf",
    }
    assert schema["type"] == "object"
    assert schema["required"] == ["scope"]
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {
        "scope",
        "namespace_id",
        "collection_id",
        "page_size",
        "cursor",
    }
    scope_schema = schema["properties"]["scope"]
    assert scope_schema["type"] == "string"
    assert scope_schema["enum"] == [
        definition.scope.value for definition in SCOPE_DEFINITIONS
    ]
    assert all(
        definition.description in scope_schema["description"]
        for definition in SCOPE_DEFINITIONS
    )
    assert schema["properties"]["page_size"] == {
        "type": "integer",
        "description": (
            "Optional for initial requests only; omit when cursor is present."
        ),
        "minimum": 1,
        "maximum": 100,
        "default": 50,
    }
    assert schema["properties"]["cursor"] == {
        "type": "string",
        "description": (
            "For continuation requests only, repeat the exact selector from the initial "
            "request and omit page_size."
        ),
        "minLength": 1,
        "maxLength": 4096,
    }
    assert schema["properties"]["collection_id"]["oneOf"][1] == {
        "type": "null"
    }
    branches = schema["oneOf"]
    assert branches == [
        {
            "not": {
                "anyOf": [
                    {"required": ["namespace_id"]},
                    {"required": ["collection_id"]},
                    {"required": ["cursor"]},
                ]
            }
        },
        {
            "required": ["namespace_id"],
            "not": {"required": ["cursor"]},
        },
        {
            "required": ["cursor"],
            "not": {
                "anyOf": [
                    {"required": ["namespace_id"]},
                    {"required": ["collection_id"]},
                    {"required": ["page_size"]},
                ]
            },
        },
        {
            "required": ["namespace_id", "cursor"],
            "not": {"required": ["page_size"]},
        },
    ]


def test_memory_list_flat_property_prose_explains_every_request_variant() -> None:
    schema = TOOL["inputSchema"]
    properties = schema["properties"]
    scope_description = properties["scope"]["description"]

    assert "Valid argument combinations" in TOOL["description"]
    for variant in (
        "scope with optional page_size",
        "scope and namespace_id with optional collection_id and page_size",
        "scope and cursor",
        "scope, namespace_id, and cursor with optional collection_id",
    ):
        assert variant in TOOL["description"]
        assert variant in scope_description

    namespace_description = properties["namespace_id"]["description"]
    assert "Omit for scope-wide" in namespace_description
    assert "required when collection_id is present" in namespace_description
    assert "repeat" in namespace_description

    collection_description = properties["collection_id"]["description"]
    for constraint in ("only with namespace_id", "omitted", "null", "string", "repeat"):
        assert constraint in collection_description

    page_size_description = properties["page_size"]["description"]
    assert "initial requests only" in page_size_description
    assert "omit when cursor is present" in page_size_description

    cursor_description = properties["cursor"]["description"]
    assert "continuation requests only" in cursor_description
    assert "repeat the exact selector" in cursor_description
    assert "omit page_size" in cursor_description


def test_memory_list_remains_callable_through_top_level_only_projection() -> None:
    schema = TOOL["inputSchema"]
    flattened = {
        "properties": schema["properties"],
        "required": schema["required"],
    }
    requests = [
        {"scope": "project", "page_size": 5},
        {
            "scope": "project",
            "namespace_id": "mnemosyne",
            "collection_id": None,
            "page_size": 5,
        },
        {"scope": "project", "cursor": "opaque-cursor"},
        {
            "scope": "project",
            "namespace_id": "mnemosyne",
            "collection_id": "decisions",
            "cursor": "opaque-cursor",
        },
    ]

    projected_requests = [
        {
            name: value
            for name, value in request.items()
            if name in flattened["properties"]
        }
        for request in requests
    ]

    assert flattened["required"] == ["scope"]
    assert projected_requests == requests

    captured: dict[str, object] = {}

    def _list(selector, page_size, cursor):
        captured.update(
            selector=selector,
            page_size=page_size,
            cursor=cursor,
        )
        return MemoryListResult(
            memories=(),
            page=MemoryListPage(
                number=1,
                count=0,
                total_count=0,
                total_pages=0,
                truncated=False,
                next_cursor=None,
            ),
        )

    result = handle(projected_requests[0], list_operation=_list)

    assert result.get("isError") is not True
    assert captured == {
        "selector": MemoryListSelector(scope=MemoryScope.PROJECT),
        "page_size": 5,
        "cursor": None,
    }


def test_memory_list_package_reexports_definition_and_handler() -> None:
    assert TOOL is DEFINED_TOOL
    assert handle is handler_module.handle


@pytest.mark.parametrize(
    ("arguments", "expected_selector", "expected_page_size", "expected_cursor"),
    [
        (
            {"scope": "project"},
            MemoryListSelector(scope=MemoryScope.PROJECT),
            None,
            None,
        ),
        (
            {"scope": "project", "namespace_id": "mnemosyne", "page_size": 25},
            MemoryListSelector(
                scope=MemoryScope.PROJECT,
                namespace_id="mnemosyne",
            ),
            25,
            None,
        ),
        (
            {
                "scope": "project",
                "namespace_id": "mnemosyne",
                "collection_id": None,
            },
            MemoryListSelector(
                scope=MemoryScope.PROJECT,
                namespace_id="mnemosyne",
                collection=MemoryCollectionSelector.collectionless(),
            ),
            None,
            None,
        ),
        (
            {
                "scope": "project",
                "namespace_id": "mnemosyne",
                "collection_id": "decisions",
                "cursor": "opaque-cursor",
            },
            MemoryListSelector(
                scope=MemoryScope.PROJECT,
                namespace_id="mnemosyne",
                collection=MemoryCollectionSelector.exact("decisions"),
            ),
            None,
            "opaque-cursor",
        ),
    ],
)
def test_memory_list_adapts_omission_sensitive_selectors_and_pagination(
    arguments: dict[str, object],
    expected_selector: MemoryListSelector,
    expected_page_size: int | None,
    expected_cursor: str | None,
) -> None:
    observed: list[tuple[MemoryListSelector, int | None, str | None]] = []

    def operation(
        selector: MemoryListSelector,
        page_size: int | None,
        cursor: str | None,
    ) -> MemoryListResult:
        observed.append((selector, page_size, cursor))
        return _empty_result()

    result = handle(arguments, list_operation=operation)

    assert _payload(result)["status"] == "ok"
    assert observed == [
        (expected_selector, expected_page_size, expected_cursor)
    ]


@pytest.mark.parametrize(
    ("arguments", "code", "field"),
    [
        (None, "invalid_request", "request"),
        ({"scope": "project", "path": "/private"}, "invalid_request", "request"),
        ({}, "invalid_scope", "scope"),
        ({"scope": "missing"}, "invalid_scope", "scope"),
        (
            {"scope": "project", "namespace_id": "Invalid"},
            "invalid_namespace",
            "namespace_id",
        ),
        (
            {"scope": "project", "collection_id": None},
            "invalid_collection",
            "collection_id",
        ),
        (
            {
                "scope": "project",
                "namespace_id": "mnemosyne",
                "collection_id": "Invalid",
            },
            "invalid_collection",
            "collection_id",
        ),
        ({"scope": "project", "page_size": True}, "invalid_page_size", "page_size"),
        ({"scope": "project", "page_size": None}, "invalid_page_size", "page_size"),
        ({"scope": "project", "cursor": None}, "invalid_cursor", "cursor"),
        ({"scope": "project", "cursor": ""}, "invalid_cursor", "cursor"),
        ({"scope": "project", "cursor": "x" * 4097}, "invalid_cursor", "cursor"),
        (
            {"scope": "project", "cursor": "opaque", "page_size": None},
            "invalid_cursor",
            "cursor",
        ),
    ],
)
def test_memory_list_rejects_invalid_requests_before_operation(
    arguments: object,
    code: str,
    field: str,
) -> None:
    result = handle(
        arguments,
        list_operation=lambda *args: pytest.fail("operation must not run"),
    )

    assert result["isError"] is True
    payload = _payload(result)
    assert payload["status"] == "invalid_request"
    assert payload["code"] == code
    assert payload["field"] == field
    assert set(payload) == {"status", "code", "field", "message"}


def test_memory_list_projects_legacy_and_canonical_metadata_without_content() -> None:
    result_value = MemoryListResult(
        memories=(
            _legacy(inspectability=MemoryInspectability.AMBIGUOUS),
            _canonical(state="archived"),
        ),
        page=MemoryListPage(
            number=2,
            count=2,
            total_count=4,
            total_pages=2,
            truncated=False,
            next_cursor=None,
        ),
    )

    result = handle(
        {"scope": "project"},
        list_operation=lambda *args: result_value,
    )

    assert _payload(result) == {
        "status": "ok",
        "memories": [
            {
                "reference": {
                    "schema_version": 1,
                    "scope": "preference",
                    "id": "rainy-weekend",
                },
                "title": "Rainy weekends",
                "inspectability": "ambiguous",
            },
            {
                "reference": {
                    "schema_version": 2,
                    "scope": "project",
                    "namespace_id": "mnemosyne",
                    "collection_id": "decisions",
                    "id": CANONICAL_ID,
                },
                "title": "Discovery contract",
                "inspectability": "exact",
                "kind": "decision",
                "lifecycle": {"state": "archived"},
            },
        ],
        "page": {
            "number": 2,
            "count": 2,
            "total_count": 4,
            "total_pages": 2,
            "truncated": False,
            "next_cursor": None,
        },
    }
    serialized = result["content"][0]["text"]
    forbidden = [
        "Private legacy content",
        "private-legacy-tag",
        "private/rainy.json",
        "private-legacy-fingerprint",
        "Private canonical content",
        "private-canonical-tag",
        "Private namespace label",
        "Private collection label",
        "private-canonical-fingerprint",
        '"revision"',
        '"language"',
        '"provenance"',
        '"created_at"',
        '"updated_at"',
    ]
    assert all(value not in serialized for value in forbidden)


@pytest.mark.parametrize(
    ("error", "expected", "level"),
    [
        (
            InvalidMemoryListCursor(),
            {
                "status": "invalid_request",
                "code": "invalid_cursor",
                "field": "cursor",
                "message": "cursor is invalid",
            },
            logging.WARNING,
        ),
        (
            StaleMemoryListCursor(),
            {
                "status": "conflict",
                "code": "stale_cursor",
                "message": "cursor is stale; start a new listing",
            },
            logging.WARNING,
        ),
        (
            CandidateLimitExceeded(),
            {
                "status": "storage_error",
                "code": "candidate_limit_exceeded",
                "message": (
                    "selected memory container contains more than 1000 candidate files"
                ),
            },
            logging.WARNING,
        ),
        (
            UnsafeMemoryPath("/private/path"),
            {
                "status": "storage_error",
                "code": "memory_source_unavailable",
                "message": "memory could not be listed",
            },
            logging.WARNING,
        ),
        (
            MemorySourceUnavailable("private source detail"),
            {
                "status": "storage_error",
                "code": "memory_source_unavailable",
                "message": "memory could not be listed",
            },
            logging.WARNING,
        ),
        (
            OSError("private os detail"),
            {
                "status": "storage_error",
                "code": "memory_source_unavailable",
                "message": "memory could not be listed",
            },
            logging.WARNING,
        ),
        (
            RuntimeError("private internal detail"),
            {
                "status": "internal_error",
                "code": "internal_error",
                "message": "memory could not be listed",
            },
            logging.ERROR,
        ),
    ],
)
def test_memory_list_maps_failures_and_logs_one_bounded_terminal_event(
    error: Exception,
    expected: dict[str, object],
    level: int,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def operation(*args: object) -> MemoryListResult:
        raise error

    caplog.set_level(logging.INFO, logger="mcp.memory_list")
    result = handle(
        {
            "scope": "project",
            "namespace_id": "private-namespace",
            "collection_id": "private-collection",
        },
        list_operation=operation,
    )

    assert result["isError"] is True
    assert _payload(result) == expected
    records = [record for record in caplog.records if record.name == "mcp.memory_list"]
    assert len(records) == 1
    assert records[0].levelno == level
    message = records[0].getMessage()
    assert message.startswith("event=memory_list outcome=")
    assert "scope=project" in message
    assert "namespace_selector_present=True" in message
    assert "collection_selector_present=True" in message
    assert records[0].exc_info is None
    forbidden = [
        "private-namespace",
        "private-collection",
        "/private/path",
        "private source detail",
        "private os detail",
        "private internal detail",
    ]
    assert all(value not in message for value in forbidden)


def test_memory_list_logs_one_content_free_success_event(
    caplog: pytest.LogCaptureFixture,
) -> None:
    result_value = MemoryListResult(
        memories=(_canonical(state="active"),),
        page=MemoryListPage(
            number=1,
            count=1,
            total_count=2,
            total_pages=2,
            truncated=True,
            next_cursor="private-cursor",
        ),
    )
    caplog.set_level(logging.INFO, logger="mcp.memory_list")

    result = handle(
        {"scope": "project", "namespace_id": "mnemosyne"},
        list_operation=lambda *args: result_value,
    )

    assert _payload(result)["status"] == "ok"
    records = [record for record in caplog.records if record.name == "mcp.memory_list"]
    assert len(records) == 1
    assert records[0].getMessage() == (
        "event=memory_list outcome=ok scope=project "
        "namespace_selector_present=True collection_selector_present=False "
        "returned_count=1 total_count=2 page_number=1 truncated=True"
    )
    assert "mnemosyne" not in records[0].getMessage()
    assert "private-cursor" not in records[0].getMessage()
    assert CANONICAL_ID not in records[0].getMessage()


def test_memory_list_validation_precedes_memory_root_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        handler_module,
        "get_memory_root",
        lambda: pytest.fail("memory root must not be resolved"),
    )

    result = handle({"scope": "missing"})

    assert _payload(result)["code"] == "invalid_scope"


def test_memory_list_missing_root_returns_empty_without_initialization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "application" / "memory"
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(root))

    result = handle({"scope": "project"})

    assert _payload(result) == {
        "status": "ok",
        "memories": [],
        "page": {
            "number": 1,
            "count": 0,
            "total_count": 0,
            "total_pages": 0,
            "truncated": False,
            "next_cursor": None,
        },
    }
    assert not (tmp_path / "application").exists()


def test_memory_list_preserves_existing_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "preference" / "legacy" / "rainy.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "rainy-weekend",
                "title": "Rainy weekends",
                "content": "Private source content",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    before = _snapshot(tmp_path)

    result = handle({"scope": "preference"})

    assert _payload(result)["status"] == "ok"
    assert _snapshot(tmp_path) == before

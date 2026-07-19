import json
import logging
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from mnemosyne.mcp.tools._memory_revise import parse_revise_request
from mnemosyne.mcp.tools.memory_revise import TOOL, handle
from mnemosyne.mcp.tools.memory_revise import handler as handler_module
from mnemosyne.mcp.tools.memory_revise.definition import TOOL as DEFINED_TOOL
from mnemosyne.memory.errors import (
    DisallowedMemoryContent,
    MemoryNotFound,
    MemorySourceUnavailable,
    MemoryValidationError,
    MutationDisabled,
    ReplacementOutcomeUncertain,
    RevisionConflict,
    UnsafeMemoryPath,
    WriteConflict,
)
from mnemosyne.memory.records import (
    MemoryLifecycle,
    MemoryReference,
    MemoryRevision,
    parse_memory_record,
    serialize_memory_record,
)
from mnemosyne.memory.scopes import MemoryScope
from mnemosyne.memory.service import MemoryResult


CANONICAL_ID = "mem_0123456789abcdef0123456789abcdef"


def _arguments() -> dict[str, object]:
    return {
        "reference": {
            "schema_version": 2,
            "scope": "preference",
            "namespace_id": "tea",
            "collection_id": "favorites",
            "id": CANONICAL_ID,
        },
        "expected_revision": 3,
        "namespace_label": "Tea",
        "collection_label": "Favorites",
        "title": "Japanese green tea",
        "content": "The user enjoys sencha and gyokuro.",
        "tags": ["tea", "japanese-green-tea"],
    }


def _payload(result: dict[str, Any]) -> dict[str, Any]:
    return json.loads(result["content"][0]["text"])


def _record(*, state: str = "active", revision: int = 4):
    return parse_memory_record(
        {
            "schema_version": 2,
            "id": CANONICAL_ID,
            "scope": "preference",
            "namespace": {"kind": "domain", "id": "tea", "label": "Tea"},
            "collection": {"id": "favorites", "label": "Favorites"},
            "kind": "preference",
            "language": "en",
            "title": "Japanese green tea",
            "content": "The user enjoys sencha and gyokuro.",
            "tags": ["tea", "japanese-green-tea"],
            "provenance": {
                "origin": "explicit_user_statement",
                "recorded_via": "memory_remember",
            },
            "lifecycle": {"state": state, "revision": revision},
            "created_at": "2026-07-18T12:00:00Z",
            "updated_at": "2026-07-19T12:00:00Z",
        }
    )


def test_memory_revise_exposes_a_strict_complete_replacement_definition() -> None:
    assert TOOL["name"] == "memory_revise"
    description = TOOL["description"].lower()
    assert all(
        term in description
        for term in ("complete", "canonical", "approval", "preserves", "secrets")
    )
    schema = TOOL["inputSchema"]
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["required"] == [
        "reference",
        "expected_revision",
        "namespace_label",
        "collection_label",
        "title",
        "content",
        "tags",
    ]
    assert set(schema["properties"]) == set(schema["required"])
    assert schema["properties"]["expected_revision"] == {
        "type": "integer",
        "minimum": 1,
    }
    reference = schema["properties"]["reference"]
    assert reference["properties"]["schema_version"] == {"const": 2}
    assert reference["additionalProperties"] is False
    assert reference["required"] == [
        "schema_version",
        "scope",
        "namespace_id",
        "collection_id",
        "id",
    ]
    assert schema["properties"]["tags"] == {
        "type": "array",
        "items": {
            "type": "string",
            "minLength": 1,
            "maxLength": 50,
            "pattern": "\\S",
        },
        "minItems": 0,
        "maxItems": 10,
        "uniqueItems": True,
    }


def test_memory_revise_package_reexports_definition_and_handler() -> None:
    assert TOOL is DEFINED_TOOL
    assert handle is handler_module.handle


def test_revise_request_parser_adapts_identity_and_normalized_replacement() -> None:
    arguments = _arguments()
    arguments.update(
        {
            "namespace_label": "  Tea  ",
            "collection_label": " Favorites ",
            "title": " Japanese green tea ",
            "content": " The user enjoys sencha and gyokuro. ",
            "tags": [" Tea ", "japanese-green-tea"],
        }
    )

    request = parse_revise_request(arguments)

    assert request.reference == MemoryReference(
        scope=MemoryScope.PREFERENCE,
        namespace_id="tea",
        collection_id="favorites",
        id=CANONICAL_ID,
    )
    assert request.revision == MemoryRevision(
        expected_revision=3,
        namespace_label="Tea",
        collection_label="Favorites",
        title="Japanese green tea",
        content="The user enjoys sencha and gyokuro.",
        tags=("Tea", "japanese-green-tea"),
    )


@pytest.mark.parametrize(
    ("mutate", "code", "field"),
    [
        (lambda value: value.pop("reference"), "invalid_reference", "reference"),
        (
            lambda value: value.update({"expected_revision": True}),
            "invalid_expected_revision",
            "expected_revision",
        ),
        (
            lambda value: value.update({"expected_revision": 0}),
            "invalid_expected_revision",
            "expected_revision",
        ),
        (
            lambda value: value.pop("namespace_label"),
            "invalid_record",
            "revision",
        ),
        (
            lambda value: value.update({"content": " "}),
            "invalid_record",
            "content",
        ),
        (
            lambda value: value.update({"path": "/private/memory.json"}),
            "invalid_record",
            "revision",
        ),
        (
            lambda value: value.update({"language": "en"}),
            "invalid_record",
            "revision",
        ),
        (
            lambda value: value["reference"].update({"schema_version": 1}),
            "invalid_reference",
            "reference",
        ),
    ],
)
def test_revise_request_parser_rejects_invalid_or_forbidden_fields(
    mutate,
    code: str,
    field: str,
) -> None:
    arguments = deepcopy(_arguments())
    mutate(arguments)

    with pytest.raises(MemoryValidationError) as caught:
        parse_revise_request(arguments)

    assert caught.value.code == code
    assert caught.value.field == field


def test_revise_request_accepts_nullable_labels_title_and_collection() -> None:
    arguments = _arguments()
    arguments["reference"]["collection_id"] = None
    arguments.update(
        {
            "namespace_label": None,
            "collection_label": None,
            "title": None,
            "tags": [],
        }
    )

    request = parse_revise_request(arguments)

    assert request.reference.collection_id is None
    assert request.revision.namespace_label is None
    assert request.revision.collection_label is None
    assert request.revision.title is None
    assert request.revision.tags == ()


def test_memory_revise_direct_call_is_disabled_without_registration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        handler_module,
        "get_memory_root",
        lambda: pytest.fail("memory root must not be resolved"),
    )

    result = handle(_arguments())

    assert result["isError"] is True
    assert _payload(result) == {
        "status": "policy_error",
        "code": "mutation_disabled",
        "message": "memory revise is disabled",
    }


@pytest.mark.parametrize(
    ("status", "state", "revision"),
    [
        ("revised", "active", 4),
        ("revised", "archived", 4),
        ("already_current", "active", 3),
        ("already_current", "archived", 3),
    ],
)
def test_memory_revise_executes_normalized_request_and_returns_minimal_result(
    status: str,
    state: str,
    revision: int,
) -> None:
    observed: list[tuple[MemoryReference, MemoryRevision]] = []
    arguments = _arguments()
    arguments["namespace_label"] = " Tea "

    def revise_operation(
        reference: MemoryReference,
        replacement: MemoryRevision,
    ) -> MemoryResult:
        observed.append((reference, replacement))
        return MemoryResult(
            status=status,
            memory=_record(state=state, revision=revision),
        )

    result = handle(
        arguments,
        mutations_enabled=True,
        revise_operation=revise_operation,
    )

    assert observed == [
        (
            MemoryReference(
                scope=MemoryScope.PREFERENCE,
                namespace_id="tea",
                collection_id="favorites",
                id=CANONICAL_ID,
            ),
            MemoryRevision(
                expected_revision=3,
                namespace_label="Tea",
                collection_label="Favorites",
                title="Japanese green tea",
                content="The user enjoys sencha and gyokuro.",
                tags=("tea", "japanese-green-tea"),
            ),
        )
    ]
    assert _payload(result) == {
        "status": status,
        "reference": {
            "schema_version": 2,
            "scope": "preference",
            "namespace_id": "tea",
            "collection_id": "favorites",
            "id": CANONICAL_ID,
        },
        "lifecycle": {"state": state, "revision": revision},
    }
    serialized = result["content"][0]["text"]
    assert all(
        value not in serialized
        for value in ("Japanese green tea", "sencha", "gyokuro", "Favorites")
    )


@pytest.mark.parametrize(
    "bad_result",
    [
        MemoryResult(status="unexpected", memory=_record()),
        MemoryResult(
            status="revised",
            memory=replace(_record(), id="mem_fedcba9876543210fedcba9876543210"),
        ),
        MemoryResult(status="revised", memory=_record(revision=3)),
        MemoryResult(
            status="already_current",
            memory=_record(revision=4),
        ),
        MemoryResult(
            status="revised",
            memory=replace(_record(), content="Different replacement"),
        ),
    ],
)
def test_memory_revise_rejects_inconsistent_operation_results(
    bad_result: MemoryResult,
) -> None:
    result = handle(
        _arguments(),
        mutations_enabled=True,
        revise_operation=lambda reference, revision: bad_result,
    )

    assert result["isError"] is True
    assert _payload(result) == {
        "status": "internal_error",
        "code": "internal_error",
        "message": "memory could not be revised",
    }


def test_memory_revise_updates_one_source_file_through_the_shared_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _record(revision=3)
    original = replace(
        original,
        title="Tea preference",
        content="The user enjoys Japanese green tea.",
        tags=("tea",),
        updated_at=datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc),
        lifecycle=MemoryLifecycle(state=original.lifecycle.state, revision=3),
    )
    path = tmp_path / "preference" / "tea" / "favorites" / f"{CANONICAL_ID}.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(serialize_memory_record(original)),
        encoding="utf-8",
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    result = handle(_arguments(), mutations_enabled=True)

    assert _payload(result)["status"] == "revised"
    stored = parse_memory_record(json.loads(path.read_text(encoding="utf-8")))
    assert stored.id == original.id
    assert stored.content == "The user enjoys sencha and gyokuro."
    assert stored.lifecycle.revision == 4
    assert len(list(tmp_path.rglob("*.json"))) == 1


def test_memory_revise_maps_real_collectionless_mismatch_without_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = replace(_record(revision=3), collection=None)
    path = tmp_path / "preference" / "tea" / f"{CANONICAL_ID}.json"
    path.parent.mkdir(parents=True)
    serialized = json.dumps(serialize_memory_record(original))
    path.write_text(serialized, encoding="utf-8")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    arguments = _arguments()
    arguments["reference"]["collection_id"] = None

    result = handle(arguments, mutations_enabled=True)

    assert _payload(result) == {
        "status": "invalid_request",
        "code": "invalid_collection",
        "field": "collection_label",
        "message": "collection label is invalid for memory",
    }
    assert path.read_text(encoding="utf-8") == serialized
    assert len(list(tmp_path.rglob("*.json"))) == 1


def test_memory_revise_maps_collection_mismatch_to_public_flat_field(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="mcp.memory_revise")

    def fail(reference: MemoryReference, revision: MemoryRevision) -> MemoryResult:
        raise MemoryValidationError(
            "invalid_collection",
            "collection.label",
            "private collection detail",
        )

    result = handle(
        _arguments(),
        mutations_enabled=True,
        revise_operation=fail,
    )

    assert _payload(result) == {
        "status": "invalid_request",
        "code": "invalid_collection",
        "field": "collection_label",
        "message": "collection label is invalid for memory",
    }
    assert len([r for r in caplog.records if r.name == "mcp.memory_revise"]) == 1
    assert "private collection detail" not in caplog.text


@pytest.mark.parametrize(
    ("error", "expected", "level", "outcome"),
    [
        (
            DisallowedMemoryContent(),
            {
                "status": "refused",
                "code": "disallowed_content",
                "message": "memory contains content that Mnemosyne does not store",
            },
            logging.WARNING,
            "refused",
        ),
        (
            MutationDisabled(),
            {
                "status": "policy_error",
                "code": "mutation_disabled",
                "message": "memory revise is disabled",
            },
            logging.WARNING,
            "policy_error",
        ),
        (
            MemoryNotFound(),
            {
                "status": "not_found",
                "code": "not_found",
                "message": "memory to revise was not found",
            },
            logging.WARNING,
            "not_found",
        ),
        (
            RevisionConflict(),
            {
                "status": "conflict",
                "code": "revision_conflict",
                "message": "memory to revise is not at the expected revision",
            },
            logging.WARNING,
            "conflict",
        ),
        (
            WriteConflict(),
            {
                "status": "conflict",
                "code": "write_conflict",
                "message": "memory changed before it could be revised",
            },
            logging.WARNING,
            "conflict",
        ),
        (
            ReplacementOutcomeUncertain(),
            {
                "status": "uncertain",
                "code": "replacement_outcome_uncertain",
                "message": (
                    "memory revise outcome is uncertain; inspect the same reference "
                    "before any retry"
                ),
            },
            logging.WARNING,
            "uncertain",
        ),
        (
            UnsafeMemoryPath("/private/path"),
            {
                "status": "storage_error",
                "code": "memory_source_unavailable",
                "message": "memory could not be revised",
            },
            logging.WARNING,
            "storage_error",
        ),
        (
            MemorySourceUnavailable("private source"),
            {
                "status": "storage_error",
                "code": "memory_source_unavailable",
                "message": "memory could not be revised",
            },
            logging.WARNING,
            "storage_error",
        ),
        (
            OSError("private os detail"),
            {
                "status": "storage_error",
                "code": "memory_source_unavailable",
                "message": "memory could not be revised",
            },
            logging.WARNING,
            "storage_error",
        ),
        (
            RuntimeError("private internal detail"),
            {
                "status": "internal_error",
                "code": "internal_error",
                "message": "memory could not be revised",
            },
            logging.ERROR,
            "internal_error",
        ),
    ],
)
def test_memory_revise_maps_failures_and_logs_one_content_free_event(
    error: Exception,
    expected: dict[str, str],
    level: int,
    outcome: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="mcp.memory_revise")

    def fail(reference: MemoryReference, revision: MemoryRevision) -> MemoryResult:
        raise error

    result = handle(
        _arguments(),
        mutations_enabled=True,
        revise_operation=fail,
    )

    assert result["isError"] is True
    assert _payload(result) == expected
    records = [record for record in caplog.records if record.name == "mcp.memory_revise"]
    assert len(records) == 1
    record = records[0]
    assert record.levelno == level
    message = record.getMessage()
    assert f"event=memory_revise outcome={outcome}" in message
    assert "schema_version=2 scope=preference" in message
    assert record.exc_info is None
    assert all(
        value not in message
        for value in (
            CANONICAL_ID,
            "tea",
            "favorites",
            "Japanese green tea",
            "sencha",
            "gyokuro",
            "/private",
            "private source",
            "private internal",
        )
    )


def test_memory_revise_logs_success_with_only_lifecycle_metadata(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="mcp.memory_revise")

    result = handle(
        _arguments(),
        mutations_enabled=True,
        revise_operation=lambda reference, revision: MemoryResult(
            status="revised",
            memory=_record(),
        ),
    )

    assert _payload(result)["status"] == "revised"
    records = [record for record in caplog.records if record.name == "mcp.memory_revise"]
    assert len(records) == 1
    message = records[0].getMessage()
    assert message == (
        "event=memory_revise outcome=revised schema_version=2 scope=preference "
        "lifecycle_state=active revision=4"
    )
    assert records[0].exc_info is None


def test_memory_revise_invalid_call_logs_one_bounded_event_without_root(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="mcp.memory_revise")
    monkeypatch.setattr(
        handler_module,
        "get_memory_root",
        lambda: pytest.fail("memory root must not be resolved"),
    )

    result = handle({})

    assert _payload(result)["code"] == "invalid_reference"
    records = [record for record in caplog.records if record.name == "mcp.memory_revise"]
    assert len(records) == 1
    assert records[0].getMessage() == (
        "event=memory_revise outcome=invalid_request "
        "code=invalid_reference field=reference"
    )
    assert records[0].exc_info is None

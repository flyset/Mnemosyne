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
    ContentRefusalReason,
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
        "title",
        "content",
        "tags",
    ]
    assert set(schema["properties"]) == set(schema["required"]) | {
        "collection_label"
    }
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
    assert schema["properties"]["namespace_label"] == {
        "type": ["string", "null"],
        "description": (
            "Required complete replacement for the namespace label; send JSON null "
            "to remove the label."
        ),
        "minLength": 1,
        "maxLength": 100,
        "pattern": "\\S",
    }
    assert schema["properties"]["collection_label"] == {
        "type": ["string", "null"],
        "description": (
            "Required when reference.collection_id is a string; omit when "
            "reference.collection_id is null. For a collected memory, send a string "
            "or JSON null to replace its label."
        ),
        "minLength": 1,
        "maxLength": 100,
        "pattern": "\\S",
    }
    assert schema["properties"]["title"] == {
        "type": ["string", "null"],
        "description": (
            "Required complete replacement for the title; send JSON null to remove it."
        ),
        "minLength": 1,
        "maxLength": 200,
        "pattern": "\\S",
    }


def test_memory_revise_description_explains_safe_refusal_recovery() -> None:
    description = TOOL["description"]

    assert "disallowed_content" in description
    assert "bounded field and reason" in description
    assert "Do not obfuscate suspected sensitive data" in description
    assert (
        "retry only when the user confirms that the formatting is benign and "
        "approves the exact revised call"
    ) in description


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
    ("mutate", "code", "field", "message"),
    [
        (
            lambda value: value.pop("reference"),
            "invalid_reference",
            "reference",
            "reference is invalid",
        ),
        (
            lambda value: value.update({"expected_revision": True}),
            "invalid_expected_revision",
            "expected_revision",
            "expected revision is invalid",
        ),
        (
            lambda value: value.update({"expected_revision": 0}),
            "invalid_expected_revision",
            "expected_revision",
            "expected revision is invalid",
        ),
        (
            lambda value: value.pop("namespace_label"),
            "invalid_record",
            "namespace_label",
            "namespace label is invalid",
        ),
        (
            lambda value: value.update({"content": " "}),
            "invalid_record",
            "content",
            "content is invalid",
        ),
        (
            lambda value: value.update({"path": "/private/memory.json"}),
            "invalid_record",
            "revision",
            "revision request is invalid",
        ),
        (
            lambda value: value.update({"language": "en"}),
            "invalid_record",
            "revision",
            "revision request is invalid",
        ),
        (
            lambda value: value.update({"occurred_at": "2026-07-17T09:30:00Z"}),
            "invalid_record",
            "revision",
            "revision request is invalid",
        ),
        (
            lambda value: value["reference"].update({"schema_version": 1}),
            "invalid_reference",
            "reference",
            "reference is invalid",
        ),
    ],
)
def test_revise_request_parser_rejects_invalid_or_forbidden_fields(
    mutate,
    code: str,
    field: str,
    message: str,
) -> None:
    arguments = deepcopy(_arguments())
    mutate(arguments)

    with pytest.raises(MemoryValidationError) as caught:
        parse_revise_request(arguments)

    assert caught.value.code == code
    assert caught.value.field == field
    assert caught.value.message == message


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


def test_revise_request_accepts_omitted_collection_label_only_when_collectionless() -> None:
    collectionless = _arguments()
    collectionless["reference"]["collection_id"] = None
    del collectionless["collection_label"]

    request = parse_revise_request(collectionless)

    assert request.reference.collection_id is None
    assert request.revision.collection_label is None

    collected = _arguments()
    del collected["collection_label"]

    with pytest.raises(MemoryValidationError) as caught:
        parse_revise_request(collected)

    assert caught.value.code == "invalid_record"
    assert caught.value.field == "collection_label"
    assert caught.value.message == "collection label is required for collected memory"


def test_revise_request_preserves_literal_null_collection_label_as_text() -> None:
    arguments = _arguments()
    arguments["collection_label"] = "null"

    request = parse_revise_request(arguments)

    assert request.revision.collection_label == "null"


def test_revise_request_reports_invalid_collection_label_consistently() -> None:
    arguments = _arguments()
    arguments["collection_label"] = ""

    with pytest.raises(MemoryValidationError) as caught:
        parse_revise_request(arguments)

    assert caught.value.code == "invalid_record"
    assert caught.value.field == "collection_label"
    assert caught.value.message == "collection label is invalid"


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


def test_memory_revise_updates_collectionless_source_with_omitted_collection_label(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = replace(
        _record(revision=3),
        collection=None,
        title="Tea preference",
        content="Original collectionless content.",
        tags=("tea",),
        updated_at=datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc),
    )
    path = tmp_path / "preference" / "tea" / f"{CANONICAL_ID}.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(serialize_memory_record(original)),
        encoding="utf-8",
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    arguments = _arguments()
    arguments["reference"]["collection_id"] = None
    del arguments["collection_label"]

    result = handle(arguments, mutations_enabled=True)

    assert _payload(result) == {
        "status": "revised",
        "reference": {
            "schema_version": 2,
            "scope": "preference",
            "namespace_id": "tea",
            "collection_id": None,
            "id": CANONICAL_ID,
        },
        "lifecycle": {"state": "active", "revision": 4},
    }
    stored = parse_memory_record(json.loads(path.read_text(encoding="utf-8")))
    assert stored.collection is None
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
    ("domain_field", "expected_public_field"),
    [
        ("namespace.label", "namespace_label"),
        ("collection.label", "collection_label"),
        ("title", "title"),
        ("content", "content"),
        ("tags", "tags"),
    ],
)
def test_memory_revise_maps_refusal_to_bounded_flat_public_field(
    domain_field: str,
    expected_public_field: str,
) -> None:
    def fail(reference: MemoryReference, revision: MemoryRevision) -> MemoryResult:
        raise DisallowedMemoryContent(
            domain_field,
            ContentRefusalReason.CREDENTIAL_SHAPE,
        )

    result = handle(
        _arguments(),
        mutations_enabled=True,
        revise_operation=fail,
    )

    assert result["isError"] is True
    assert _payload(result) == {
        "status": "refused",
        "code": "disallowed_content",
        "field": expected_public_field,
        "reason": "credential_shape",
        "message": (
            "memory field resembles content that Mnemosyne does not store; "
            "review the named field and retry only if the user confirms that "
            "the formatting is benign"
        ),
    }


@pytest.mark.parametrize(
    ("error", "expected", "level", "outcome"),
    [
        (
            DisallowedMemoryContent(
                "content",
                ContentRefusalReason.COMPACT_TOKEN_SHAPE,
            ),
            {
                "status": "refused",
                "code": "disallowed_content",
                "field": "content",
                "reason": "compact_token_shape",
                "message": (
                    "memory field resembles content that Mnemosyne does not store; "
                    "review the named field and retry only if the user confirms that "
                    "the formatting is benign"
                ),
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
    if isinstance(error, DisallowedMemoryContent):
        assert " field=" not in message
        assert error.reason.value not in message
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

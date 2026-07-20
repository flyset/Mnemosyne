import json
import logging
from pathlib import Path
from typing import Any

import pytest

from mnemosyne.mcp.tools._memory_lifecycle import parse_lifecycle_request
from mnemosyne.mcp.tools.memory_archive import TOOL, handle
from mnemosyne.mcp.tools.memory_archive import handler as handler_module
from mnemosyne.mcp.tools.memory_archive.definition import TOOL as DEFINED_TOOL
from mnemosyne.memory.errors import (
    MemoryNotFound,
    MemorySourceUnavailable,
    MemoryValidationError,
    MutationDisabled,
    ReplacementOutcomeUncertain,
    RevisionConflict,
    UnsafeMemoryPath,
    WriteConflict,
)
from mnemosyne.memory.records import MemoryReference, parse_memory_record
from mnemosyne.memory.scopes import MemoryScope, SCOPE_DEFINITIONS
from mnemosyne.memory.service import MemoryResult


CANONICAL_ID = "mem_0123456789abcdef0123456789abcdef"


def _arguments() -> dict[str, object]:
    return {
        "reference": {
            "schema_version": 2,
            "scope": "project",
            "namespace_id": "mnemosyne",
            "collection_id": "decisions",
            "id": CANONICAL_ID,
        },
        "expected_revision": 3,
    }


def _payload(result: dict[str, Any]) -> dict[str, Any]:
    return json.loads(result["content"][0]["text"])


def _record(*, state: str = "archived", revision: int = 4, event: bool = False):
    payload = {
        "schema_version": 2,
        "id": CANONICAL_ID,
        "scope": "project",
        "namespace": {"kind": "project", "id": "mnemosyne", "label": "Private"},
        "collection": {"id": "decisions", "label": "Private"},
        "kind": "event" if event else "decision",
        "language": "en",
        "title": "Private title",
        "content": "Archive lifecycle context.",
        "tags": ["private-tag"],
        "provenance": {
            "origin": "explicit_user_statement",
            "recorded_via": "memory_remember",
        },
        "lifecycle": {"state": state, "revision": revision},
        "created_at": "2026-07-18T12:00:00Z",
        "updated_at": "2026-07-19T12:00:00Z",
    }
    if event:
        payload["occurred_at"] = "2026-07-17T09:30:00Z"
    return parse_memory_record(payload)


def test_memory_archive_exposes_a_strict_canonical_revision_definition() -> None:
    assert TOOL["name"] == "memory_archive"
    assert "archive" in TOOL["description"].lower()
    assert "canonical" in TOOL["description"].lower()

    schema = TOOL["inputSchema"]
    assert schema["type"] == "object"
    assert schema["required"] == ["reference", "expected_revision"]
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {"reference", "expected_revision"}
    assert schema["properties"]["expected_revision"] == {
        "type": "integer",
        "minimum": 1,
    }

    reference = schema["properties"]["reference"]
    assert reference["type"] == "object"
    assert reference["required"] == [
        "schema_version",
        "scope",
        "namespace_id",
        "collection_id",
        "id",
    ]
    assert reference["additionalProperties"] is False
    assert set(reference["properties"]) == set(reference["required"])
    assert reference["properties"]["schema_version"] == {"const": 2}
    assert reference["properties"]["namespace_id"]["pattern"] == (
        "^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$"
    )
    assert reference["properties"]["collection_id"]["oneOf"][1] == {
        "type": "null"
    }
    assert reference["properties"]["id"] == {
        "type": "string",
        "pattern": "^mem_[0-9a-f]{32}$",
    }
    assert reference["properties"]["scope"]["oneOf"] == [
        {
            "const": definition.scope.value,
            "description": definition.description,
        }
        for definition in SCOPE_DEFINITIONS
    ]


def test_memory_archive_package_reexports_definition_and_handler() -> None:
    assert TOOL is DEFINED_TOOL
    assert handle is handler_module.handle


def test_lifecycle_request_parser_adapts_canonical_identity_and_revision() -> None:
    request = parse_lifecycle_request(_arguments())

    assert request.reference == MemoryReference(
        scope=MemoryScope.PROJECT,
        namespace_id="mnemosyne",
        collection_id="decisions",
        id=CANONICAL_ID,
    )
    assert request.expected_revision == 3


@pytest.mark.parametrize(
    ("mutate", "code", "field"),
    [
        (lambda value: value.pop("reference"), "invalid_reference", "reference"),
        (
            lambda value: value.update({"path": "project/private.json"}),
            "invalid_reference",
            "reference",
        ),
        (
            lambda value: value.update(
                {
                    "reference": {
                        "schema_version": 1,
                        "scope": "project",
                        "id": "legacy",
                    }
                }
            ),
            "invalid_reference",
            "reference",
        ),
        (
            lambda value: value["reference"].update({"schema_version": 2.0}),
            "invalid_reference",
            "reference",
        ),
        (
            lambda value: value["reference"].update({"content": "private"}),
            "invalid_reference",
            "reference",
        ),
        (
            lambda value: value["reference"].update({"scope": "missing"}),
            "invalid_reference",
            "reference.scope",
        ),
        (
            lambda value: value["reference"].update({"namespace_id": "Invalid"}),
            "invalid_reference",
            "reference.namespace_id",
        ),
        (
            lambda value: value.pop("expected_revision"),
            "invalid_expected_revision",
            "expected_revision",
        ),
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
    ],
)
def test_lifecycle_request_parser_rejects_broad_or_invalid_arguments(
    mutate,
    code: str,
    field: str,
) -> None:
    arguments = _arguments()
    mutate(arguments)

    with pytest.raises(MemoryValidationError) as caught:
        parse_lifecycle_request(arguments)

    assert caught.value.code == code
    assert caught.value.field == field


def test_memory_archive_direct_call_remains_disabled_without_registration() -> None:
    result = handle(_arguments())

    assert result["isError"] is True
    assert _payload(result) == {
        "status": "policy_error",
        "code": "mutation_disabled",
        "message": "memory archive is disabled",
    }


def test_memory_archive_returns_only_reference_and_lifecycle() -> None:
    observed = []

    def archive_operation(reference: MemoryReference, revision: int) -> MemoryResult:
        observed.append((reference, revision))
        return MemoryResult(status="archived", memory=_record())

    result = handle(
        _arguments(),
        mutations_enabled=True,
        archive_operation=archive_operation,
    )

    assert observed == [
        (
            MemoryReference(
                scope=MemoryScope.PROJECT,
                namespace_id="mnemosyne",
                collection_id="decisions",
                id=CANONICAL_ID,
            ),
            3,
        )
    ]
    assert _payload(result) == {
        "status": "archived",
        "reference": {
            "schema_version": 2,
            "scope": "project",
            "namespace_id": "mnemosyne",
            "collection_id": "decisions",
            "id": CANONICAL_ID,
        },
        "lifecycle": {"state": "archived", "revision": 4},
    }
    assert all(
        value not in result["content"][0]["text"]
        for value in ("Private title", "Archive lifecycle context", "private-tag")
    )


@pytest.mark.parametrize(
    ("error", "expected", "level", "outcome"),
    [
        (MutationDisabled(), {"status": "policy_error", "code": "mutation_disabled", "message": "memory archive is disabled"}, logging.WARNING, "policy_error"),
        (MemoryNotFound(), {"status": "not_found", "code": "not_found", "message": "memory to archive was not found"}, logging.WARNING, "not_found"),
        (RevisionConflict(), {"status": "conflict", "code": "revision_conflict", "message": "memory to archive is not at the expected revision"}, logging.WARNING, "conflict"),
        (WriteConflict(), {"status": "conflict", "code": "write_conflict", "message": "memory changed before it could be archived"}, logging.WARNING, "conflict"),
        (ReplacementOutcomeUncertain(), {"status": "uncertain", "code": "replacement_outcome_uncertain", "message": "memory archive outcome is uncertain; inspect the same reference before any retry"}, logging.WARNING, "uncertain"),
        (UnsafeMemoryPath("/private/path"), {"status": "storage_error", "code": "memory_source_unavailable", "message": "memory could not be archived"}, logging.WARNING, "storage_error"),
        (MemorySourceUnavailable("private source"), {"status": "storage_error", "code": "memory_source_unavailable", "message": "memory could not be archived"}, logging.WARNING, "storage_error"),
        (OSError("private os detail"), {"status": "storage_error", "code": "memory_source_unavailable", "message": "memory could not be archived"}, logging.WARNING, "storage_error"),
        (RuntimeError("private internal detail"), {"status": "internal_error", "code": "internal_error", "message": "memory could not be archived"}, logging.ERROR, "internal_error"),
    ],
)
def test_memory_archive_maps_failures_and_logs_one_bounded_event(
    error: Exception,
    expected: dict[str, str],
    level: int,
    outcome: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="mcp.memory_archive")

    def fail(reference: MemoryReference, revision: int) -> MemoryResult:
        raise error

    result = handle(_arguments(), mutations_enabled=True, archive_operation=fail)

    assert result["isError"] is True
    assert _payload(result) == expected
    records = [r for r in caplog.records if r.name == "mcp.memory_archive"]
    assert len(records) == 1
    assert records[0].levelno == level
    message = records[0].getMessage()
    assert f"event=memory_archive outcome={outcome}" in message
    assert "schema_version=2 scope=project" in message
    assert records[0].exc_info is None
    assert all(value not in message for value in (CANONICAL_ID, "mnemosyne", "decisions", "/private", "private internal"))


def test_memory_archive_invalid_and_disabled_calls_do_not_resolve_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        handler_module,
        "get_memory_root",
        lambda: pytest.fail("memory root was resolved"),
        raising=False,
    )

    assert _payload(handle({}))["code"] == "invalid_reference"
    assert _payload(handle(_arguments()))["code"] == "mutation_disabled"


def test_memory_archive_changes_one_file_and_excludes_recall_but_keeps_inspection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _record(state="active", revision=1, event=True)
    path = tmp_path / "project" / "mnemosyne" / "decisions" / f"{CANONICAL_ID}.json"
    path.parent.mkdir(parents=True)
    from mnemosyne.memory.records import serialize_memory_record
    path.write_text(json.dumps(serialize_memory_record(record)), encoding="utf-8")
    unrelated = tmp_path / "project" / "other.json"
    unrelated.write_text("unrelated", encoding="utf-8")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    result = handle({**_arguments(), "expected_revision": 1}, mutations_enabled=True)

    assert _payload(result)["status"] == "archived"
    assert len(list(tmp_path.rglob(f"{CANONICAL_ID}.json"))) == 1
    assert list(path.parent.glob(".*.tmp")) == []
    assert unrelated.read_text(encoding="utf-8") == "unrelated"
    from mnemosyne.mcp.tools.memory_recall import handle as recall
    from mnemosyne.mcp.tools.memory_inspect import handle as inspect
    assert _payload(recall({"query": "archive lifecycle context", "scope": "project"}))["status"] == "no_matches"
    inspected = _payload(inspect({"reference": _arguments()["reference"]}))
    assert inspected["memory"]["lifecycle"] == {"state": "archived", "revision": 2}
    assert inspected["memory"]["occurred_at"] == "2026-07-17T09:30:00Z"

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from mymcp.memory.errors import (
    DeletionOutcomeUncertain,
    MemoryNotArchived,
    MemoryNotFound,
    MemorySourceUnavailable,
    MemoryValidationError,
    MutationDisabled,
    RevisionConflict,
    UnsafeMemoryPath,
    WriteConflict,
)
from mymcp.memory.records import MemoryReference, parse_memory_record, serialize_memory_record
from mymcp.memory.scopes import MemoryScope, SCOPE_DEFINITIONS
from mymcp.memory.service import ForgetResult, MemoryService
from mymcp.memory.store import FilesystemMemoryStore
from mymcp.mcp.tools.memory_forget import TOOL, handle as public_handle
from mymcp.mcp.tools.memory_forget import handler as handler_module
from mymcp.mcp.tools.memory_forget.definition import TOOL as DEFINED_TOOL
from mymcp.mnemosyne.configuration import get_memory_root


CANONICAL_ID = "mem_0123456789abcdef0123456789abcdef"


def _forget_operation(reference: MemoryReference, revision: int) -> ForgetResult:
    return MemoryService(
        FilesystemMemoryStore(get_memory_root()),
        mutations_enabled=True,
    ).forget(reference, expected_revision=revision)


def handle(
    arguments,
    *,
    mutations_enabled=False,
    forget_operation=None,
):
    return public_handle(
        arguments,
        forget_operation=(
            _forget_operation if forget_operation is None else forget_operation
        ),
        mutations_enabled=mutations_enabled,
    )


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


def _reference() -> MemoryReference:
    return MemoryReference(
        scope=MemoryScope.PROJECT,
        namespace_id="mnemosyne",
        collection_id="decisions",
        id=CANONICAL_ID,
    )


def _payload(result: dict[str, Any]) -> dict[str, Any]:
    return json.loads(result["content"][0]["text"])


def test_memory_forget_exposes_a_strict_irreversible_definition() -> None:
    assert TOOL["name"] == "memory_forget"
    description = TOOL["description"].lower()
    assert "permanently" in description
    assert "archived" in description
    assert "canonical" in description
    assert "irreversible" in description

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
    assert reference["required"] == [
        "schema_version",
        "scope",
        "namespace_id",
        "collection_id",
        "id",
    ]
    assert reference["additionalProperties"] is False
    assert reference["properties"]["schema_version"] == {"const": 2}
    assert reference["properties"]["scope"]["oneOf"] == [
        {
            "const": definition.scope.value,
            "description": definition.description,
        }
        for definition in SCOPE_DEFINITIONS
    ]


def test_memory_forget_package_reexports_definition_and_handler() -> None:
    assert TOOL is DEFINED_TOOL
    assert public_handle is handler_module.handle


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
            lambda value: value["reference"].update({"content": "private"}),
            "invalid_reference",
            "reference",
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
            lambda value: value.update({"expected_revision": 1.0}),
            "invalid_expected_revision",
            "expected_revision",
        ),
    ],
)
def test_memory_forget_rejects_broad_or_invalid_arguments(
    mutate,
    code: str,
    field: str,
) -> None:
    arguments = _arguments()
    mutate(arguments)

    result = handle(arguments)

    assert result["isError"] is True
    payload = _payload(result)
    assert payload["status"] == "invalid_request"
    assert payload["code"] == code
    assert payload["field"] == field


def test_memory_forget_direct_call_remains_disabled_without_registration() -> None:
    result = handle(_arguments())

    assert result["isError"] is True
    assert _payload(result) == {
        "status": "policy_error",
        "code": "mutation_disabled",
        "message": "memory forget is disabled",
    }


def test_memory_forget_returns_only_status_and_same_reference() -> None:
    observed = []

    def forget_operation(reference: MemoryReference, revision: int) -> ForgetResult:
        observed.append((reference, revision))
        return ForgetResult(status="forgotten", reference=reference)

    result = handle(
        _arguments(),
        mutations_enabled=True,
        forget_operation=forget_operation,
    )

    assert observed == [(_reference(), 3)]
    assert _payload(result) == {
        "status": "forgotten",
        "reference": _arguments()["reference"],
    }
    assert "lifecycle" not in result["content"][0]["text"]


@pytest.mark.parametrize(
    "bad_result",
    [
        ForgetResult(status="already_forgotten", reference=_reference()),
        ForgetResult(
            status="forgotten",
            reference=MemoryReference(
                scope=MemoryScope.PROJECT,
                namespace_id="other",
                collection_id="decisions",
                id=CANONICAL_ID,
            ),
        ),
    ],
)
def test_memory_forget_rejects_inconsistent_operation_results(
    bad_result: ForgetResult,
) -> None:
    result = handle(
        _arguments(),
        mutations_enabled=True,
        forget_operation=lambda reference, revision: bad_result,
    )

    assert result["isError"] is True
    assert _payload(result) == {
        "status": "internal_error",
        "code": "internal_error",
        "message": "memory could not be forgotten",
    }


def test_memory_forget_invalid_and_disabled_calls_do_not_resolve_root(
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


@pytest.mark.parametrize(
    ("error", "expected", "level", "outcome"),
    [
        (
            MemoryValidationError("invalid_record", "expected_revision", "private"),
            {
                "status": "invalid_request",
                "code": "invalid_expected_revision",
                "field": "expected_revision",
                "message": "expected revision is invalid",
            },
            logging.WARNING,
            "invalid_request",
        ),
        (
            MutationDisabled(),
            {
                "status": "policy_error",
                "code": "mutation_disabled",
                "message": "memory forget is disabled",
            },
            logging.WARNING,
            "policy_error",
        ),
        (
            MemoryNotArchived(),
            {
                "status": "conflict",
                "code": "not_archived",
                "message": "memory must be archived before it can be forgotten",
            },
            logging.WARNING,
            "conflict",
        ),
        (
            MemoryNotFound(),
            {
                "status": "not_found",
                "code": "not_found",
                "message": "memory to forget was not found",
            },
            logging.WARNING,
            "not_found",
        ),
        (
            RevisionConflict(),
            {
                "status": "conflict",
                "code": "revision_conflict",
                "message": "memory to forget is not at the expected revision",
            },
            logging.WARNING,
            "conflict",
        ),
        (
            WriteConflict(),
            {
                "status": "conflict",
                "code": "write_conflict",
                "message": "memory changed before it could be forgotten",
            },
            logging.WARNING,
            "conflict",
        ),
        (
            UnsafeMemoryPath("/private/path"),
            {
                "status": "storage_error",
                "code": "memory_source_unavailable",
                "message": "memory could not be forgotten",
            },
            logging.WARNING,
            "storage_error",
        ),
        (
            MemorySourceUnavailable("private source"),
            {
                "status": "storage_error",
                "code": "memory_source_unavailable",
                "message": "memory could not be forgotten",
            },
            logging.WARNING,
            "storage_error",
        ),
        (
            OSError("private os detail"),
            {
                "status": "storage_error",
                "code": "memory_source_unavailable",
                "message": "memory could not be forgotten",
            },
            logging.WARNING,
            "storage_error",
        ),
        (
            DeletionOutcomeUncertain("private sync detail"),
            {
                "status": "uncertain",
                "code": "deletion_outcome_uncertain",
                "message": (
                    "memory deletion outcome is uncertain; inspect the same "
                    "reference before any retry"
                ),
            },
            logging.WARNING,
            "uncertain",
        ),
        (
            RuntimeError("private internal detail"),
            {
                "status": "internal_error",
                "code": "internal_error",
                "message": "memory could not be forgotten",
            },
            logging.ERROR,
            "internal_error",
        ),
    ],
)
def test_memory_forget_maps_failures_and_logs_one_bounded_event(
    error: Exception,
    expected: dict[str, str],
    level: int,
    outcome: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="mcp.memory_forget")

    def fail(reference: MemoryReference, revision: int) -> ForgetResult:
        raise error

    result = handle(_arguments(), mutations_enabled=True, forget_operation=fail)

    assert result["isError"] is True
    assert _payload(result) == expected
    records = [record for record in caplog.records if record.name == "mcp.memory_forget"]
    assert len(records) == 1
    assert records[0].levelno == level
    message = records[0].getMessage()
    assert f"event=memory_forget outcome={outcome}" in message
    assert "schema_version=2 scope=project" in message
    assert records[0].exc_info is None
    assert all(
        value not in message
        for value in (
            CANONICAL_ID,
            "mnemosyne",
            "decisions",
            "/private",
            "private internal",
            "private sync",
        )
    )


def test_memory_forget_success_logs_only_bounded_metadata(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="mcp.memory_forget")

    result = handle(
        _arguments(),
        mutations_enabled=True,
        forget_operation=lambda reference, revision: ForgetResult(
            status="forgotten",
            reference=reference,
        ),
    )

    assert _payload(result)["status"] == "forgotten"
    records = [record for record in caplog.records if record.name == "mcp.memory_forget"]
    assert len(records) == 1
    assert records[0].levelno == logging.INFO
    assert records[0].getMessage() == (
        "event=memory_forget outcome=forgotten schema_version=2 scope=project"
    )


def _record(*, state: str, revision: int):
    return parse_memory_record(
        {
            "schema_version": 2,
            "id": CANONICAL_ID,
            "scope": "project",
            "namespace": {"kind": "project", "id": "mnemosyne", "label": "Private"},
            "collection": {"id": "decisions", "label": "Private"},
            "kind": "decision",
            "language": "en",
            "title": "Private title",
            "content": "Forget integration context.",
            "tags": ["private-tag"],
            "provenance": {
                "origin": "explicit_user_statement",
                "recorded_via": "memory_remember",
            },
            "lifecycle": {"state": state, "revision": revision},
            "created_at": "2026-07-18T12:00:00Z",
            "updated_at": "2026-07-19T12:00:00Z",
        }
    )


def test_memory_forget_deletes_one_archived_record_and_all_read_paths_report_absence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "project" / "mnemosyne" / "decisions" / f"{CANONICAL_ID}.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(serialize_memory_record(_record(state="archived", revision=2))),
        encoding="utf-8",
    )
    unrelated = path.parent / "unrelated.txt"
    unrelated.write_text("unrelated", encoding="utf-8")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    arguments = {**_arguments(), "expected_revision": 2}

    result = handle(arguments, mutations_enabled=True)

    assert _payload(result) == {
        "status": "forgotten",
        "reference": arguments["reference"],
    }
    assert not path.exists()
    assert path.parent.is_dir()
    assert unrelated.read_text(encoding="utf-8") == "unrelated"
    assert sorted(item.name for item in path.parent.iterdir()) == ["unrelated.txt"]

    from mymcp.mcp.tools.memory_inspect import handle as inspect
    from mymcp.mcp.tools.memory_recall import handle as recall
    from mymcp.mcp.tools.memory_restore import handle as restore

    read_service = MemoryService(FilesystemMemoryStore(tmp_path))
    mutation_service = MemoryService(
        FilesystemMemoryStore(tmp_path),
        mutations_enabled=True,
    )
    assert _payload(
        inspect(
            {"reference": arguments["reference"]},
            inspect_operation=read_service.inspect,
        )
    )["code"] == "not_found"
    assert _payload(
        recall(
            {"query": "forget integration context", "scope": "project"},
            recall_operation=read_service.recall,
        )
    ) == {
        "status": "no_matches",
        "memories": [],
    }
    assert _payload(
        restore(
            arguments,
            restore_operation=lambda reference, revision: mutation_service.restore(
                reference,
                expected_revision=revision,
            ),
            mutations_enabled=True,
        )
    )["code"] == "not_found"
    assert _payload(handle(arguments, mutations_enabled=True))["code"] == "not_found"


def test_memory_forget_active_and_stale_requests_leave_record_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "project" / "mnemosyne" / "decisions" / f"{CANONICAL_ID}.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(serialize_memory_record(_record(state="active", revision=2))),
        encoding="utf-8",
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    before = (path.read_bytes(), path.stat().st_mtime_ns)

    stale = handle({**_arguments(), "expected_revision": 1}, mutations_enabled=True)
    active = handle({**_arguments(), "expected_revision": 2}, mutations_enabled=True)

    assert _payload(stale)["code"] == "revision_conflict"
    assert _payload(active)["code"] == "not_archived"
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before

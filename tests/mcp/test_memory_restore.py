import json
import logging
from pathlib import Path
from typing import Any

import pytest

from mnemosyne.mcp.tools._memory_lifecycle import parse_lifecycle_request
from mnemosyne.mcp.tools.memory_restore import TOOL, handle
from mnemosyne.mcp.tools.memory_restore import handler as handler_module
from mnemosyne.mcp.tools.memory_restore.definition import TOOL as DEFINED_TOOL
from mnemosyne.memory.errors import ReplacementOutcomeUncertain
from mnemosyne.memory.records import MemoryReference, parse_memory_record, serialize_memory_record
from mnemosyne.memory.scopes import MemoryScope
from mnemosyne.memory.service import MemoryResult


CANONICAL_ID = "mem_fedcba9876543210fedcba9876543210"


def _arguments() -> dict[str, object]:
    return {
        "reference": {
            "schema_version": 2,
            "scope": "project",
            "namespace_id": "mnemosyne",
            "collection_id": None,
            "id": CANONICAL_ID,
        },
        "expected_revision": 2,
    }


def _payload(result: dict[str, Any]) -> dict[str, Any]:
    return json.loads(result["content"][0]["text"])


def _record(*, state: str = "active", revision: int = 3, event: bool = False):
    payload = {
        "schema_version": 2,
        "id": CANONICAL_ID,
        "scope": "project",
        "namespace": {"kind": "project", "id": "mnemosyne", "label": None},
        "collection": None,
        "kind": "event" if event else "state",
        "language": "en",
        "title": None,
        "content": "Restore lifecycle context.",
        "tags": [],
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


def test_memory_restore_uses_the_same_strict_request_contract() -> None:
    assert TOOL["name"] == "memory_restore"
    assert "restore" in TOOL["description"].lower()
    assert "canonical" in TOOL["description"].lower()
    assert TOOL["inputSchema"] == {
        **TOOL["inputSchema"],
        "required": ["reference", "expected_revision"],
        "additionalProperties": False,
    }
    assert set(TOOL["inputSchema"]["properties"]) == {
        "reference",
        "expected_revision",
    }
    assert TOOL["inputSchema"]["properties"]["reference"]["properties"][
        "schema_version"
    ] == {"const": 2}


def test_memory_restore_package_reexports_definition_and_handler() -> None:
    assert TOOL is DEFINED_TOOL
    assert handle is handler_module.handle


def test_restore_request_adapts_a_nullable_collection_reference() -> None:
    request = parse_lifecycle_request(_arguments())

    assert request.reference == MemoryReference(
        scope=MemoryScope.PROJECT,
        namespace_id="mnemosyne",
        collection_id=None,
        id=CANONICAL_ID,
    )
    assert request.expected_revision == 2


def test_memory_restore_direct_call_remains_disabled_without_registration() -> None:
    result = handle(_arguments())

    assert result["isError"] is True
    assert _payload(result) == {
        "status": "policy_error",
        "code": "mutation_disabled",
        "message": "memory restore is disabled",
    }


def test_memory_restore_returns_minimal_changed_and_idempotent_projections() -> None:
    for status in ("restored", "already_active"):
        revision = 3 if status == "restored" else 2
        result = handle(
            _arguments(),
            mutations_enabled=True,
            restore_operation=lambda reference, expected_revision, result_revision=revision: MemoryResult(
                status=status,
                memory=_record(revision=result_revision),
            ),
        )
        assert _payload(result) == {
            "status": status,
            "reference": {
                "schema_version": 2,
                "scope": "project",
                "namespace_id": "mnemosyne",
                "collection_id": None,
                "id": CANONICAL_ID,
            },
            "lifecycle": {"state": "active", "revision": revision},
        }


def test_memory_restore_maps_uncertain_replacement_without_private_details(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="mcp.memory_restore")

    def fail(reference: MemoryReference, revision: int) -> MemoryResult:
        raise ReplacementOutcomeUncertain("private storage detail")

    result = handle(
        _arguments(),
        mutations_enabled=True,
        restore_operation=fail,
    )

    assert _payload(result) == {
        "status": "uncertain",
        "code": "replacement_outcome_uncertain",
        "message": (
            "memory restore outcome is uncertain; inspect the same reference "
            "before any retry"
        ),
    }
    records = [record for record in caplog.records if record.name == "mcp.memory_restore"]
    assert len(records) == 1
    assert records[0].levelno == logging.WARNING
    assert "outcome=uncertain code=replacement_outcome_uncertain" in records[0].getMessage()
    assert "private storage detail" not in records[0].getMessage()
    assert records[0].exc_info is None


def test_memory_restore_returns_archived_memory_to_recall_and_inspection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _record(state="archived", revision=2, event=True)
    path = tmp_path / "project" / "mnemosyne" / f"{CANONICAL_ID}.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(serialize_memory_record(record)), encoding="utf-8")
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    result = handle(_arguments(), mutations_enabled=True)

    assert _payload(result)["status"] == "restored"
    from mnemosyne.mcp.tools.memory_recall import handle as recall
    from mnemosyne.mcp.tools.memory_inspect import handle as inspect
    recalled = _payload(recall({"query": "restore lifecycle context", "scope": "project"}))
    assert recalled["status"] == "ok"
    inspected = _payload(inspect({"reference": _arguments()["reference"]}))
    assert inspected["memory"]["lifecycle"] == {"state": "active", "revision": 3}
    assert inspected["memory"]["occurred_at"] == "2026-07-17T09:30:00Z"

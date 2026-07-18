import json
import logging
import stat
from pathlib import Path
from typing import Any

import pytest

from mnemosyne.mcp.tools.memory_inspect import TOOL, handle
from mnemosyne.mcp.tools.memory_inspect import handler as handler_module
from mnemosyne.mcp.tools.memory_inspect.definition import TOOL as DEFINED_TOOL
from mnemosyne.memory.errors import (
    AmbiguousMemoryReference,
    CandidateLimitExceeded,
    MemoryNotFound,
    MemorySourceUnavailable,
    UnsafeMemoryPath,
)
from mnemosyne.memory.records import (
    LegacyMemoryRecordV1,
    LegacyMemoryReference,
    MemoryReference,
)
from mnemosyne.memory.scopes import MemoryScope, SCOPE_DEFINITIONS


CANONICAL_ID = "mem_0123456789abcdef0123456789abcdef"
ARCHIVED_ID = "mem_fedcba9876543210fedcba9876543210"


def _write_memory(path: Path, record: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record), encoding="utf-8")


def _v2(
    memory_id: str = CANONICAL_ID,
    *,
    namespace_id: str = "mnemosyne",
    state: str = "active",
    revision: int = 1,
) -> dict[str, object]:
    return {
        "schema_version": 2,
        "id": memory_id,
        "scope": "project",
        "namespace": {
            "kind": "project",
            "id": namespace_id,
            "label": "Private project label",
        },
        "collection": {"id": "decisions", "label": "Private collection label"},
        "kind": "decision",
        "language": "en",
        "title": "Private inspection title",
        "content": "Private inspection content.",
        "tags": ["private-inspection-tag"],
        "provenance": {
            "origin": "explicit_user_statement",
            "recorded_via": "memory_remember",
        },
        "lifecycle": {"state": state, "revision": revision},
        "created_at": "2026-07-18T12:00:00Z",
        "updated_at": "2026-07-18T13:00:00Z",
    }


def _canonical_arguments(
    memory_id: str = CANONICAL_ID,
    *,
    namespace_id: str = "mnemosyne",
) -> dict[str, object]:
    return {
        "reference": {
            "schema_version": 2,
            "scope": "project",
            "namespace_id": namespace_id,
            "collection_id": "decisions",
            "id": memory_id,
        }
    }


def _legacy_arguments(memory_id: str = "rainy-weekend") -> dict[str, object]:
    return {
        "reference": {
            "schema_version": 1,
            "scope": "preference",
            "id": memory_id,
        }
    }


def _payload(result: dict[str, Any]) -> dict[str, Any]:
    return json.loads(result["content"][0]["text"])


def _snapshot(root: Path) -> dict[str, tuple[bytes, int, int]]:
    return {
        path.relative_to(root).as_posix(): (
            path.read_bytes(),
            stat.S_IMODE(path.stat().st_mode),
            path.stat().st_mtime_ns,
        )
        for path in sorted(root.rglob("*.json"))
    }


def test_memory_inspect_exposes_a_strict_versioned_reference_definition() -> None:
    assert TOOL["name"] == "memory_inspect"
    assert "read-only" in TOOL["description"]
    assert "one exact" in TOOL["description"]

    schema = TOOL["inputSchema"]
    assert schema["type"] == "object"
    assert schema["required"] == ["reference"]
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {"reference"}

    branches = schema["properties"]["reference"]["oneOf"]
    assert len(branches) == 2
    canonical, legacy = branches

    assert canonical["type"] == "object"
    assert canonical["required"] == [
        "schema_version",
        "scope",
        "namespace_id",
        "collection_id",
        "id",
    ]
    assert canonical["additionalProperties"] is False
    assert set(canonical["properties"]) == set(canonical["required"])
    assert canonical["properties"]["schema_version"] == {"const": 2}
    assert canonical["properties"]["id"] == {
        "type": "string",
        "pattern": "^mem_[0-9a-f]{32}$",
    }
    assert canonical["properties"]["collection_id"]["oneOf"][1] == {
        "type": "null"
    }

    assert legacy["type"] == "object"
    assert legacy["required"] == ["schema_version", "scope", "id"]
    assert legacy["additionalProperties"] is False
    assert set(legacy["properties"]) == set(legacy["required"])
    assert legacy["properties"]["schema_version"] == {"const": 1}
    assert legacy["properties"]["id"] == {
        "type": "string",
        "pattern": "^[A-Za-z0-9._-]{1,100}$",
    }

    expected_scopes = [
        {
            "const": definition.scope.value,
            "description": definition.description,
        }
        for definition in SCOPE_DEFINITIONS
    ]
    assert canonical["properties"]["scope"]["oneOf"] == expected_scopes
    assert legacy["properties"]["scope"]["oneOf"] == expected_scopes


def test_memory_inspect_package_reexports_definition_and_handler() -> None:
    assert TOOL is DEFINED_TOOL
    assert handle is handler_module.handle


def test_memory_inspect_handler_adapts_a_canonical_reference() -> None:
    observed: list[MemoryReference | LegacyMemoryReference] = []

    def inspect_operation(
        reference: MemoryReference | LegacyMemoryReference,
    ) -> LegacyMemoryRecordV1:
        observed.append(reference)
        raise MemoryNotFound

    result = handle(
        {
            "reference": {
                "schema_version": 2,
                "scope": "project",
                "namespace_id": "mnemosyne",
                "collection_id": None,
                "id": CANONICAL_ID,
            }
        },
        inspect_operation=inspect_operation,
    )

    assert observed == [
        MemoryReference(
            scope=MemoryScope.PROJECT,
            namespace_id="mnemosyne",
            collection_id=None,
            id=CANONICAL_ID,
        )
    ]
    assert _payload(result) == {
        "status": "not_found",
        "code": "not_found",
        "message": "memory was not found",
    }


def test_memory_inspect_handler_adapts_a_legacy_reference() -> None:
    observed: list[MemoryReference | LegacyMemoryReference] = []

    def inspect_operation(
        reference: MemoryReference | LegacyMemoryReference,
    ) -> LegacyMemoryRecordV1:
        observed.append(reference)
        raise MemoryNotFound

    result = handle(
        {
            "reference": {
                "schema_version": 1,
                "scope": "preference",
                "id": "rainy-weekend",
            }
        },
        inspect_operation=inspect_operation,
    )

    assert observed == [
        LegacyMemoryReference(
            scope=MemoryScope.PREFERENCE,
            id="rainy-weekend",
        )
    ]
    assert _payload(result) == {
        "status": "not_found",
        "code": "not_found",
        "message": "memory was not found",
    }


@pytest.mark.parametrize(
    ("arguments", "field"),
    [
        ({}, "reference"),
        ({"reference": {}, "extra": True}, "reference"),
        ({"reference": "project"}, "reference"),
        (
            {"reference": {"schema_version": 3, "scope": "project", "id": "x"}},
            "reference",
        ),
        (
            {
                "reference": {
                    "schema_version": 1,
                    "scope": "missing",
                    "id": "legacy",
                }
            },
            "reference.scope",
        ),
        (
            {
                "reference": {
                    "schema_version": 1,
                    "scope": "project",
                    "id": "legacy",
                    "path": "project/legacy.json",
                }
            },
            "reference",
        ),
        (
            {
                "reference": {
                    "schema_version": 2,
                    "scope": "project",
                    "namespace_id": "Invalid",
                    "collection_id": None,
                    "id": CANONICAL_ID,
                }
            },
            "reference.namespace_id",
        ),
        (
            {
                "reference": {
                    "schema_version": 2,
                    "scope": "project",
                    "namespace_id": "mnemosyne",
                    "collection_id": "Invalid",
                    "id": CANONICAL_ID,
                }
            },
            "reference.collection_id",
        ),
        (
            {
                "reference": {
                    "schema_version": 2,
                    "scope": "project",
                    "namespace_id": "mnemosyne",
                    "collection_id": None,
                }
            },
            "reference",
        ),
    ],
)
def test_memory_inspect_maps_invalid_references_to_bounded_tool_errors(
    arguments: dict[str, object],
    field: str,
) -> None:
    result = handle(
        arguments,
        inspect_operation=lambda reference: LegacyMemoryRecordV1(
            id="unused",
            title=None,
            content="Unused",
            tags=(),
        ),
    )

    assert result["isError"] is True
    assert _payload(result) == {
        "status": "invalid_request",
        "code": "invalid_reference",
        "field": field,
        "message": "reference is invalid",
    }


@pytest.mark.parametrize("state", ["active", "archived"])
def test_memory_inspect_returns_complete_canonical_memory(
    state: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory_id = CANONICAL_ID if state == "active" else ARCHIVED_ID
    namespace_id = "mnemosyne" if state == "active" else "archived-project"
    revision = 1 if state == "active" else 3
    record = _v2(
        memory_id,
        namespace_id=namespace_id,
        state=state,
        revision=revision,
    )
    _write_memory(
        tmp_path / "project" / namespace_id / "decisions" / f"{memory_id}.json",
        record,
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    result = handle(_canonical_arguments(memory_id, namespace_id=namespace_id))

    assert "isError" not in result
    assert _payload(result) == {
        "status": "ok",
        "memory": {
            "reference": {
                "schema_version": 2,
                "scope": "project",
                "namespace_id": namespace_id,
                "collection_id": "decisions",
                "id": memory_id,
            },
            **record,
        },
    }
    serialized = result["content"][0]["text"]
    assert "path" not in serialized
    assert "fingerprint" not in serialized
    assert "score" not in serialized


def test_memory_inspect_returns_a_stable_legacy_projection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_memory(
        tmp_path / "preference" / "legacy" / "rainy.json",
        {
            "schema_version": 1,
            "id": "rainy-weekend",
            "content": "Museums on rainy weekends.",
        },
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    result = handle(_legacy_arguments())

    assert _payload(result) == {
        "status": "ok",
        "memory": {
            "reference": {
                "schema_version": 1,
                "scope": "preference",
                "id": "rainy-weekend",
            },
            "schema_version": 1,
            "id": "rainy-weekend",
            "title": None,
            "content": "Museums on rainy weekends.",
            "tags": [],
        },
    }


@pytest.mark.parametrize(
    ("error", "expected", "level", "outcome"),
    [
        (
            MemoryNotFound(),
            {"status": "not_found", "code": "not_found", "message": "memory was not found"},
            logging.INFO,
            "not_found",
        ),
        (
            AmbiguousMemoryReference(),
            {
                "status": "conflict",
                "code": "ambiguous_reference",
                "message": "legacy memory reference is ambiguous",
            },
            logging.WARNING,
            "conflict",
        ),
        (
            CandidateLimitExceeded(),
            {
                "status": "storage_error",
                "code": "candidate_limit_exceeded",
                "message": "memory scope contains more than 1000 candidate files",
            },
            logging.WARNING,
            "storage_error",
        ),
        (
            UnsafeMemoryPath("/private/unsafe"),
            {
                "status": "storage_error",
                "code": "memory_source_unavailable",
                "message": "memory could not be inspected",
            },
            logging.WARNING,
            "storage_error",
        ),
        (
            MemorySourceUnavailable("/private/unavailable"),
            {
                "status": "storage_error",
                "code": "memory_source_unavailable",
                "message": "memory could not be inspected",
            },
            logging.WARNING,
            "storage_error",
        ),
        (
            OSError("/private/os-error"),
            {
                "status": "storage_error",
                "code": "memory_source_unavailable",
                "message": "memory could not be inspected",
            },
            logging.WARNING,
            "storage_error",
        ),
        (
            RuntimeError("private-internal-detail"),
            {
                "status": "internal_error",
                "code": "internal_error",
                "message": "memory could not be inspected",
            },
            logging.ERROR,
            "internal_error",
        ),
    ],
)
def test_memory_inspect_maps_failures_and_logs_one_bounded_terminal_event(
    error: Exception,
    expected: dict[str, str],
    level: int,
    outcome: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def inspect_operation(
        reference: MemoryReference | LegacyMemoryReference,
    ) -> LegacyMemoryRecordV1:
        raise error

    caplog.set_level(logging.INFO, logger="mcp.memory_inspect")

    result = handle(_legacy_arguments(), inspect_operation=inspect_operation)

    assert result["isError"] is True
    assert _payload(result) == expected
    records = [
        record for record in caplog.records if record.name == "mcp.memory_inspect"
    ]
    assert len(records) == 1
    assert records[0].levelno == level
    assert f"event=memory_inspect outcome={outcome}" in records[0].getMessage()
    assert "schema_version=1 scope=preference" in records[0].getMessage()
    assert records[0].exc_info is None
    assert "rainy-weekend" not in records[0].getMessage()
    assert "/private" not in records[0].getMessage()
    assert "private-internal-detail" not in records[0].getMessage()


def test_memory_inspect_validation_precedes_memory_root_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called() -> Path:
        raise AssertionError("memory root was resolved")

    monkeypatch.setattr(handler_module, "get_memory_root", fail_if_called, raising=False)

    result = handle({})

    assert _payload(result)["code"] == "invalid_reference"


def test_memory_inspect_missing_root_does_not_initialize_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "application" / "memory"
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(root))

    result = handle(_legacy_arguments())

    assert _payload(result)["code"] == "not_found"
    assert not (tmp_path / "application").exists()


def test_memory_inspect_preserves_canonical_and_legacy_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_memory(
        tmp_path / "project" / "mnemosyne" / "decisions" / f"{CANONICAL_ID}.json",
        _v2(),
    )
    _write_memory(
        tmp_path
        / "project"
        / "archived-project"
        / "decisions"
        / f"{ARCHIVED_ID}.json",
        _v2(ARCHIVED_ID, namespace_id="archived-project", state="archived", revision=2),
    )
    _write_memory(
        tmp_path / "preference" / "legacy" / "rainy.json",
        {"schema_version": 1, "id": "rainy-weekend", "content": "Legacy"},
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    before = _snapshot(tmp_path)

    assert _payload(handle(_canonical_arguments()))["status"] == "ok"
    assert _payload(
        handle(_canonical_arguments(ARCHIVED_ID, namespace_id="archived-project"))
    )["status"] == "ok"
    assert _payload(handle(_legacy_arguments()))["status"] == "ok"

    assert _snapshot(tmp_path) == before


def test_memory_inspect_ambiguous_legacy_failure_preserves_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_memory(
        tmp_path / "preference" / "one" / "rainy.json",
        {"schema_version": 1, "id": "rainy-weekend", "content": "First"},
    )
    _write_memory(
        tmp_path / "preference" / "two" / "rainy.json",
        {"schema_version": 1, "id": "rainy-weekend", "content": "Second"},
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    before = _snapshot(tmp_path)

    result = handle(_legacy_arguments())

    assert _payload(result)["code"] == "ambiguous_reference"
    assert _snapshot(tmp_path) == before


def test_memory_inspect_legacy_discovery_warnings_contain_no_candidate_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    invalid_path = tmp_path / "preference" / "private-invalid-name.json"
    _write_memory(invalid_path, {"schema_version": 1})
    _write_memory(
        tmp_path / "preference" / "legacy" / "rainy.json",
        {"schema_version": 1, "id": "rainy-weekend", "content": "Legacy"},
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    caplog.set_level(logging.INFO)

    assert _payload(handle(_legacy_arguments()))["status"] == "ok"

    store_messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "mnemosyne.memory.store"
    ]
    inspect_messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "mcp.memory_inspect"
    ]
    assert store_messages == ["skipped scope='preference' reason='invalid_record'"]
    assert len(inspect_messages) == 1
    combined = " ".join(store_messages + inspect_messages)
    assert "private-invalid-name.json" not in combined
    assert str(tmp_path) not in combined


def test_memory_inspect_record_version_mismatch_is_an_internal_error() -> None:
    result = handle(
        _canonical_arguments(),
        inspect_operation=lambda reference: LegacyMemoryRecordV1(
            id="legacy",
            title=None,
            content="Legacy",
            tags=(),
        ),
    )

    assert _payload(result) == {
        "status": "internal_error",
        "code": "internal_error",
        "message": "memory could not be inspected",
    }


def test_memory_inspect_logs_one_bounded_invalid_event(
    caplog: pytest.LogCaptureFixture,
) -> None:
    private_value = "private-invalid-reference"
    caplog.set_level(logging.INFO, logger="mcp.memory_inspect")

    result = handle(
        {
            "reference": {
                "schema_version": 1,
                "scope": "preference",
                "id": private_value,
                "unknown": True,
            }
        }
    )

    assert _payload(result)["code"] == "invalid_reference"
    records = [
        record for record in caplog.records if record.name == "mcp.memory_inspect"
    ]
    assert len(records) == 1
    assert records[0].levelno == logging.WARNING
    assert records[0].getMessage() == (
        "event=memory_inspect outcome=invalid_request "
        "code=invalid_reference field=reference"
    )
    assert private_value not in records[0].getMessage()


def test_memory_inspect_logs_one_content_free_success_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    path = (
        tmp_path / "project" / "mnemosyne" / "decisions" / f"{CANONICAL_ID}.json"
    )
    _write_memory(path, _v2())
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    caplog.set_level(logging.INFO, logger="mcp.memory_inspect")

    assert _payload(handle(_canonical_arguments()))["status"] == "ok"

    records = [
        record for record in caplog.records if record.name == "mcp.memory_inspect"
    ]
    assert len(records) == 1
    assert records[0].getMessage() == (
        "event=memory_inspect outcome=ok schema_version=2 scope=project"
    )
    forbidden = [
        CANONICAL_ID,
        "mnemosyne",
        "decisions",
        "Private project label",
        "Private inspection title",
        "Private inspection content",
        "private-inspection-tag",
        str(tmp_path),
    ]
    assert all(value not in records[0].getMessage() for value in forbidden)

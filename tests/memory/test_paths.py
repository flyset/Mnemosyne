from pathlib import Path

import pytest

from mymcp.memory.errors import UnsafeMemoryPath
from mymcp.memory.paths import (
    ensure_record_path,
    relative_path_for_record,
    relative_path_for_reference,
    scope_directory,
)
from mymcp.memory.records import MemoryRecordV2, MemoryReference, parse_memory_record
from mymcp.memory.scopes import MemoryScope


def _record(*, collection: bool = True) -> MemoryRecordV2:
    record = parse_memory_record(
        {
            "schema_version": 2,
            "id": "mem_0123456789abcdef0123456789abcdef",
            "scope": "project",
            "namespace": {
                "kind": "project",
                "id": "mnemosyne",
                "label": "Mnemosyne",
            },
            "collection": (
                {"id": "decisions", "label": "Decisions"}
                if collection
                else None
            ),
            "kind": "decision",
            "language": "en",
            "title": "Shared ownership",
            "content": "Memory belongs to the shared domain.",
            "tags": ["architecture"],
            "provenance": {
                "origin": "explicit_user_statement",
                "recorded_via": "memory_remember",
            },
            "lifecycle": {"state": "active", "revision": 1},
            "created_at": "2026-07-18T12:00:00Z",
            "updated_at": "2026-07-18T12:00:00Z",
        }
    )
    assert isinstance(record, MemoryRecordV2)
    return record


def test_scope_directory_uses_the_canonical_fixed_mapping(tmp_path: Path) -> None:
    assert scope_directory(tmp_path, MemoryScope.PREFERENCE) == (
        tmp_path / "preference"
    )


def test_version_two_reference_and_record_paths_are_deterministic() -> None:
    record = _record()
    reference = MemoryReference(
        scope=record.scope,
        namespace_id=record.namespace.id,
        collection_id=record.collection.id if record.collection else None,
        id=record.id,
    )

    assert relative_path_for_reference(reference) == Path(
        "project/mnemosyne/decisions/mem_0123456789abcdef0123456789abcdef.json"
    )
    assert relative_path_for_record(record) == relative_path_for_reference(reference)


def test_version_two_path_omits_absent_collection() -> None:
    record = _record(collection=False)

    assert relative_path_for_record(record) == Path(
        "project/mnemosyne/mem_0123456789abcdef0123456789abcdef.json"
    )


def test_record_path_agreement_accepts_only_the_derived_location() -> None:
    record = _record()
    expected = relative_path_for_record(record)

    ensure_record_path(record, expected)

    for mismatched in [
        Path("self/mnemosyne/decisions") / expected.name,
        Path("project/other/decisions") / expected.name,
        Path("project/mnemosyne/other") / expected.name,
        expected.with_name("mem_ffffffffffffffffffffffffffffffff.json"),
    ]:
        with pytest.raises(UnsafeMemoryPath):
            ensure_record_path(record, mismatched)


@pytest.mark.parametrize(
    "path",
    [
        Path("../project/memory.json"),
        Path("project/../../memory.json"),
        Path("/tmp/memory.json"),
    ],
)
def test_record_path_agreement_rejects_unsafe_paths(path: Path) -> None:
    with pytest.raises(UnsafeMemoryPath):
        ensure_record_path(_record(), path)

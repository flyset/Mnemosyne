import json
import os
import stat
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mnemosyne.memory.errors import (
    MemorySourceUnavailable,
    MemoryValidationError,
    RevisionConflict,
    UnsafeMemoryPath,
    WriteConflict,
)
from mnemosyne.memory.records import (
    LegacyMemoryReference,
    LifecycleState,
    MemoryLifecycle,
    MemoryRecordV2,
    MemoryReference,
    parse_memory_record,
)
from mnemosyne.memory.scopes import MemoryScope
from mnemosyne.memory.store import FilesystemMemoryStore


MEMORY_ID = "mem_0123456789abcdef0123456789abcdef"


def _payload(*, content: str = "Original content", revision: int = 1) -> dict[str, object]:
    return {
        "schema_version": 2,
        "id": MEMORY_ID,
        "scope": "project",
        "namespace": {
            "kind": "project",
            "id": "mnemosyne",
            "label": "Mnemosyne",
        },
        "collection": {"id": "decisions", "label": "Decisions"},
        "kind": "decision",
        "language": "en",
        "title": "Shared ownership",
        "content": content,
        "tags": ["architecture"],
        "provenance": {
            "origin": "explicit_user_statement",
            "recorded_via": "memory_remember",
        },
        "lifecycle": {"state": "active", "revision": revision},
        "created_at": "2026-07-18T12:00:00Z",
        "updated_at": f"2026-07-18T12:00:0{revision - 1}Z",
    }


def _record(*, content: str = "Original content", revision: int = 1) -> MemoryRecordV2:
    record = parse_memory_record(_payload(content=content, revision=revision))
    assert isinstance(record, MemoryRecordV2)
    return record


def _reference() -> MemoryReference:
    return MemoryReference(
        scope=MemoryScope.PROJECT,
        namespace_id="mnemosyne",
        collection_id="decisions",
        id=MEMORY_ID,
    )


def test_store_atomically_creates_private_directories_and_file(tmp_path: Path) -> None:
    root = tmp_path / "memory"
    store = FilesystemMemoryStore(root)

    stored = store.create(_record())

    path = root / stored.relative_path
    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8")) == _payload()
    assert list(path.parent.glob(".*.tmp")) == []
    if os.name == "posix":
        assert stat.S_IMODE(root.stat().st_mode) == 0o700
        assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_store_create_never_overwrites_an_existing_record(tmp_path: Path) -> None:
    store = FilesystemMemoryStore(tmp_path)
    store.create(_record())

    with pytest.raises(WriteConflict):
        store.create(_record(content="Replacement attempt"))

    assert store.get(_reference()).record.content == "Original content"


def test_store_create_revalidates_direct_record_instances(tmp_path: Path) -> None:
    invalid = replace(_record(), language="not valid")

    with pytest.raises(MemoryValidationError):
        FilesystemMemoryStore(tmp_path).create(invalid)

    assert list(tmp_path.rglob("*.json")) == []


def test_store_create_rejects_a_symlinked_parent(tmp_path: Path) -> None:
    root = tmp_path / "memory"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (root / "project").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")

    with pytest.raises(UnsafeMemoryPath):
        FilesystemMemoryStore(root).create(_record())

    assert list(outside.rglob("*.json")) == []


def test_store_create_cleans_temporary_file_when_sync_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_sync(descriptor: int) -> None:
        raise OSError("sync failed")

    monkeypatch.setattr(os, "fsync", fail_sync)

    with pytest.raises(MemorySourceUnavailable):
        FilesystemMemoryStore(tmp_path).create(_record())

    assert list(tmp_path.rglob("*.tmp")) == []
    assert list(tmp_path.rglob("*.json")) == []


def test_store_atomically_replaces_after_expected_revision(tmp_path: Path) -> None:
    store = FilesystemMemoryStore(tmp_path)
    original = _record()
    store.create(original)
    revised = replace(
        original,
        content="Revised content",
        lifecycle=MemoryLifecycle(state=LifecycleState.ACTIVE, revision=2),
        updated_at=datetime(2026, 7, 18, 12, 0, 1, tzinfo=timezone.utc),
    )

    stored = store.replace(revised, expected_revision=1)

    path = tmp_path / stored.relative_path
    text = path.read_text(encoding="utf-8")
    assert "Revised content" in text
    assert "Original content" not in text
    assert list(path.parent.glob(".*.tmp")) == []


def test_store_replace_rejects_revision_mismatch(tmp_path: Path) -> None:
    store = FilesystemMemoryStore(tmp_path)
    original = _record()
    store.create(original)
    revised = replace(
        original,
        lifecycle=MemoryLifecycle(state=LifecycleState.ACTIVE, revision=2),
    )

    with pytest.raises(RevisionConflict):
        store.replace(revised, expected_revision=2)


def test_store_replace_detects_external_change_before_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = FilesystemMemoryStore(tmp_path)
    original = _record()
    store.create(original)
    revised = replace(
        original,
        content="Revised content",
        lifecycle=MemoryLifecycle(state=LifecycleState.ACTIVE, revision=2),
        updated_at=datetime(2026, 7, 18, 12, 0, 1, tzinfo=timezone.utc),
    )
    original_write_temp = store._write_temp

    def write_temp_and_tamper(path: Path, payload: bytes) -> Path:
        temporary = original_write_temp(path, payload)
        path.write_text(
            json.dumps(_payload(content="External change")),
            encoding="utf-8",
        )
        return temporary

    monkeypatch.setattr(store, "_write_temp", write_temp_and_tamper)

    with pytest.raises(WriteConflict):
        store.replace(revised, expected_revision=1)

    assert store.get(_reference()).record.content == "External change"
    assert list((tmp_path / "project" / "mnemosyne" / "decisions").glob(".*.tmp")) == []


def test_store_physically_deletes_current_record_and_leaves_directories(
    tmp_path: Path,
) -> None:
    store = FilesystemMemoryStore(tmp_path)
    stored = store.create(_record())
    path = tmp_path / stored.relative_path

    store.delete(_reference(), expected_revision=1)

    assert not path.exists()
    assert path.parent.is_dir()
    assert list(tmp_path.rglob("*.json")) == []


def test_store_delete_rejects_revision_mismatch(tmp_path: Path) -> None:
    store = FilesystemMemoryStore(tmp_path)
    store.create(_record())

    with pytest.raises(RevisionConflict):
        store.delete(_reference(), expected_revision=2)


def test_store_physically_deletes_unique_legacy_record(tmp_path: Path) -> None:
    path = tmp_path / "preference" / "leisure" / "legacy.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "legacy",
                "content": "Legacy content",
            }
        ),
        encoding="utf-8",
    )
    store = FilesystemMemoryStore(tmp_path)

    store.delete(
        LegacyMemoryReference(scope=MemoryScope.PREFERENCE, id="legacy"),
        expected_revision=None,
    )

    assert not path.exists()
    assert path.parent.is_dir()

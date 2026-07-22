import json
import os
import stat
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mymcp.memory.errors import (
    DeletionOutcomeUncertain,
    MemoryNotArchived,
    MemoryNotFound,
    MemorySourceUnavailable,
    MemoryValidationError,
    ReplacementOutcomeUncertain,
    RevisionConflict,
    UnsafeMemoryPath,
    WriteConflict,
)
from mymcp.memory.records import (
    LegacyMemoryReference,
    LifecycleState,
    MemoryLifecycle,
    MemoryRecordV2,
    MemoryReference,
    parse_memory_record,
)
from mymcp.memory.scopes import MemoryScope
from mymcp.memory.store import FilesystemMemoryStore


MEMORY_ID = "mem_0123456789abcdef0123456789abcdef"


def _payload(
    *,
    content: str = "Original content",
    revision: int = 1,
    state: str = "active",
    kind: str = "decision",
    occurred_at: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 2,
        "id": MEMORY_ID,
        "scope": "project",
        "namespace": {
            "kind": "project",
            "id": "mnemosyne",
            "label": "Mnemosyne",
        },
        "collection": {"id": "decisions", "label": "Decisions"},
        "kind": kind,
        "language": "en",
        "title": "Shared ownership",
        "content": content,
        "tags": ["architecture"],
        "provenance": {
            "origin": "explicit_user_statement",
            "recorded_via": "memory_remember",
        },
        "lifecycle": {"state": state, "revision": revision},
        "created_at": "2026-07-18T12:00:00Z",
        "updated_at": f"2026-07-18T12:00:0{revision - 1}Z",
    }
    if occurred_at is not None:
        payload["occurred_at"] = occurred_at
    return payload


def _record(
    *,
    content: str = "Original content",
    revision: int = 1,
    state: str = "active",
    kind: str = "decision",
    occurred_at: str | None = None,
) -> MemoryRecordV2:
    record = parse_memory_record(
        _payload(
            content=content,
            revision=revision,
            state=state,
            kind=kind,
            occurred_at=occurred_at,
        )
    )
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
    home = tmp_path / "home"
    home.mkdir(mode=0o750)
    root = home / ".mnemosyne" / "memory"
    store = FilesystemMemoryStore(root)

    stored = store.create(_record())

    path = root / stored.relative_path
    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8")) == _payload()
    assert list(path.parent.glob(".*.tmp")) == []
    if os.name == "posix":
        assert stat.S_IMODE(home.stat().st_mode) == 0o750
        for directory in (
            home / ".mnemosyne",
            root,
            root / "project",
            root / "project" / "mnemosyne",
            path.parent,
        ):
            assert stat.S_IMODE(directory.stat().st_mode) == 0o700
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


def test_store_replace_rejects_changed_event_occurrence_time(tmp_path: Path) -> None:
    store = FilesystemMemoryStore(tmp_path)
    original = _record(kind="event", occurred_at="2026-07-17T09:30:00Z")
    stored = store.create(original)
    path = tmp_path / stored.relative_path
    before = path.read_bytes()
    replacement = replace(
        original,
        occurred_at=datetime(2026, 7, 17, 9, 31, tzinfo=timezone.utc),
        lifecycle=MemoryLifecycle(state=LifecycleState.ACTIVE, revision=2),
        updated_at=datetime(2026, 7, 18, 12, 0, 1, tzinfo=timezone.utc),
    )

    with pytest.raises(WriteConflict):
        store.replace(replacement, expected_revision=1)

    assert path.read_bytes() == before


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


def test_store_replace_reports_uncertain_outcome_after_publication_sync_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = FilesystemMemoryStore(tmp_path)
    original = _record()
    stored = store.create(original)
    path = tmp_path / stored.relative_path
    revised = replace(
        original,
        content="Revised content",
        lifecycle=MemoryLifecycle(state=LifecycleState.ACTIVE, revision=2),
        updated_at=datetime(2026, 7, 18, 12, 0, 1, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(
        store,
        "_sync_directory",
        lambda directory: (_ for _ in ()).throw(MemorySourceUnavailable()),
    )

    with pytest.raises(ReplacementOutcomeUncertain):
        store.replace(revised, expected_revision=1)

    assert store.get(_reference()).record == revised
    assert list(path.parent.glob(".*.tmp")) == []


def test_store_physically_deletes_current_archived_record_without_artifacts(
    tmp_path: Path,
) -> None:
    store = FilesystemMemoryStore(tmp_path)
    stored = store.create(_record(revision=2, state="archived"))
    path = tmp_path / stored.relative_path
    unrelated = path.parent / "unrelated.txt"
    unrelated.write_bytes(b"unrelated")

    result = store.delete(_reference(), expected_revision=2)

    assert result is None
    assert not path.exists()
    assert path.parent.is_dir()
    assert list(tmp_path.rglob("*.json")) == []
    assert unrelated.read_bytes() == b"unrelated"
    assert sorted(item.name for item in path.parent.iterdir()) == ["unrelated.txt"]


def test_store_delete_rejects_current_active_record_without_changing_it(
    tmp_path: Path,
) -> None:
    store = FilesystemMemoryStore(tmp_path)
    stored = store.create(_record())
    path = tmp_path / stored.relative_path
    before = (path.read_bytes(), path.stat().st_mtime_ns)

    with pytest.raises(MemoryNotArchived):
        store.delete(_reference(), expected_revision=1)

    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


def test_store_delete_rejects_revision_mismatch(tmp_path: Path) -> None:
    store = FilesystemMemoryStore(tmp_path)
    store.create(_record())

    with pytest.raises(RevisionConflict):
        store.delete(_reference(), expected_revision=2)


@pytest.mark.parametrize("invalid_revision", [True, False, 0, -1, 1.0, "1", None])
def test_store_delete_rejects_invalid_revision_before_read(
    invalid_revision: object,
    tmp_path: Path,
) -> None:
    store = FilesystemMemoryStore(tmp_path)
    store.get = lambda reference: pytest.fail("store read must not run")

    with pytest.raises(MemoryValidationError) as caught:
        store.delete(_reference(), expected_revision=invalid_revision)

    assert caught.value.field == "expected_revision"


def test_store_delete_rejects_legacy_reference_before_discovery(tmp_path: Path) -> None:
    store = FilesystemMemoryStore(tmp_path)
    store.discover = lambda scope: pytest.fail("legacy discovery must not run")

    with pytest.raises(MemoryValidationError) as caught:
        store.delete(
            LegacyMemoryReference(scope=MemoryScope.PREFERENCE, id="legacy"),
            expected_revision=1,
        )

    assert caught.value.code == "invalid_reference"
    assert caught.value.field == "reference"


def test_store_delete_detects_external_change_and_preserves_changed_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = FilesystemMemoryStore(tmp_path)
    stored = store.create(_record(revision=2, state="archived"))
    path = tmp_path / stored.relative_path

    def tamper_then_fingerprint(selected: Path) -> str:
        selected.write_text(
            json.dumps(_payload(content="External change", revision=2, state="archived")),
            encoding="utf-8",
        )
        return FilesystemMemoryStore._fingerprint(store, selected)

    monkeypatch.setattr(store, "_fingerprint", tamper_then_fingerprint)

    with pytest.raises(WriteConflict):
        store.delete(_reference(), expected_revision=2)

    assert path.exists()
    assert store.get(_reference()).record.content == "External change"


def test_store_delete_reports_uncertain_outcome_after_unlink_sync_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = FilesystemMemoryStore(tmp_path)
    stored = store.create(_record(revision=2, state="archived"))
    path = tmp_path / stored.relative_path
    monkeypatch.setattr(
        store,
        "_sync_directory",
        lambda directory: (_ for _ in ()).throw(MemorySourceUnavailable()),
    )

    with pytest.raises(DeletionOutcomeUncertain):
        store.delete(_reference(), expected_revision=2)

    assert not path.exists()
    assert path.parent.is_dir()


def test_store_mutations_share_a_lock_across_instances(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deleting_store = FilesystemMemoryStore(tmp_path)
    replacing_store = FilesystemMemoryStore(tmp_path)
    original = _record(revision=2, state="archived")
    deleting_store.create(original)
    replacement = replace(
        original,
        lifecycle=MemoryLifecycle(state=LifecycleState.ACTIVE, revision=3),
        updated_at=datetime(2026, 7, 18, 12, 0, 2, tzinfo=timezone.utc),
    )
    fingerprint_read = threading.Event()
    continue_delete = threading.Event()
    original_fingerprint = deleting_store._fingerprint

    def pause_after_fingerprint(path: Path) -> str:
        fingerprint = original_fingerprint(path)
        fingerprint_read.set()
        assert continue_delete.wait(timeout=2)
        return fingerprint

    monkeypatch.setattr(deleting_store, "_fingerprint", pause_after_fingerprint)

    with ThreadPoolExecutor(max_workers=2) as executor:
        deleting = executor.submit(
            deleting_store.delete,
            _reference(),
            expected_revision=2,
        )
        assert fingerprint_read.wait(timeout=2)
        replacing = executor.submit(
            replacing_store.replace,
            replacement,
            expected_revision=2,
        )
        assert not replacing.done()
        continue_delete.set()
        assert deleting.result(timeout=2) is None
        with pytest.raises(MemoryNotFound):
            replacing.result(timeout=2)


def test_store_legacy_records_remain_readable_but_are_not_deletable(
    tmp_path: Path,
) -> None:
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
    reference = LegacyMemoryReference(scope=MemoryScope.PREFERENCE, id="legacy")

    assert store.get(reference).record.content == "Legacy content"
    with pytest.raises(MemoryValidationError):
        store.delete(reference, expected_revision=1)

    assert path.exists()
    assert path.parent.is_dir()

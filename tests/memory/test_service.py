import json
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mnemosyne.memory.errors import MutationDisabled, RevisionConflict
from mnemosyne.memory.records import (
    LegacyMemoryReference,
    LifecycleState,
    MemoryDraft,
    MemoryReference,
    MemoryRevision,
)
from mnemosyne.memory.scopes import MemoryScope
from mnemosyne.memory.service import MemoryService
from mnemosyne.memory.store import FilesystemMemoryStore


MEMORY_ID = "mem_0123456789abcdef0123456789abcdef"
NOW = datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 7, 18, 13, 0, tzinfo=timezone.utc)


def _draft() -> MemoryDraft:
    return MemoryDraft.from_dict(
        {
            "scope": "preference",
            "namespace": {
                "kind": "domain",
                "id": "leisure",
                "label": "Leisure",
            },
            "collection": None,
            "kind": "preference",
            "language": "en",
            "title": "Rainy weekends",
            "content": "The user prefers museums on rainy weekends.",
            "tags": ["leisure", "rainy-day"],
            "origin": "explicit_user_statement",
        }
    )


def _reference() -> MemoryReference:
    return MemoryReference(
        scope=MemoryScope.PREFERENCE,
        namespace_id="leisure",
        collection_id=None,
        id=MEMORY_ID,
    )


def _service(
    tmp_path: Path,
    *,
    enabled: bool = True,
    clock=lambda: NOW,
) -> MemoryService:
    return MemoryService(
        FilesystemMemoryStore(tmp_path),
        mutations_enabled=enabled,
        clock=clock,
        id_factory=lambda: MEMORY_ID,
    )


def test_service_disables_mutations_by_default(tmp_path: Path) -> None:
    service = MemoryService(FilesystemMemoryStore(tmp_path))

    with pytest.raises(MutationDisabled):
        service.remember(_draft())

    assert not tmp_path.exists() or list(tmp_path.rglob("*.json")) == []


def test_service_remember_generates_operational_fields_and_persists_record(
    tmp_path: Path,
) -> None:
    result = _service(tmp_path).remember(_draft())

    assert result.status == "remembered"
    assert result.memory.id == MEMORY_ID
    assert result.memory.created_at == NOW
    assert result.memory.updated_at == NOW
    assert result.memory.lifecycle.state is LifecycleState.ACTIVE
    assert result.memory.lifecycle.revision == 1
    assert result.memory.provenance.recorded_via.value == "memory_remember"
    assert (tmp_path / "preference" / "leisure" / f"{MEMORY_ID}.json").exists()


def test_service_remember_returns_existing_active_duplicate(tmp_path: Path) -> None:
    service = _service(tmp_path)
    first = service.remember(_draft())

    second = service.remember(_draft())

    assert second.status == "already_exists"
    assert second.memory.id == first.memory.id
    assert len(list(tmp_path.rglob("*.json"))) == 1


def test_service_serializes_concurrent_duplicate_detection(tmp_path: Path) -> None:
    store = FilesystemMemoryStore(tmp_path)
    original_discover = store.discover
    counter_lock = threading.Lock()
    callers_ready = threading.Barrier(2)
    active_discovery = 0
    maximum_active_discovery = 0

    def observed_discover(scope: MemoryScope):
        nonlocal active_discovery, maximum_active_discovery
        with counter_lock:
            active_discovery += 1
            maximum_active_discovery = max(maximum_active_discovery, active_discovery)
        try:
            time.sleep(0.05)
            return original_discover(scope)
        finally:
            with counter_lock:
                active_discovery -= 1

    store.discover = observed_discover
    service = MemoryService(
        store,
        mutations_enabled=True,
        clock=lambda: NOW,
        id_factory=lambda: f"mem_{uuid.uuid4().hex}",
    )

    def remember_after_barrier():
        callers_ready.wait()
        return service.remember(_draft())

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: remember_after_barrier(), range(2)))

    assert maximum_active_discovery == 1
    assert sorted(result.status for result in results) == [
        "already_exists",
        "remembered",
    ]
    assert len(list(tmp_path.rglob("*.json"))) == 1


def test_service_remember_returns_existing_archived_duplicate(tmp_path: Path) -> None:
    service = _service(tmp_path)
    remembered = service.remember(_draft())
    service.archive(_reference(), expected_revision=remembered.memory.lifecycle.revision)

    duplicate = service.remember(_draft())

    assert duplicate.status == "existing_archived"
    assert duplicate.memory.id == remembered.memory.id
    assert duplicate.memory.lifecycle.state is LifecycleState.ARCHIVED
    assert len(list(tmp_path.rglob("*.json"))) == 1


def test_service_inspect_is_available_when_mutations_are_disabled(tmp_path: Path) -> None:
    enabled = _service(tmp_path)
    enabled.remember(_draft())
    disabled = _service(tmp_path, enabled=False)

    inspected = disabled.inspect(_reference())

    assert inspected.id == MEMORY_ID


def test_service_revise_replaces_only_mutable_state(tmp_path: Path) -> None:
    clocks = iter([NOW, LATER])
    service = _service(tmp_path, clock=lambda: next(clocks))
    original = service.remember(_draft()).memory
    revision = MemoryRevision.from_dict(
        {
            "expected_revision": 1,
            "namespace_label": "Free time",
            "collection_label": None,
            "title": "Rainy-day activities",
            "content": "The user prefers galleries on rainy weekends.",
            "tags": ["leisure", "rainy-day"],
        }
    )

    result = service.revise(_reference(), revision)

    assert result.status == "revised"
    assert result.memory.id == original.id
    assert result.memory.scope == original.scope
    assert result.memory.namespace.id == original.namespace.id
    assert result.memory.namespace.label == "Free time"
    assert result.memory.kind == original.kind
    assert result.memory.created_at == original.created_at
    assert result.memory.updated_at == LATER
    assert result.memory.lifecycle.revision == 2
    serialized = next(tmp_path.rglob("*.json")).read_text(encoding="utf-8")
    assert "galleries" in serialized
    assert "museums" not in serialized


def test_service_revise_rejects_stale_expected_revision(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.remember(_draft())
    stale = MemoryRevision.from_dict(
        {
            "expected_revision": 2,
            "namespace_label": "Leisure",
            "collection_label": None,
            "title": "Rainy weekends",
            "content": "Changed",
            "tags": [],
        }
    )

    with pytest.raises(RevisionConflict):
        service.revise(_reference(), stale)


def test_service_archive_and_restore_are_revisioned_and_idempotent(
    tmp_path: Path,
) -> None:
    clocks = iter([NOW, LATER, LATER])
    service = _service(tmp_path, clock=lambda: next(clocks))
    service.remember(_draft())

    archived = service.archive(_reference(), expected_revision=1)
    already_archived = service.archive(_reference(), expected_revision=2)
    restored = service.restore(_reference(), expected_revision=2)
    already_active = service.restore(_reference(), expected_revision=3)

    assert archived.status == "archived"
    assert archived.memory.lifecycle.state is LifecycleState.ARCHIVED
    assert archived.memory.lifecycle.revision == 2
    assert already_archived.status == "already_archived"
    assert already_archived.memory.lifecycle.revision == 2
    assert restored.status == "restored"
    assert restored.memory.lifecycle.state is LifecycleState.ACTIVE
    assert restored.memory.lifecycle.revision == 3
    assert already_active.status == "already_active"
    assert already_active.memory.lifecycle.revision == 3


def test_service_forget_physically_deletes_current_record(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.remember(_draft())

    result = service.forget(_reference(), expected_revision=1)

    assert result.status == "forgotten"
    assert result.reference == _reference()
    assert list(tmp_path.rglob("*.json")) == []


def test_service_forget_physically_deletes_legacy_record(tmp_path: Path) -> None:
    path = tmp_path / "preference" / "legacy" / "old.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "old",
                "content": "Legacy memory",
            }
        ),
        encoding="utf-8",
    )
    service = _service(tmp_path)
    reference = LegacyMemoryReference(scope=MemoryScope.PREFERENCE, id="old")

    result = service.forget(reference, expected_revision=None)

    assert result.status == "forgotten"
    assert result.reference == reference
    assert not path.exists()

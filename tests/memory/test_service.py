import json
import stat
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mnemosyne.memory.errors import (
    ContentRefusalReason,
    DisallowedMemoryContent,
    MemoryNotArchived,
    MemoryNotFound,
    MemoryValidationError,
    MutationDisabled,
    RevisionConflict,
)
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
SECOND_MEMORY_ID = "mem_fedcba9876543210fedcba9876543210"
NOW = datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 7, 18, 13, 0, tzinfo=timezone.utc)
OCCURRED_AT = datetime(2026, 7, 17, 9, 30, tzinfo=timezone.utc)


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


def _collection_draft() -> MemoryDraft:
    return MemoryDraft.from_dict(
        {
            "scope": "preference",
            "namespace": {
                "kind": "domain",
                "id": "leisure",
                "label": "Leisure",
            },
            "collection": {"id": "weekends", "label": "Weekends"},
            "kind": "preference",
            "language": "en",
            "title": "Rainy weekends",
            "content": "The user prefers museums on rainy weekends.",
            "tags": ["leisure", "rainy-day"],
            "origin": "explicit_user_statement",
        }
    )


def _event_draft(occurred_at: str = "2026-07-17T09:30:00Z") -> MemoryDraft:
    return MemoryDraft.from_dict(
        {
            "scope": "project",
            "namespace": {
                "kind": "project",
                "id": "mnemosyne",
                "label": "Mnemosyne",
            },
            "collection": {"id": "events", "label": "Events"},
            "kind": "event",
            "language": "en",
            "title": "Track activated",
            "content": "Track 021 moved to active execution.",
            "tags": ["track-021"],
            "origin": "explicit_user_statement",
            "occurred_at": occurred_at,
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


def test_service_remember_refuses_disallowed_content_before_discovery_or_write(
    tmp_path: Path,
) -> None:
    store = FilesystemMemoryStore(tmp_path)
    store.discover = lambda scope: pytest.fail("discovery must not run")
    service = MemoryService(store, mutations_enabled=True)
    arguments = {
        "scope": "project",
        "namespace": {"kind": "project", "id": "mnemosyne", "label": None},
        "collection": None,
        "kind": "decision",
        "language": "en",
        "title": None,
        "content": "Authorization: Bearer synthetic-token",
        "tags": [],
        "origin": "explicit_user_statement",
    }

    with pytest.raises(DisallowedMemoryContent) as caught:
        service.remember(MemoryDraft.from_dict(arguments))

    assert caught.value.field == "content"
    assert caught.value.reason is ContentRefusalReason.CREDENTIAL_SHAPE
    assert not tmp_path.exists() or list(tmp_path.iterdir()) == []


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


def test_service_event_identity_and_mutations_preserve_occurrence_time(
    tmp_path: Path,
) -> None:
    ids = iter([MEMORY_ID, SECOND_MEMORY_ID])
    clocks = iter([NOW, NOW, LATER, LATER, LATER])
    service = MemoryService(
        FilesystemMemoryStore(tmp_path),
        mutations_enabled=True,
        clock=lambda: next(clocks),
        id_factory=lambda: next(ids),
    )

    first = service.remember(_event_draft())
    duplicate = service.remember(_event_draft())
    later_event = service.remember(_event_draft("2026-07-17T09:31:00Z"))
    reference = MemoryReference(
        scope=MemoryScope.PROJECT,
        namespace_id="mnemosyne",
        collection_id="events",
        id=MEMORY_ID,
    )

    assert first.memory.occurred_at == OCCURRED_AT
    assert duplicate.status == "already_exists"
    assert duplicate.memory.id == MEMORY_ID
    assert later_event.status == "remembered"
    assert later_event.memory.id == SECOND_MEMORY_ID
    assert len(list(tmp_path.rglob("*.json"))) == 2

    revised = service.revise(
        reference,
        MemoryRevision.from_dict(
            {
                "expected_revision": 1,
                "namespace_label": "Mnemosyne",
                "collection_label": "Events",
                "title": "Track activation",
                "content": first.memory.content,
                "tags": list(first.memory.tags),
            }
        ),
    )
    archived = service.archive(reference, expected_revision=2)
    restored = service.restore(reference, expected_revision=3)

    assert revised.memory.occurred_at == OCCURRED_AT
    assert archived.memory.occurred_at == OCCURRED_AT
    assert restored.memory.occurred_at == OCCURRED_AT
    assert service.inspect(reference).occurred_at == OCCURRED_AT


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
    assert result.memory.namespace.kind == original.namespace.kind
    assert result.memory.namespace.id == original.namespace.id
    assert result.memory.namespace.label == "Free time"
    assert result.memory.collection == original.collection
    assert result.memory.kind == original.kind
    assert result.memory.language == original.language
    assert result.memory.provenance == original.provenance
    assert result.memory.created_at == original.created_at
    assert result.memory.updated_at == LATER
    assert result.memory.lifecycle.state is original.lifecycle.state
    assert result.memory.lifecycle.revision == 2
    assert len(list(tmp_path.rglob("*.json"))) == 1
    serialized = next(tmp_path.rglob("*.json")).read_text(encoding="utf-8")
    assert "galleries" in serialized
    assert "museums" not in serialized


def test_service_revise_changes_collection_label_without_relocating_memory(
    tmp_path: Path,
) -> None:
    clocks = iter([NOW, LATER])
    service = _service(tmp_path, clock=lambda: next(clocks))
    original = service.remember(_collection_draft()).memory
    reference = MemoryReference(
        scope=MemoryScope.PREFERENCE,
        namespace_id="leisure",
        collection_id="weekends",
        id=MEMORY_ID,
    )
    path = (
        tmp_path
        / "preference"
        / "leisure"
        / "weekends"
        / f"{MEMORY_ID}.json"
    )

    result = service.revise(
        reference,
        MemoryRevision.from_dict(
            {
                "expected_revision": 1,
                "namespace_label": original.namespace.label,
                "collection_label": "Rainy days",
                "title": original.title,
                "content": original.content,
                "tags": list(original.tags),
            }
        ),
    )

    assert result.status == "revised"
    assert result.memory.collection is not None
    assert result.memory.collection.id == "weekends"
    assert result.memory.collection.label == "Rainy days"
    assert result.memory.lifecycle.revision == 2
    assert path.exists()
    assert len(list(tmp_path.rglob("*.json"))) == 1


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


def test_service_revise_returns_already_current_without_clock_or_write(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    original = service.remember(_draft()).memory
    path = next(tmp_path.rglob("*.json"))
    original_bytes = path.read_bytes()
    original_metadata = path.stat()
    service.clock = lambda: pytest.fail("clock must not run")
    service.store.replace = lambda record, expected_revision: pytest.fail(
        "store write must not run"
    )
    revision = MemoryRevision.from_dict(
        {
            "expected_revision": 1,
            "namespace_label": original.namespace.label,
            "collection_label": None,
            "title": original.title,
            "content": original.content,
            "tags": list(original.tags),
        }
    )

    result = service.revise(_reference(), revision)

    assert result.status == "already_current"
    assert result.memory == original
    assert path.read_bytes() == original_bytes
    assert path.stat().st_mtime_ns == original_metadata.st_mtime_ns


def test_service_revise_checks_stale_revision_before_already_current(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    original = service.remember(_draft()).memory
    stale_no_op = MemoryRevision.from_dict(
        {
            "expected_revision": 2,
            "namespace_label": original.namespace.label,
            "collection_label": None,
            "title": original.title,
            "content": original.content,
            "tags": list(original.tags),
        }
    )

    with pytest.raises(RevisionConflict):
        service.revise(_reference(), stale_no_op)


def test_service_revise_preserves_archived_state(tmp_path: Path) -> None:
    clocks = iter([NOW, LATER, LATER])
    service = _service(tmp_path, clock=lambda: next(clocks))
    original = service.remember(_draft()).memory
    archived = service.archive(_reference(), expected_revision=1).memory
    revision = MemoryRevision.from_dict(
        {
            "expected_revision": 2,
            "namespace_label": "Free time",
            "collection_label": None,
            "title": original.title,
            "content": "The user prefers galleries on rainy weekends.",
            "tags": list(original.tags),
        }
    )

    result = service.revise(_reference(), revision)

    assert result.status == "revised"
    assert result.memory.lifecycle.state is LifecycleState.ARCHIVED
    assert result.memory.lifecycle.revision == 3
    assert result.memory.created_at == original.created_at
    assert result.memory.provenance == archived.provenance
    assert len(list(tmp_path.rglob("*.json"))) == 1


def test_service_revise_refuses_disallowed_replacement_before_read_or_write(
    tmp_path: Path,
) -> None:
    store = FilesystemMemoryStore(tmp_path)
    store.get = lambda reference: pytest.fail("store read must not run")
    store.replace = lambda record, expected_revision: pytest.fail(
        "store write must not run"
    )
    service = MemoryService(store, mutations_enabled=True)
    revision = MemoryRevision.from_dict(
        {
            "expected_revision": 1,
            "namespace_label": "Tea",
            "collection_label": None,
            "title": "Japanese green tea",
            "content": "Authorization: Bearer synthetic-token",
            "tags": ["tea"],
        }
    )

    with pytest.raises(DisallowedMemoryContent) as caught:
        service.revise(_reference(), revision)

    assert caught.value.field == "content"
    assert caught.value.reason is ContentRefusalReason.CREDENTIAL_SHAPE
    assert not tmp_path.exists() or list(tmp_path.iterdir()) == []


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


@pytest.mark.parametrize("invalid_revision", [True, False, 0, -1, 1.0, "1", None])
@pytest.mark.parametrize("operation", ["archive", "restore"])
def test_service_lifecycle_rejects_non_positive_exact_integer_revision_before_read(
    invalid_revision: object,
    operation: str,
    tmp_path: Path,
) -> None:
    store = FilesystemMemoryStore(tmp_path)
    store.get = lambda reference: pytest.fail("store read must not run")
    service = MemoryService(store, mutations_enabled=True)

    with pytest.raises(MemoryValidationError) as caught:
        getattr(service, operation)(_reference(), expected_revision=invalid_revision)

    assert caught.value.field == "expected_revision"


def test_service_lifecycle_stale_target_states_conflict_and_idempotency_does_not_write(
    tmp_path: Path,
) -> None:
    clocks = iter([NOW, LATER, LATER])
    service = _service(tmp_path, clock=lambda: next(clocks))
    service.remember(_draft())
    archived = service.archive(_reference(), expected_revision=1)
    path = next(tmp_path.rglob("*.json"))

    with pytest.raises(RevisionConflict):
        service.archive(_reference(), expected_revision=1)
    before_archive = (path.read_bytes(), stat.S_IMODE(path.stat().st_mode), path.stat().st_mtime_ns)
    assert service.archive(_reference(), expected_revision=2).status == "already_archived"
    assert (path.read_bytes(), stat.S_IMODE(path.stat().st_mode), path.stat().st_mtime_ns) == before_archive

    restored = service.restore(_reference(), expected_revision=archived.memory.lifecycle.revision)
    with pytest.raises(RevisionConflict):
        service.restore(_reference(), expected_revision=2)
    before_restore = (path.read_bytes(), stat.S_IMODE(path.stat().st_mode), path.stat().st_mtime_ns)
    assert service.restore(_reference(), expected_revision=restored.memory.lifecycle.revision).status == "already_active"
    assert (path.read_bytes(), stat.S_IMODE(path.stat().st_mode), path.stat().st_mtime_ns) == before_restore


def test_service_forget_physically_deletes_current_archived_record(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.remember(_draft())
    archived = service.archive(_reference(), expected_revision=1)

    result = service.forget(
        _reference(),
        expected_revision=archived.memory.lifecycle.revision,
    )

    assert result.status == "forgotten"
    assert result.reference == _reference()
    assert list(tmp_path.rglob("*.json")) == []

    with pytest.raises(MemoryNotFound):
        service.forget(_reference(), expected_revision=2)



def test_service_forget_requires_current_archived_record(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.remember(_draft())

    with pytest.raises(RevisionConflict):
        service.forget(_reference(), expected_revision=2)

    with pytest.raises(MemoryNotArchived):
        service.forget(_reference(), expected_revision=1)

    assert service.inspect(_reference()).lifecycle.state is LifecycleState.ACTIVE


@pytest.mark.parametrize("invalid_revision", [True, False, 0, -1, 1.0, "1", None])
def test_service_forget_rejects_invalid_revision_before_read(
    invalid_revision: object,
    tmp_path: Path,
) -> None:
    store = FilesystemMemoryStore(tmp_path)
    store.delete = lambda reference, expected_revision: pytest.fail(
        "store delete must not run"
    )
    service = MemoryService(store, mutations_enabled=True)

    with pytest.raises(MemoryValidationError) as caught:
        service.forget(_reference(), expected_revision=invalid_revision)

    assert caught.value.field == "expected_revision"


def test_service_forget_rejects_legacy_reference_before_store_access(
    tmp_path: Path,
) -> None:
    store = FilesystemMemoryStore(tmp_path)
    store.delete = lambda reference, expected_revision: pytest.fail(
        "store delete must not run"
    )
    service = MemoryService(store, mutations_enabled=True)

    with pytest.raises(MemoryValidationError) as caught:
        service.forget(
            LegacyMemoryReference(scope=MemoryScope.PREFERENCE, id="old"),
            expected_revision=1,
        )

    assert caught.value.code == "invalid_reference"
    assert caught.value.field == "reference"

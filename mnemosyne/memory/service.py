import threading
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timezone

from mnemosyne.memory.errors import (
    MemoryValidationError,
    MutationDisabled,
    RevisionConflict,
)
from mnemosyne.memory.normalization import normalize_memory_id
from mnemosyne.memory.policy import validate_remember_content, validate_revision_content
from mnemosyne.memory.records import (
    LegacyMemoryRecordV1,
    LegacyMemoryReference,
    LifecycleState,
    MemoryDraft,
    MemoryLifecycle,
    MemoryNamespace,
    MemoryProvenance,
    MemoryRecordV2,
    MemoryRecordedVia,
    MemoryReference,
    MemoryRevision,
)
from mnemosyne.memory.retrieval import MemoryMatch, rank_memories
from mnemosyne.memory.scopes import MemoryScope
from mnemosyne.memory.store import FilesystemMemoryStore


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


def _default_id_factory() -> str:
    return f"mem_{uuid.uuid4().hex}"


@dataclass(frozen=True)
class MemoryResult:
    status: str
    memory: MemoryRecordV2


@dataclass(frozen=True)
class ForgetResult:
    status: str
    reference: MemoryReference


class MemoryService:
    def __init__(
        self,
        store: FilesystemMemoryStore,
        *,
        mutations_enabled: bool = False,
        clock: Callable[[], datetime] = _default_clock,
        id_factory: Callable[[], str] = _default_id_factory,
    ) -> None:
        self.store = store
        self.mutations_enabled = mutations_enabled
        self.clock = clock
        self.id_factory = id_factory
        self._mutation_lock = threading.RLock()

    def _require_mutations(self) -> None:
        if not self.mutations_enabled:
            raise MutationDisabled

    def _now(self) -> datetime:
        value = self.clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise MemoryValidationError(
                "invalid_record",
                "timestamp",
                "clock must return an aware datetime",
            )
        return value.astimezone(timezone.utc).replace(microsecond=0)

    def _current(
        self,
        reference: MemoryReference,
        expected_revision: int,
    ) -> MemoryRecordV2:
        stored = self.store.get(reference)
        if not isinstance(stored.record, MemoryRecordV2):
            raise MemoryValidationError(
                "invalid_reference",
                "reference",
                "reference does not identify a version-2 memory",
            )
        if stored.record.lifecycle.revision != expected_revision:
            raise RevisionConflict
        return stored.record

    def inspect(
        self,
        reference: MemoryReference | LegacyMemoryReference,
    ) -> LegacyMemoryRecordV1 | MemoryRecordV2:
        return self.store.get(reference).record

    def recall(
        self,
        scope: MemoryScope,
        query: str,
        tags: Sequence[str],
    ) -> list[MemoryMatch]:
        return rank_memories(self.store.discover(scope), query, tags)

    def remember(self, draft: MemoryDraft) -> MemoryResult:
        self._require_mutations()
        validate_remember_content(draft)
        with self._mutation_lock:
            duplicate_key = draft.duplicate_key()
            for stored in self.store.discover(draft.scope):
                if (
                    isinstance(stored.record, MemoryRecordV2)
                    and stored.record.duplicate_key() == duplicate_key
                ):
                    status = (
                        "already_exists"
                        if stored.record.lifecycle.state is LifecycleState.ACTIVE
                        else "existing_archived"
                    )
                    return MemoryResult(status=status, memory=stored.record)

            now = self._now()
            record = MemoryRecordV2(
                id=normalize_memory_id(self.id_factory()),
                scope=draft.scope,
                namespace=draft.namespace,
                collection=draft.collection,
                kind=draft.kind,
                language=draft.language,
                title=draft.title,
                content=draft.content,
                tags=draft.tags,
                provenance=MemoryProvenance(
                    origin=draft.origin,
                    recorded_via=MemoryRecordedVia.MEMORY_REMEMBER,
                ),
                lifecycle=MemoryLifecycle(
                    state=LifecycleState.ACTIVE,
                    revision=1,
                ),
                created_at=now,
                updated_at=now,
            )
            stored = self.store.create(record)
            assert isinstance(stored.record, MemoryRecordV2)
            return MemoryResult(status="remembered", memory=stored.record)

    def revise(
        self,
        reference: MemoryReference,
        revision: MemoryRevision,
    ) -> MemoryResult:
        self._require_mutations()
        validate_revision_content(revision)
        with self._mutation_lock:
            current = self._current(reference, revision.expected_revision)
            if current.collection is None:
                if revision.collection_label is not None:
                    raise MemoryValidationError(
                        "invalid_collection",
                        "collection.label",
                        "memory has no collection",
                    )
                collection = None
            else:
                collection = replace(
                    current.collection,
                    label=revision.collection_label,
                )
            if (
                current.namespace.label,
                current.collection.label if current.collection is not None else None,
                current.title,
                current.content,
                current.tags,
            ) == (
                revision.namespace_label,
                revision.collection_label,
                revision.title,
                revision.content,
                revision.tags,
            ):
                return MemoryResult(status="already_current", memory=current)
            revised = replace(
                current,
                namespace=replace(
                    current.namespace,
                    label=revision.namespace_label,
                ),
                collection=collection,
                title=revision.title,
                content=revision.content,
                tags=revision.tags,
                lifecycle=MemoryLifecycle(
                    state=current.lifecycle.state,
                    revision=current.lifecycle.revision + 1,
                ),
                updated_at=self._now(),
            )
            stored = self.store.replace(
                revised,
                expected_revision=revision.expected_revision,
            )
            assert isinstance(stored.record, MemoryRecordV2)
            return MemoryResult(status="revised", memory=stored.record)

    def _set_state(
        self,
        reference: MemoryReference,
        *,
        expected_revision: int,
        state: LifecycleState,
    ) -> MemoryResult:
        self._require_mutations()
        if type(expected_revision) is not int or expected_revision < 1:
            raise MemoryValidationError(
                "invalid_record",
                "expected_revision",
                "invalid expected_revision",
            )
        with self._mutation_lock:
            current = self._current(reference, expected_revision)
            if current.lifecycle.state is state:
                status = (
                    "already_archived"
                    if state is LifecycleState.ARCHIVED
                    else "already_active"
                )
                return MemoryResult(status=status, memory=current)
            changed = replace(
                current,
                lifecycle=MemoryLifecycle(
                    state=state,
                    revision=current.lifecycle.revision + 1,
                ),
                updated_at=self._now(),
            )
            stored = self.store.replace(changed, expected_revision=expected_revision)
            assert isinstance(stored.record, MemoryRecordV2)
            status = "archived" if state is LifecycleState.ARCHIVED else "restored"
            return MemoryResult(status=status, memory=stored.record)

    def archive(
        self,
        reference: MemoryReference,
        *,
        expected_revision: int,
    ) -> MemoryResult:
        return self._set_state(
            reference,
            expected_revision=expected_revision,
            state=LifecycleState.ARCHIVED,
        )

    def restore(
        self,
        reference: MemoryReference,
        *,
        expected_revision: int,
    ) -> MemoryResult:
        return self._set_state(
            reference,
            expected_revision=expected_revision,
            state=LifecycleState.ACTIVE,
        )

    def forget(
        self,
        reference: MemoryReference,
        *,
        expected_revision: int,
    ) -> ForgetResult:
        self._require_mutations()
        if not isinstance(reference, MemoryReference):
            raise MemoryValidationError(
                "invalid_reference",
                "reference",
                "reference does not identify a version-2 memory",
            )
        if type(expected_revision) is not int or expected_revision < 1:
            raise MemoryValidationError(
                "invalid_record",
                "expected_revision",
                "invalid expected_revision",
            )
        with self._mutation_lock:
            self.store.delete(reference, expected_revision=expected_revision)
            return ForgetResult(status="forgotten", reference=reference)

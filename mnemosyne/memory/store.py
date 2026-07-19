import json
import hashlib
import logging
import os
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path

from mnemosyne.memory.errors import (
    AmbiguousMemoryReference,
    CandidateLimitExceeded,
    DeletionOutcomeUncertain,
    MemoryNotArchived,
    MemoryNotFound,
    MemorySourceUnavailable,
    MemoryValidationError,
    RevisionConflict,
    UnsafeMemoryPath,
    WriteConflict,
)
from mnemosyne.memory.paths import (
    ensure_record_path,
    relative_path_for_reference,
    scope_directory,
)
from mnemosyne.memory.records import (
    LegacyMemoryRecordV1,
    LegacyMemoryReference,
    LifecycleState,
    MemoryRecordV2,
    MemoryReference,
    parse_memory_record,
    serialize_memory_record,
)
from mnemosyne.memory.scopes import MemoryScope, get_scope_definition


logger = logging.getLogger("mnemosyne.memory.store")

MAX_CANDIDATES = 1_000
MAX_DIRECTORY_DEPTH = 4
MAX_FILE_BYTES = 65_536


@dataclass(frozen=True)
class StoredMemory:
    record: LegacyMemoryRecordV1 | MemoryRecordV2
    scope: MemoryScope
    relative_path: str
    fingerprint: str

    @property
    def scope_relative_path(self) -> str:
        scope_directory_name = get_scope_definition(self.scope).directory
        try:
            return Path(self.relative_path).relative_to(scope_directory_name).as_posix()
        except ValueError as error:
            raise UnsafeMemoryPath from error


def _log_skipped(scope: MemoryScope, reason: str) -> None:
    logger.warning(
        "skipped scope=%r reason=%r",
        scope.value,
        reason,
    )


class FilesystemMemoryStore:
    _lock_registry_guard = threading.Lock()
    _mutation_locks: dict[Path, threading.RLock] = {}

    def __init__(self, memory_root: Path) -> None:
        self.memory_root = memory_root
        lock_key = memory_root.absolute()
        with self._lock_registry_guard:
            self._mutation_lock = self._mutation_locks.setdefault(
                lock_key,
                threading.RLock(),
            )

    def _discover_candidates(
        self,
        directory: Path,
        scope: MemoryScope,
    ) -> list[Path]:
        candidates: list[Path] = []

        def walk(current: Path, relative_directory: Path, depth: int) -> None:
            try:
                with os.scandir(current) as iterator:
                    entries = sorted(iterator, key=lambda entry: entry.name)
            except OSError as error:
                raise MemorySourceUnavailable from error

            for entry in entries:
                relative_path = relative_directory / entry.name
                try:
                    if entry.is_symlink():
                        _log_skipped(scope, "symlink")
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        if depth >= MAX_DIRECTORY_DEPTH:
                            _log_skipped(scope, "too_deep")
                        else:
                            walk(Path(entry.path), relative_path, depth + 1)
                        continue
                    is_json_file = (
                        entry.is_file(follow_symlinks=False)
                        and Path(entry.name).suffix == ".json"
                    )
                except OSError:
                    _log_skipped(scope, "unreadable")
                    continue

                if not is_json_file:
                    continue
                candidates.append(Path(entry.path))
                if len(candidates) > MAX_CANDIDATES:
                    raise CandidateLimitExceeded

        walk(directory, Path(), 0)
        return candidates

    def _reject_symlink_components(self, scope_path: Path, path: Path) -> None:
        current = scope_path
        if current.is_symlink():
            raise UnsafeMemoryPath
        for part in path.relative_to(scope_path).parts:
            current /= part
            if current.is_symlink():
                raise UnsafeMemoryPath

    def _ensure_private_directories(self, directory: Path) -> None:
        try:
            relative_directory = directory.relative_to(self.memory_root)
        except ValueError as error:
            raise UnsafeMemoryPath from error

        missing_ancestors: list[Path] = []
        current = self.memory_root
        while not current.exists():
            if current.is_symlink():
                raise UnsafeMemoryPath
            missing_ancestors.append(current)
            parent = current.parent
            if parent == current:
                raise MemorySourceUnavailable
            current = parent

        directories = list(reversed(missing_ancestors))
        if not directories or directories[-1] != self.memory_root:
            directories.append(self.memory_root)
        current = self.memory_root
        for part in relative_directory.parts:
            current /= part
            directories.append(current)

        for current in directories:
            if current.is_symlink():
                raise UnsafeMemoryPath
            if current.exists():
                if not current.is_dir():
                    raise MemorySourceUnavailable
                continue
            try:
                current.mkdir(mode=0o700)
            except FileExistsError:
                if current.is_symlink() or not current.is_dir():
                    raise UnsafeMemoryPath
            except OSError as error:
                raise MemorySourceUnavailable from error

    def _serialize(self, record: MemoryRecordV2) -> bytes:
        serialized_record = serialize_memory_record(record)
        canonical_record = parse_memory_record(serialized_record)
        if canonical_record != record:
            raise MemoryValidationError(
                "invalid_record",
                "record",
                "record is not canonical",
            )
        payload = (
            json.dumps(
                serialized_record,
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        ).encode("utf-8")
        if len(payload) > MAX_FILE_BYTES:
            raise MemoryValidationError(
                "invalid_record",
                "record",
                "serialized memory exceeds file limit",
            )
        return payload

    def _write_temp(self, path: Path, payload: bytes) -> Path:
        descriptor: int | None = None
        temporary_path: Path | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{path.stem}.",
                suffix=".tmp",
                dir=path.parent,
            )
            temporary_path = Path(temporary_name)
            os.fchmod(descriptor, 0o600)
            temporary_file = os.fdopen(descriptor, "wb")
            descriptor = None
            with temporary_file:
                temporary_file.write(payload)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            return temporary_path
        except OSError as error:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise MemorySourceUnavailable from error

    def _fingerprint(self, path: Path) -> str:
        try:
            with path.open("rb") as source:
                raw_record = source.read(MAX_FILE_BYTES + 1)
        except OSError as error:
            raise MemorySourceUnavailable from error
        if len(raw_record) > MAX_FILE_BYTES:
            raise MemorySourceUnavailable
        return hashlib.sha256(raw_record).hexdigest()

    def _sync_directory(self, directory: Path) -> None:
        if os.name != "posix":
            return
        try:
            descriptor = os.open(directory, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        except OSError as error:
            raise MemorySourceUnavailable from error

    def _load(
        self,
        path: Path,
        scope: MemoryScope,
        scope_path: Path,
    ) -> StoredMemory | None:
        root_relative_path = path.relative_to(self.memory_root).as_posix()
        try:
            if path.is_symlink():
                _log_skipped(scope, "symlink")
                return None
            if path.stat().st_size > MAX_FILE_BYTES:
                _log_skipped(scope, "oversized")
                return None
            raw_record = path.read_bytes()
        except OSError:
            _log_skipped(scope, "unreadable")
            return None

        if len(raw_record) > MAX_FILE_BYTES:
            _log_skipped(scope, "oversized")
            return None
        try:
            text_record = raw_record.decode("utf-8")
        except UnicodeDecodeError:
            _log_skipped(scope, "invalid_encoding")
            return None
        try:
            payload = json.loads(text_record)
        except json.JSONDecodeError:
            _log_skipped(scope, "invalid_json")
            return None
        try:
            record = parse_memory_record(payload)
        except MemoryValidationError:
            _log_skipped(scope, "invalid_record")
            return None

        if isinstance(record, MemoryRecordV2):
            try:
                ensure_record_path(record, Path(root_relative_path))
            except UnsafeMemoryPath:
                _log_skipped(scope, "path_mismatch")
                return None

        return StoredMemory(
            record=record,
            scope=scope,
            relative_path=root_relative_path,
            fingerprint=hashlib.sha256(raw_record).hexdigest(),
        )

    def discover(self, scope: MemoryScope) -> list[StoredMemory]:
        scope_path = scope_directory(self.memory_root, scope)
        if not scope_path.exists():
            return []
        if scope_path.is_symlink():
            _log_skipped(scope, "symlink")
            return []
        if not scope_path.is_dir():
            raise MemorySourceUnavailable

        return [
            stored
            for path in self._discover_candidates(scope_path, scope)
            if (stored := self._load(path, scope, scope_path)) is not None
        ]

    def get(
        self,
        reference: MemoryReference | LegacyMemoryReference,
    ) -> StoredMemory:
        if isinstance(reference, LegacyMemoryReference):
            matches = [
                stored
                for stored in self.discover(reference.scope)
                if isinstance(stored.record, LegacyMemoryRecordV1)
                and stored.record.id == reference.id
            ]
            if not matches:
                raise MemoryNotFound
            if len(matches) > 1:
                raise AmbiguousMemoryReference
            return matches[0]

        relative_path = relative_path_for_reference(reference)
        path = self.memory_root / relative_path
        scope_path = scope_directory(self.memory_root, reference.scope)
        self._reject_symlink_components(scope_path, path)
        if not path.exists() or not path.is_file():
            raise MemoryNotFound
        stored = self._load(path, reference.scope, scope_path)
        if stored is None or not isinstance(stored.record, MemoryRecordV2):
            raise MemoryNotFound
        return stored

    def create(self, record: MemoryRecordV2) -> StoredMemory:
        relative_path = relative_path_for_reference(
            MemoryReference(
                scope=record.scope,
                namespace_id=record.namespace.id,
                collection_id=(
                    record.collection.id if record.collection is not None else None
                ),
                id=record.id,
            )
        )
        path = self.memory_root / relative_path
        payload = self._serialize(record)

        with self._mutation_lock:
            self._ensure_private_directories(path.parent)
            scope_path = scope_directory(self.memory_root, record.scope)
            self._reject_symlink_components(scope_path, path)
            if path.is_symlink():
                raise UnsafeMemoryPath
            temporary = self._write_temp(path, payload)
            try:
                try:
                    os.link(temporary, path)
                except FileExistsError as error:
                    raise WriteConflict from error
                except OSError as error:
                    raise MemorySourceUnavailable from error
                self._sync_directory(path.parent)
            finally:
                temporary.unlink(missing_ok=True)
            return self.get(
                MemoryReference(
                    scope=record.scope,
                    namespace_id=record.namespace.id,
                    collection_id=(
                        record.collection.id if record.collection is not None else None
                    ),
                    id=record.id,
                )
            )

    def replace(
        self,
        record: MemoryRecordV2,
        *,
        expected_revision: int,
    ) -> StoredMemory:
        reference = MemoryReference(
            scope=record.scope,
            namespace_id=record.namespace.id,
            collection_id=(
                record.collection.id if record.collection is not None else None
            ),
            id=record.id,
        )
        path = self.memory_root / relative_path_for_reference(reference)
        payload = self._serialize(record)

        with self._mutation_lock:
            current = self.get(reference)
            assert isinstance(current.record, MemoryRecordV2)
            if current.record.lifecycle.revision != expected_revision:
                raise RevisionConflict
            if record.lifecycle.revision != expected_revision + 1:
                raise RevisionConflict
            immutable_current = (
                current.record.id,
                current.record.scope,
                current.record.namespace.kind,
                current.record.namespace.id,
                current.record.collection.id if current.record.collection else None,
                current.record.kind,
                current.record.language,
                current.record.provenance,
                current.record.created_at,
            )
            immutable_replacement = (
                record.id,
                record.scope,
                record.namespace.kind,
                record.namespace.id,
                record.collection.id if record.collection else None,
                record.kind,
                record.language,
                record.provenance,
                record.created_at,
            )
            if immutable_current != immutable_replacement:
                raise WriteConflict

            temporary = self._write_temp(path, payload)
            try:
                if self._fingerprint(path) != current.fingerprint:
                    raise WriteConflict
                try:
                    os.replace(temporary, path)
                except OSError as error:
                    raise MemorySourceUnavailable from error
                self._sync_directory(path.parent)
            finally:
                temporary.unlink(missing_ok=True)
            return self.get(reference)

    def delete(
        self,
        reference: MemoryReference,
        *,
        expected_revision: int,
    ) -> None:
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
            stored = self.get(reference)
            if not isinstance(stored.record, MemoryRecordV2):
                raise MemoryValidationError(
                    "invalid_reference",
                    "reference",
                    "reference does not identify a version-2 memory",
                )
            if stored.record.lifecycle.revision != expected_revision:
                raise RevisionConflict
            if stored.record.lifecycle.state is not LifecycleState.ARCHIVED:
                raise MemoryNotArchived

            path = self.memory_root / stored.relative_path
            scope_path = scope_directory(self.memory_root, reference.scope)
            self._reject_symlink_components(scope_path, path)
            try:
                fingerprint = self._fingerprint(path)
            except MemorySourceUnavailable as error:
                raise WriteConflict from error
            if fingerprint != stored.fingerprint:
                raise WriteConflict
            try:
                path.unlink()
            except FileNotFoundError as error:
                raise WriteConflict from error
            except OSError as error:
                raise MemorySourceUnavailable from error
            try:
                self._sync_directory(path.parent)
            except Exception as error:
                raise DeletionOutcomeUncertain from error

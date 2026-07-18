from pathlib import Path

from mnemosyne.memory.errors import UnsafeMemoryPath
from mnemosyne.memory.normalization import (
    normalize_identifier,
    normalize_memory_id,
)
from mnemosyne.memory.records import MemoryRecordV2, MemoryReference
from mnemosyne.memory.scopes import MemoryScope, get_scope_definition


def scope_directory(memory_root: Path, scope: MemoryScope) -> Path:
    return memory_root / get_scope_definition(scope).directory


def _ensure_safe_relative_path(path: Path) -> None:
    if path.is_absolute() or ".." in path.parts:
        raise UnsafeMemoryPath


def relative_path_for_reference(reference: MemoryReference) -> Path:
    namespace_id = normalize_identifier(
        reference.namespace_id,
        field="namespace.id",
    )
    collection_id = (
        None
        if reference.collection_id is None
        else normalize_identifier(
            reference.collection_id,
            field="collection.id",
        )
    )
    memory_id = normalize_memory_id(reference.id)
    path = Path(get_scope_definition(reference.scope).directory) / namespace_id
    if collection_id is not None:
        path /= collection_id
    path /= f"{memory_id}.json"
    _ensure_safe_relative_path(path)
    return path


def relative_path_for_record(record: MemoryRecordV2) -> Path:
    return relative_path_for_reference(
        MemoryReference(
            scope=record.scope,
            namespace_id=record.namespace.id,
            collection_id=(
                record.collection.id if record.collection is not None else None
            ),
            id=record.id,
        )
    )


def ensure_record_path(record: MemoryRecordV2, relative_path: Path) -> None:
    _ensure_safe_relative_path(relative_path)
    if relative_path != relative_path_for_record(record):
        raise UnsafeMemoryPath

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
import uuid
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from mymcp.memory.errors import (
    InvalidMemoryListCursor,
    MemoryValidationError,
    StaleMemoryListCursor,
)
from mymcp.memory.normalization import normalize_identifier
from mymcp.memory.records import LegacyMemoryRecordV1, MemoryRecordV2
from mymcp.memory.scopes import MemoryScope, parse_scope

if TYPE_CHECKING:
    from mymcp.memory.store import StoredMemory


DEFAULT_MEMORY_LIST_PAGE_SIZE = 50
MIN_MEMORY_LIST_PAGE_SIZE = 1
MAX_MEMORY_LIST_PAGE_SIZE = 100
MAX_MEMORY_LIST_CURSOR_LENGTH = 4_096
_CURSOR_VERSION = 1
_DIGEST_LENGTH = 64


class CollectionSelectionMode(StrEnum):
    ALL = "all"
    COLLECTIONLESS = "collectionless"
    EXACT = "exact"


class MemoryInspectability(StrEnum):
    EXACT = "exact"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class MemoryCollectionSelector:
    mode: CollectionSelectionMode
    id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.mode, CollectionSelectionMode):
            raise MemoryValidationError(
                "invalid_collection",
                "collection.id",
                "invalid collection.id",
            )
        if self.mode is CollectionSelectionMode.EXACT:
            normalized_id = normalize_identifier(self.id, field="collection.id")
            object.__setattr__(self, "id", normalized_id)
        elif self.id is not None:
            raise MemoryValidationError(
                "invalid_collection",
                "collection.id",
                "invalid collection.id",
            )

    @classmethod
    def all(cls) -> MemoryCollectionSelector:
        return cls(mode=CollectionSelectionMode.ALL)

    @classmethod
    def collectionless(cls) -> MemoryCollectionSelector:
        return cls(mode=CollectionSelectionMode.COLLECTIONLESS)

    @classmethod
    def exact(cls, collection_id: object) -> MemoryCollectionSelector:
        return cls(mode=CollectionSelectionMode.EXACT, id=collection_id)


@dataclass(frozen=True)
class MemoryListSelector:
    scope: MemoryScope
    namespace_id: str | None = None
    collection: MemoryCollectionSelector = field(
        default_factory=MemoryCollectionSelector.all
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "scope", parse_scope(self.scope))
        if self.namespace_id is not None:
            object.__setattr__(
                self,
                "namespace_id",
                normalize_identifier(self.namespace_id, field="namespace.id"),
            )
        if not isinstance(self.collection, MemoryCollectionSelector):
            raise MemoryValidationError(
                "invalid_collection",
                "collection.id",
                "invalid collection.id",
            )
        if (
            self.namespace_id is None
            and self.collection.mode is not CollectionSelectionMode.ALL
        ):
            raise MemoryValidationError(
                "invalid_collection",
                "collection.id",
                "collection selection requires namespace.id",
            )


@dataclass(frozen=True)
class MemoryListItem:
    memory: StoredMemory
    inspectability: MemoryInspectability


@dataclass(frozen=True)
class MemoryListPage:
    number: int
    count: int
    total_count: int
    total_pages: int
    truncated: bool
    next_cursor: str | None


@dataclass(frozen=True)
class MemoryListResult:
    memories: tuple[MemoryListItem, ...]
    page: MemoryListPage


@dataclass(frozen=True)
class MemoryListCursorPosition:
    offset: int
    page_size: int
    snapshot_digest: str


def select_listable_memories(
    memories: Sequence[StoredMemory],
    selector: MemoryListSelector,
) -> list[StoredMemory]:
    selected: list[StoredMemory] = []
    for memory in memories:
        if memory.scope is not selector.scope:
            continue
        record = memory.record
        if selector.namespace_id is None:
            selected.append(memory)
            continue
        if isinstance(record, LegacyMemoryRecordV1):
            continue
        assert isinstance(record, MemoryRecordV2)
        if record.namespace.id != selector.namespace_id:
            continue
        if selector.collection.mode is CollectionSelectionMode.COLLECTIONLESS:
            if record.collection is not None:
                continue
        elif selector.collection.mode is CollectionSelectionMode.EXACT:
            if (
                record.collection is None
                or record.collection.id != selector.collection.id
            ):
                continue
        selected.append(memory)
    return selected


def memory_list_order_key(memory: StoredMemory) -> tuple[object, ...]:
    record = memory.record
    if isinstance(record, LegacyMemoryRecordV1):
        return (1, record.id, memory.scope_relative_path)
    collection_present = 0 if record.collection is None else 1
    collection_id = record.collection.id if record.collection is not None else ""
    return (
        2,
        record.namespace.id,
        collection_present,
        collection_id,
        record.id,
    )


def order_listable_memories(
    memories: Sequence[StoredMemory],
) -> list[StoredMemory]:
    return sorted(memories, key=memory_list_order_key)


def build_memory_list_items(
    memories: Sequence[StoredMemory],
) -> tuple[MemoryListItem, ...]:
    legacy_counts = Counter(
        memory.record.id
        for memory in memories
        if isinstance(memory.record, LegacyMemoryRecordV1)
    )
    return tuple(
        MemoryListItem(
            memory=memory,
            inspectability=(
                MemoryInspectability.AMBIGUOUS
                if isinstance(memory.record, LegacyMemoryRecordV1)
                and legacy_counts[memory.record.id] > 1
                else MemoryInspectability.EXACT
            ),
        )
        for memory in memories
    )


def validate_memory_list_page_size(value: object | None) -> int:
    if value is None:
        return DEFAULT_MEMORY_LIST_PAGE_SIZE
    if (
        type(value) is not int
        or value < MIN_MEMORY_LIST_PAGE_SIZE
        or value > MAX_MEMORY_LIST_PAGE_SIZE
    ):
        raise MemoryValidationError(
            "invalid_page_size",
            "page_size",
            "invalid page_size",
        )
    return value


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    try:
        raw = base64.b64decode(
            value + "=" * (-len(value) % 4),
            altchars=b"-_",
            validate=True,
        )
    except (ValueError, binascii.Error) as error:
        raise InvalidMemoryListCursor from error
    if _base64url_encode(raw) != value:
        raise InvalidMemoryListCursor
    return raw


def _is_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == _DIGEST_LENGTH
        and all(character in "0123456789abcdef" for character in value)
    )


class MemoryListCursorCodec:
    def __init__(self, *, key: bytes, instance_id: str) -> None:
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("cursor key must contain at least 32 bytes")
        if not isinstance(instance_id, str) or not 1 <= len(instance_id) <= 100:
            raise ValueError("invalid cursor instance")
        self._key = key
        self.instance_id = instance_id

    @classmethod
    def generate(cls) -> MemoryListCursorCodec:
        return cls(key=secrets.token_bytes(32), instance_id=uuid.uuid4().hex)

    def _digest(self, domain: bytes, value: object) -> str:
        return hmac.new(
            self._key,
            domain + _canonical_json(value),
            hashlib.sha256,
        ).hexdigest()

    def selector_digest(self, selector: MemoryListSelector) -> str:
        return self._digest(
            b"mnemosyne-memory-list-selector\x00",
            {
                "scope": selector.scope.value,
                "namespace_id": selector.namespace_id,
                "collection_mode": selector.collection.mode.value,
                "collection_id": selector.collection.id,
            },
        )

    def snapshot_digest(self, memories: Sequence[StoredMemory]) -> str:
        snapshot: list[object] = []
        for memory in memories:
            record = memory.record
            if isinstance(record, LegacyMemoryRecordV1):
                identity: object = [1, record.id]
            else:
                identity = [
                    2,
                    record.namespace.id,
                    record.collection.id if record.collection is not None else None,
                    record.id,
                ]
            snapshot.append(
                [identity, memory.relative_path, memory.fingerprint]
            )
        return self._digest(b"mnemosyne-memory-list-snapshot\x00", snapshot)

    def encode(
        self,
        selector: MemoryListSelector,
        *,
        snapshot_digest: str,
        offset: int,
        page_size: int,
    ) -> str:
        payload = _canonical_json(
            {
                "v": _CURSOR_VERSION,
                "p": self.instance_id,
                "s": self.selector_digest(selector),
                "d": snapshot_digest,
                "o": offset,
                "z": page_size,
            }
        )
        signature = hmac.new(
            self._key,
            b"mnemosyne-memory-list-cursor\x00" + payload,
            hashlib.sha256,
        ).digest()
        return f"{_base64url_encode(payload)}.{_base64url_encode(signature)}"

    def decode(
        self,
        cursor: object,
        selector: MemoryListSelector,
    ) -> MemoryListCursorPosition:
        if (
            not isinstance(cursor, str)
            or not cursor
            or len(cursor) > MAX_MEMORY_LIST_CURSOR_LENGTH
        ):
            raise InvalidMemoryListCursor
        parts = cursor.split(".")
        if len(parts) != 2 or not all(parts):
            raise InvalidMemoryListCursor
        payload = _base64url_decode(parts[0])
        supplied_signature = _base64url_decode(parts[1])
        try:
            decoded = json.loads(payload.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise InvalidMemoryListCursor from error
        if not isinstance(decoded, dict) or set(decoded) != {
            "v",
            "p",
            "s",
            "d",
            "o",
            "z",
        }:
            raise InvalidMemoryListCursor
        version = decoded["v"]
        process = decoded["p"]
        selector_digest = decoded["s"]
        snapshot_digest = decoded["d"]
        offset = decoded["o"]
        page_size = decoded["z"]
        if (
            type(version) is not int
            or version != _CURSOR_VERSION
            or not isinstance(process, str)
            or not 1 <= len(process) <= 100
            or not _is_digest(selector_digest)
            or not _is_digest(snapshot_digest)
            or type(offset) is not int
            or offset < 1
            or type(page_size) is not int
            or not MIN_MEMORY_LIST_PAGE_SIZE
            <= page_size
            <= MAX_MEMORY_LIST_PAGE_SIZE
            or offset % page_size != 0
        ):
            raise InvalidMemoryListCursor
        if process != self.instance_id:
            raise StaleMemoryListCursor
        expected_signature = hmac.new(
            self._key,
            b"mnemosyne-memory-list-cursor\x00" + payload,
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise InvalidMemoryListCursor
        if not hmac.compare_digest(
            selector_digest,
            self.selector_digest(selector),
        ):
            raise InvalidMemoryListCursor
        return MemoryListCursorPosition(
            offset=offset,
            page_size=page_size,
            snapshot_digest=snapshot_digest,
        )


_PROCESS_MEMORY_LIST_CURSOR_CODEC = MemoryListCursorCodec.generate()

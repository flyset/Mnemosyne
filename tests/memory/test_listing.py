import json
from dataclasses import replace
from pathlib import Path

import pytest

from mnemosyne.memory.errors import (
    InvalidMemoryListCursor,
    MemoryValidationError,
    StaleMemoryListCursor,
)
from mnemosyne.memory.listing import (
    MemoryInspectability,
    MemoryCollectionSelector,
    MemoryListCursorCodec,
    MemoryListSelector,
    select_listable_memories,
)
from mnemosyne.memory.records import (
    LegacyMemoryRecordV1,
    MemoryRecordV2,
    parse_memory_record,
)
from mnemosyne.memory.scopes import MemoryScope
from mnemosyne.memory.service import MemoryService
from mnemosyne.memory.store import FilesystemMemoryStore, StoredMemory


def _legacy(
    record_id: str,
    *,
    scope: MemoryScope = MemoryScope.PREFERENCE,
    relative_path: str | None = None,
) -> StoredMemory:
    return StoredMemory(
        record=LegacyMemoryRecordV1(
            id=record_id,
            title=None,
            content="Legacy memory",
            tags=(),
        ),
        scope=scope,
        relative_path=relative_path or f"{scope.value}/{record_id}.json",
        fingerprint=f"fingerprint-{relative_path or record_id}",
    )


def _canonical(
    record_id_suffix: int,
    *,
    namespace_id: str = "leisure",
    collection_id: str | None = None,
    state: str = "active",
) -> StoredMemory:
    record_id = f"mem_{record_id_suffix:032x}"
    record = parse_memory_record(
        {
            "schema_version": 2,
            "id": record_id,
            "scope": "preference",
            "namespace": {
                "kind": "domain",
                "id": namespace_id,
                "label": None,
            },
            "collection": (
                None
                if collection_id is None
                else {"id": collection_id, "label": None}
            ),
            "kind": "preference",
            "language": "en",
            "title": None,
            "content": "Canonical memory",
            "tags": [],
            "provenance": {
                "origin": "explicit_user_statement",
                "recorded_via": "memory_remember",
            },
            "lifecycle": {"state": state, "revision": 1},
            "created_at": "2026-07-19T12:00:00Z",
            "updated_at": "2026-07-19T12:00:00Z",
        }
    )
    assert isinstance(record, MemoryRecordV2)
    collection_path = f"/{collection_id}" if collection_id is not None else ""
    return StoredMemory(
        record=record,
        scope=MemoryScope.PREFERENCE,
        relative_path=(
            f"preference/{namespace_id}{collection_path}/{record_id}.json"
        ),
        fingerprint=f"fingerprint-{record_id}",
    )


def _ids(memories: list[StoredMemory]) -> list[str]:
    return [memory.record.id for memory in memories]


def _result_ids(result: object) -> list[str]:
    return [item.memory.record.id for item in result.memories]


def _service_with_memories(
    tmp_path: Path,
    memories: list[StoredMemory],
    *,
    codec: MemoryListCursorCodec | None = None,
) -> MemoryService:
    store = FilesystemMemoryStore(tmp_path)
    store.discover_for_list = lambda selector: list(memories)
    return MemoryService(store, list_cursor_codec=codec)


def test_scope_listing_includes_legacy_active_and_archived_without_recall_cap() -> None:
    preferences = [_legacy(f"legacy-{index}") for index in range(6)]
    active = _canonical(1)
    archived = _canonical(2, state="archived")
    another_scope = _legacy("project-memory", scope=MemoryScope.PROJECT)

    selected = select_listable_memories(
        [*preferences, active, archived, another_scope],
        MemoryListSelector(scope=MemoryScope.PREFERENCE),
    )

    assert _ids(selected) == [
        "legacy-0",
        "legacy-1",
        "legacy-2",
        "legacy-3",
        "legacy-4",
        "legacy-5",
        active.record.id,
        archived.record.id,
    ]


def test_namespace_listing_excludes_legacy_and_includes_all_collection_states() -> None:
    collectionless = _canonical(1)
    weekends = _canonical(2, collection_id="weekends")
    favorites = _canonical(3, collection_id="favorites")
    another_namespace = _canonical(4, namespace_id="food")

    selected = select_listable_memories(
        [_legacy("legacy"), collectionless, weekends, favorites, another_namespace],
        MemoryListSelector(
            scope=MemoryScope.PREFERENCE,
            namespace_id="leisure",
        ),
    )

    assert _ids(selected) == [
        collectionless.record.id,
        weekends.record.id,
        favorites.record.id,
    ]


def test_collectionless_and_exact_collection_selectors_are_distinct() -> None:
    collectionless = _canonical(1)
    weekends = _canonical(2, collection_id="weekends")
    favorites = _canonical(3, collection_id="favorites")
    memories = [collectionless, weekends, favorites]

    without_collection = select_listable_memories(
        memories,
        MemoryListSelector(
            scope=MemoryScope.PREFERENCE,
            namespace_id="leisure",
            collection=MemoryCollectionSelector.collectionless(),
        ),
    )
    exact_collection = select_listable_memories(
        memories,
        MemoryListSelector(
            scope=MemoryScope.PREFERENCE,
            namespace_id="leisure",
            collection=MemoryCollectionSelector.exact("weekends"),
        ),
    )

    assert _ids(without_collection) == [collectionless.record.id]
    assert _ids(exact_collection) == [weekends.record.id]


def test_selector_rejects_unsafe_or_incoherent_container_dimensions() -> None:
    with pytest.raises(MemoryValidationError) as missing_namespace:
        MemoryListSelector(
            scope=MemoryScope.PREFERENCE,
            collection=MemoryCollectionSelector.collectionless(),
        )
    with pytest.raises(MemoryValidationError) as unsafe_namespace:
        MemoryListSelector(
            scope=MemoryScope.PREFERENCE,
            namespace_id="../unsafe",
        )
    with pytest.raises(MemoryValidationError) as unsafe_collection:
        MemoryCollectionSelector.exact("../unsafe")

    assert missing_namespace.value.code == "invalid_collection"
    assert missing_namespace.value.field == "collection.id"
    assert unsafe_namespace.value.code == "invalid_namespace"
    assert unsafe_namespace.value.field == "namespace.id"
    assert unsafe_collection.value.code == "invalid_collection"
    assert unsafe_collection.value.field == "collection.id"


def test_service_listing_discovers_only_the_selected_scope_and_never_writes(
    tmp_path: Path,
) -> None:
    store = FilesystemMemoryStore(tmp_path)
    discovered_selectors: list[MemoryListSelector] = []
    expected = [_legacy("one"), _legacy("two")]

    def discover(selector: MemoryListSelector) -> list[StoredMemory]:
        discovered_selectors.append(selector)
        return expected

    store.discover_for_list = discover
    store.create = lambda record: pytest.fail("listing must not create")
    store.replace = lambda record, expected_revision: pytest.fail(
        "listing must not replace"
    )
    store.delete = lambda reference, expected_revision: pytest.fail(
        "listing must not delete"
    )

    selector = MemoryListSelector(scope=MemoryScope.PREFERENCE)
    result = MemoryService(store).list_memories(selector)

    assert [item.memory for item in result.memories] == expected
    assert discovered_selectors == [selector]


def test_service_listing_orders_mixed_records_by_version_and_public_identity(
    tmp_path: Path,
) -> None:
    duplicate_b = _legacy(
        "duplicate",
        relative_path="preference/z/duplicate.json",
    )
    duplicate_a = _legacy(
        "duplicate",
        relative_path="preference/a/duplicate.json",
    )
    unique = _legacy("alpha")
    collectionless = _canonical(4, namespace_id="leisure")
    favorites = _canonical(3, namespace_id="leisure", collection_id="favorites")
    weekends_later = _canonical(
        2,
        namespace_id="leisure",
        collection_id="weekends",
    )
    weekends_earlier = _canonical(
        1,
        namespace_id="leisure",
        collection_id="weekends",
    )
    food = _canonical(5, namespace_id="food")
    service = _service_with_memories(
        tmp_path,
        [
            weekends_later,
            duplicate_b,
            favorites,
            food,
            duplicate_a,
            collectionless,
            unique,
            weekends_earlier,
        ],
    )

    result = service.list_memories(
        MemoryListSelector(scope=MemoryScope.PREFERENCE),
        page_size=100,
    )

    assert [item.memory.relative_path for item in result.memories] == [
        unique.relative_path,
        duplicate_a.relative_path,
        duplicate_b.relative_path,
        food.relative_path,
        collectionless.relative_path,
        favorites.relative_path,
        weekends_earlier.relative_path,
        weekends_later.relative_path,
    ]
    assert [item.inspectability for item in result.memories] == [
        MemoryInspectability.EXACT,
        MemoryInspectability.AMBIGUOUS,
        MemoryInspectability.AMBIGUOUS,
        MemoryInspectability.EXACT,
        MemoryInspectability.EXACT,
        MemoryInspectability.EXACT,
        MemoryInspectability.EXACT,
        MemoryInspectability.EXACT,
    ]


def test_listing_returns_explicit_empty_page_metadata(tmp_path: Path) -> None:
    result = _service_with_memories(tmp_path, []).list_memories(
        MemoryListSelector(scope=MemoryScope.PREFERENCE)
    )

    assert result.memories == ()
    assert result.page.number == 1
    assert result.page.count == 0
    assert result.page.total_count == 0
    assert result.page.total_pages == 0
    assert result.page.truncated is False
    assert result.page.next_cursor is None


def test_listing_uses_default_and_maximum_page_sizes_with_exact_boundaries(
    tmp_path: Path,
) -> None:
    memories = [_legacy(f"memory-{index:03}") for index in range(51)]
    selector = MemoryListSelector(scope=MemoryScope.PREFERENCE)
    service = _service_with_memories(tmp_path, memories)

    default_page = service.list_memories(selector)
    maximum_page = service.list_memories(selector, page_size=100)
    exact_page = _service_with_memories(tmp_path, memories[:2]).list_memories(
        selector,
        page_size=2,
    )

    assert default_page.page.count == 50
    assert default_page.page.total_pages == 2
    assert default_page.page.truncated is True
    assert default_page.page.next_cursor is not None
    assert maximum_page.page.count == 51
    assert maximum_page.page.total_pages == 1
    assert maximum_page.page.truncated is False
    assert maximum_page.page.next_cursor is None
    assert exact_page.page.count == 2
    assert exact_page.page.total_pages == 1
    assert exact_page.page.truncated is False
    assert exact_page.page.next_cursor is None


def test_listing_traverses_unchanged_pages_exactly_once_across_service_instances(
    tmp_path: Path,
) -> None:
    memories = [_legacy(f"memory-{index}") for index in range(5)]
    selector = MemoryListSelector(scope=MemoryScope.PREFERENCE)

    first = _service_with_memories(tmp_path, memories).list_memories(
        selector,
        page_size=2,
    )
    second = _service_with_memories(tmp_path, memories).list_memories(
        selector,
        cursor=first.page.next_cursor,
    )
    third = _service_with_memories(tmp_path, memories).list_memories(
        selector,
        cursor=second.page.next_cursor,
    )

    assert _result_ids(first) + _result_ids(second) + _result_ids(third) == [
        "memory-0",
        "memory-1",
        "memory-2",
        "memory-3",
        "memory-4",
    ]
    assert [page.page.number for page in (first, second, third)] == [1, 2, 3]
    assert [page.page.count for page in (first, second, third)] == [2, 2, 1]
    assert all(page.page.total_count == 5 for page in (first, second, third))
    assert all(page.page.total_pages == 3 for page in (first, second, third))
    assert [page.page.truncated for page in (first, second, third)] == [
        True,
        True,
        False,
    ]
    assert first.page.next_cursor is not None
    assert second.page.next_cursor is not None
    assert third.page.next_cursor is None


def test_duplicate_legacy_inspectability_is_computed_before_page_slicing(
    tmp_path: Path,
) -> None:
    memories = [
        _legacy("duplicate", relative_path="preference/a.json"),
        _legacy("duplicate", relative_path="preference/b.json"),
    ]
    selector = MemoryListSelector(scope=MemoryScope.PREFERENCE)
    service = _service_with_memories(tmp_path, memories)

    first = service.list_memories(selector, page_size=1)
    second = service.list_memories(selector, cursor=first.page.next_cursor)

    assert first.memories[0].inspectability is MemoryInspectability.AMBIGUOUS
    assert second.memories[0].inspectability is MemoryInspectability.AMBIGUOUS


@pytest.mark.parametrize(
    "page_size",
    [True, False, 0, -1, 101, 1.0, "1"],
)
def test_listing_rejects_invalid_page_size_before_discovery(
    tmp_path: Path,
    page_size: object,
) -> None:
    store = FilesystemMemoryStore(tmp_path)
    store.discover_for_list = lambda selector: pytest.fail("discovery must not run")

    with pytest.raises(MemoryValidationError) as caught:
        MemoryService(store).list_memories(
            MemoryListSelector(scope=MemoryScope.PREFERENCE),
            page_size=page_size,
        )

    assert caught.value.code == "invalid_page_size"
    assert caught.value.field == "page_size"


def test_listing_cursor_is_bound_to_selector_and_rejects_a_repeated_page_size(
    tmp_path: Path,
) -> None:
    memories = [_legacy("one"), _legacy("two")]
    service = _service_with_memories(tmp_path, memories)
    preference = MemoryListSelector(scope=MemoryScope.PREFERENCE)
    cursor = service.list_memories(preference, page_size=1).page.next_cursor

    with pytest.raises(InvalidMemoryListCursor):
        service.list_memories(
            MemoryListSelector(scope=MemoryScope.PROJECT),
            cursor=cursor,
        )
    with pytest.raises(InvalidMemoryListCursor):
        service.list_memories(preference, page_size=1, cursor=cursor)


@pytest.mark.parametrize("cursor", ["", "not-a-cursor", "a" * 4_097])
def test_listing_rejects_malformed_cursor_before_discovery(
    tmp_path: Path,
    cursor: str,
) -> None:
    store = FilesystemMemoryStore(tmp_path)
    store.discover_for_list = lambda selector: pytest.fail("discovery must not run")

    with pytest.raises(InvalidMemoryListCursor):
        MemoryService(store).list_memories(
            MemoryListSelector(scope=MemoryScope.PREFERENCE),
            cursor=cursor,
        )


def test_listing_rejects_current_process_cursor_tampering(tmp_path: Path) -> None:
    memories = [_legacy("one"), _legacy("two")]
    service = _service_with_memories(tmp_path, memories)
    selector = MemoryListSelector(scope=MemoryScope.PREFERENCE)
    cursor = service.list_memories(selector, page_size=1).page.next_cursor
    assert cursor is not None

    with pytest.raises(InvalidMemoryListCursor):
        service.list_memories(selector, cursor=f"{cursor}x")


def test_listing_rejects_foreign_process_cursor_as_stale(tmp_path: Path) -> None:
    memories = [_legacy("one"), _legacy("two")]
    selector = MemoryListSelector(scope=MemoryScope.PREFERENCE)
    first_codec = MemoryListCursorCodec(key=b"a" * 32, instance_id="process-a")
    second_codec = MemoryListCursorCodec(key=b"b" * 32, instance_id="process-b")
    cursor = _service_with_memories(
        tmp_path,
        memories,
        codec=first_codec,
    ).list_memories(selector, page_size=1).page.next_cursor

    with pytest.raises(StaleMemoryListCursor):
        _service_with_memories(
            tmp_path,
            memories,
            codec=second_codec,
        ).list_memories(selector, cursor=cursor)


@pytest.mark.parametrize("change", ["addition", "removal", "rewrite"])
def test_listing_rejects_changed_selected_snapshot(
    tmp_path: Path,
    change: str,
) -> None:
    memories = [_legacy("one"), _legacy("two"), _legacy("three")]
    selector = MemoryListSelector(scope=MemoryScope.PREFERENCE)
    service = _service_with_memories(tmp_path, memories)
    cursor = service.list_memories(selector, page_size=1).page.next_cursor

    if change == "addition":
        memories.append(_legacy("four"))
    elif change == "removal":
        memories.pop()
    else:
        memories[0] = replace(memories[0], fingerprint="rewritten")

    with pytest.raises(StaleMemoryListCursor):
        service.list_memories(selector, cursor=cursor)


def test_listing_ignores_changes_outside_the_selected_snapshot(
    tmp_path: Path,
) -> None:
    preference = tmp_path / "preference"
    preference.mkdir()
    for record_id in ("one", "two"):
        (preference / f"{record_id}.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "id": record_id,
                    "content": "Selected memory",
                }
            ),
            encoding="utf-8",
        )
    selector = MemoryListSelector(scope=MemoryScope.PREFERENCE)
    cursor = MemoryService(FilesystemMemoryStore(tmp_path)).list_memories(
        selector,
        page_size=1,
    ).page.next_cursor

    project = tmp_path / "project"
    project.mkdir()
    (project / "outside.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "outside",
                "content": "Unrelated memory",
            }
        ),
        encoding="utf-8",
    )
    continued = MemoryService(FilesystemMemoryStore(tmp_path)).list_memories(
        selector,
        cursor=cursor,
    )

    assert _result_ids(continued) == ["two"]

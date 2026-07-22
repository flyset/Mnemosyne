import json
import logging
import os
from pathlib import Path

import pytest

from mymcp.memory.errors import (
    AmbiguousMemoryReference,
    CandidateLimitExceeded,
    MemoryNotFound,
    MemorySourceUnavailable,
    UnsafeMemoryPath,
)
from mymcp.memory.listing import MemoryCollectionSelector, MemoryListSelector
from mymcp.memory.records import (
    LegacyMemoryRecordV1,
    LegacyMemoryReference,
    LifecycleState,
    MemoryRecordV2,
    MemoryReference,
)
from mymcp.memory.scopes import MemoryScope
from mymcp.memory.store import FilesystemMemoryStore


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _v1(record_id: str, content: str = "Legacy memory") -> dict[str, object]:
    return {
        "schema_version": 1,
        "id": record_id,
        "content": content,
        "tags": ["legacy"],
    }


def _v2(
    record_id: str = "mem_0123456789abcdef0123456789abcdef",
    *,
    state: str = "active",
    namespace_id: str = "mnemosyne",
    collection_id: str | None = "decisions",
) -> dict[str, object]:
    return {
        "schema_version": 2,
        "id": record_id,
        "scope": "project",
        "namespace": {
            "kind": "project",
            "id": namespace_id,
            "label": "Mnemosyne",
        },
        "collection": (
            None
            if collection_id is None
            else {"id": collection_id, "label": "Decisions"}
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
        "lifecycle": {"state": state, "revision": 1},
        "created_at": "2026-07-18T12:00:00Z",
        "updated_at": "2026-07-18T12:00:00Z",
    }


def test_store_discovers_sorted_scope_isolated_v1_and_v2_records(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "project" / "legacy" / "old.json", _v1("legacy"))
    _write(
        tmp_path
        / "project"
        / "mnemosyne"
        / "decisions"
        / "mem_0123456789abcdef0123456789abcdef.json",
        _v2(),
    )
    _write(tmp_path / "self" / "ignored.json", _v1("ignored"))

    stored = FilesystemMemoryStore(tmp_path).discover(MemoryScope.PROJECT)

    assert [memory.relative_path for memory in stored] == [
        "project/legacy/old.json",
        "project/mnemosyne/decisions/mem_0123456789abcdef0123456789abcdef.json",
    ]
    assert isinstance(stored[0].record, LegacyMemoryRecordV1)
    assert isinstance(stored[1].record, MemoryRecordV2)


def test_store_returns_empty_for_a_missing_scope_directory(tmp_path: Path) -> None:
    assert FilesystemMemoryStore(tmp_path).discover(MemoryScope.KNOWLEDGE) == []


def test_store_keeps_archived_records_available_for_exact_inspection(
    tmp_path: Path,
) -> None:
    path = (
        tmp_path
        / "project"
        / "mnemosyne"
        / "decisions"
        / "mem_0123456789abcdef0123456789abcdef.json"
    )
    _write(path, _v2(state="archived"))

    stored = FilesystemMemoryStore(tmp_path).discover(MemoryScope.PROJECT)

    assert len(stored) == 1
    assert isinstance(stored[0].record, MemoryRecordV2)
    assert stored[0].record.lifecycle.state is LifecycleState.ARCHIVED


def test_store_skips_invalid_and_path_mismatched_records_with_safe_warnings(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    scope = tmp_path / "project"
    _write(scope / "bad-json.json", "not-json")
    (scope / "bad-json.json").write_text("{", encoding="utf-8")
    _write(scope / "invalid.json", {"schema_version": 1})
    _write(scope / "wrong" / "record.json", _v2())
    caplog.set_level(logging.WARNING, logger="mymcp.memory.store")

    assert FilesystemMemoryStore(tmp_path).discover(MemoryScope.PROJECT) == []
    assert caplog.messages == [
        "skipped scope='project' reason='invalid_json'",
        "skipped scope='project' reason='invalid_record'",
        "skipped scope='project' reason='path_mismatch'",
    ]
    assert all(str(tmp_path) not in message for message in caplog.messages)
    assert all(".json" not in message for message in caplog.messages)


def test_store_skips_oversized_and_too_deep_sources(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    scope = tmp_path / "project"
    scope.mkdir()
    (scope / "oversized.json").write_bytes(b"x" * 65_537)
    _write(scope / "one" / "two" / "three" / "four" / "valid.json", _v1("valid"))
    _write(
        scope / "one" / "two" / "three" / "four" / "five" / "ignored.json",
        _v1("ignored"),
    )
    caplog.set_level(logging.WARNING, logger="mymcp.memory.store")

    stored = FilesystemMemoryStore(tmp_path).discover(MemoryScope.PROJECT)

    assert [memory.record.id for memory in stored] == ["valid"]
    assert caplog.messages == [
        "skipped scope='project' reason='too_deep'",
        "skipped scope='project' reason='oversized'",
    ]
    assert all("one/two" not in message for message in caplog.messages)
    assert all("oversized.json" not in message for message in caplog.messages)


def test_store_rejects_symlink_files_and_directories(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    scope = tmp_path / "project"
    scope.mkdir()
    outside_file = tmp_path / "outside.json"
    _write(outside_file, _v1("outside"))
    outside_directory = tmp_path / "outside"
    _write(outside_directory / "memory.json", _v1("outside-directory"))
    try:
        (scope / "linked-file.json").symlink_to(outside_file)
        (scope / "linked-directory").symlink_to(outside_directory, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")
    caplog.set_level(logging.WARNING, logger="mymcp.memory.store")

    assert FilesystemMemoryStore(tmp_path).discover(MemoryScope.PROJECT) == []
    assert caplog.messages == [
        "skipped scope='project' reason='symlink'",
        "skipped scope='project' reason='symlink'",
    ]
    assert all("linked-" not in message for message in caplog.messages)


def test_store_rejects_more_than_one_thousand_candidates(tmp_path: Path) -> None:
    scope = tmp_path / "project"
    scope.mkdir()
    for index in range(1_001):
        (scope / f"{index:04}.json").write_text("{}", encoding="utf-8")

    with pytest.raises(CandidateLimitExceeded):
        FilesystemMemoryStore(tmp_path).discover(MemoryScope.PROJECT)


def test_list_discovery_narrows_before_applying_the_candidate_bound(
    tmp_path: Path,
) -> None:
    target_id = "mem_0123456789abcdef0123456789abcdef"
    _write(
        tmp_path / "project" / "mnemosyne" / "decisions" / f"{target_id}.json",
        _v2(target_id),
    )
    overflow = tmp_path / "project" / "another-project" / "noise"
    overflow.mkdir(parents=True)
    for index in range(1_001):
        (overflow / f"{index:04}.json").write_text("{}", encoding="utf-8")

    selector = MemoryListSelector(
        scope=MemoryScope.PROJECT,
        namespace_id="mnemosyne",
        collection=MemoryCollectionSelector.exact("decisions"),
    )
    stored = FilesystemMemoryStore(tmp_path).discover_for_list(selector)

    assert [memory.record.id for memory in stored] == [target_id]


def test_namespace_list_discovery_includes_its_containers_and_ignores_other_namespace(
    tmp_path: Path,
) -> None:
    collectionless_id = "mem_11111111111111111111111111111111"
    collected_id = "mem_22222222222222222222222222222222"
    _write(
        tmp_path / "project" / "mnemosyne" / f"{collectionless_id}.json",
        _v2(collectionless_id, collection_id=None),
    )
    _write(
        tmp_path / "project" / "mnemosyne" / "decisions" / f"{collected_id}.json",
        _v2(collected_id),
    )
    _write(
        tmp_path / "project" / "mnemosyne" / "legacy.json",
        _v1("legacy"),
    )
    overflow = tmp_path / "project" / "another-project"
    overflow.mkdir(parents=True)
    for index in range(1_001):
        (overflow / f"{index:04}.json").write_text("{}", encoding="utf-8")

    stored = FilesystemMemoryStore(tmp_path).discover_for_list(
        MemoryListSelector(
            scope=MemoryScope.PROJECT,
            namespace_id="mnemosyne",
        )
    )

    assert {memory.record.id for memory in stored} == {
        collectionless_id,
        collected_id,
    }


def test_list_discovery_narrows_exact_and_collectionless_candidates(
    tmp_path: Path,
) -> None:
    collectionless_id = "mem_11111111111111111111111111111111"
    exact_id = "mem_22222222222222222222222222222222"
    _write(
        tmp_path / "project" / "mnemosyne" / f"{collectionless_id}.json",
        _v2(collectionless_id, collection_id=None),
    )
    _write(
        tmp_path / "project" / "mnemosyne" / "decisions" / f"{exact_id}.json",
        _v2(exact_id),
    )
    overflow = tmp_path / "project" / "mnemosyne" / "other"
    overflow.mkdir(parents=True)
    for index in range(1_001):
        (overflow / f"{index:04}.json").write_text("{}", encoding="utf-8")
    store = FilesystemMemoryStore(tmp_path)

    collectionless = store.discover_for_list(
        MemoryListSelector(
            scope=MemoryScope.PROJECT,
            namespace_id="mnemosyne",
            collection=MemoryCollectionSelector.collectionless(),
        )
    )
    exact = store.discover_for_list(
        MemoryListSelector(
            scope=MemoryScope.PROJECT,
            namespace_id="mnemosyne",
            collection=MemoryCollectionSelector.exact("decisions"),
        )
    )

    assert [memory.record.id for memory in collectionless] == [collectionless_id]
    assert [memory.record.id for memory in exact] == [exact_id]


def test_list_discovery_counts_only_the_selected_container_but_still_fails_closed(
    tmp_path: Path,
) -> None:
    selected = tmp_path / "project" / "mnemosyne" / "decisions"
    selected.mkdir(parents=True)
    for index in range(1_001):
        (selected / f"{index:04}.json").write_text("{}", encoding="utf-8")

    with pytest.raises(CandidateLimitExceeded):
        FilesystemMemoryStore(tmp_path).discover_for_list(
            MemoryListSelector(
                scope=MemoryScope.PROJECT,
                namespace_id="mnemosyne",
                collection=MemoryCollectionSelector.exact("decisions"),
            )
        )


def test_list_discovery_missing_container_is_empty_without_initialization(
    tmp_path: Path,
) -> None:
    memory_root = tmp_path / "missing-memory"

    stored = FilesystemMemoryStore(memory_root).discover_for_list(
        MemoryListSelector(
            scope=MemoryScope.PROJECT,
            namespace_id="mnemosyne",
            collection=MemoryCollectionSelector.exact("decisions"),
        )
    )

    assert stored == []
    assert not memory_root.exists()


def test_list_discovery_rejects_selected_symlink_or_non_directory(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    scope = tmp_path / "project"
    scope.mkdir()
    linked = scope / "linked"
    try:
        linked.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")
    store = FilesystemMemoryStore(tmp_path)

    with pytest.raises(UnsafeMemoryPath):
        store.discover_for_list(
            MemoryListSelector(
                scope=MemoryScope.PROJECT,
                namespace_id="linked",
            )
        )

    regular_file = scope / "regular"
    regular_file.write_text("not a directory", encoding="utf-8")
    with pytest.raises(MemorySourceUnavailable):
        store.discover_for_list(
            MemoryListSelector(
                scope=MemoryScope.PROJECT,
                namespace_id="regular",
            )
        )


def test_canonical_list_discovery_excludes_legacy_records_in_selected_container(
    tmp_path: Path,
) -> None:
    canonical_id = "mem_0123456789abcdef0123456789abcdef"
    container = tmp_path / "project" / "mnemosyne" / "decisions"
    _write(container / f"{canonical_id}.json", _v2(canonical_id))
    _write(container / "legacy.json", _v1("legacy"))
    (container / "invalid.json").write_text("{", encoding="utf-8")

    stored = FilesystemMemoryStore(tmp_path).discover_for_list(
        MemoryListSelector(
            scope=MemoryScope.PROJECT,
            namespace_id="mnemosyne",
            collection=MemoryCollectionSelector.exact("decisions"),
        )
    )

    assert [memory.record.id for memory in stored] == [canonical_id]


def test_store_gets_a_version_two_record_by_structured_reference(
    tmp_path: Path,
) -> None:
    path = (
        tmp_path
        / "project"
        / "mnemosyne"
        / "decisions"
        / "mem_0123456789abcdef0123456789abcdef.json"
    )
    _write(path, _v2())
    reference = MemoryReference(
        scope=MemoryScope.PROJECT,
        namespace_id="mnemosyne",
        collection_id="decisions",
        id="mem_0123456789abcdef0123456789abcdef",
    )

    stored = FilesystemMemoryStore(tmp_path).get(reference)

    assert isinstance(stored.record, MemoryRecordV2)
    assert stored.record.id == reference.id
    assert stored.relative_path == (
        "project/mnemosyne/decisions/"
        "mem_0123456789abcdef0123456789abcdef.json"
    )


def test_store_get_rejects_a_symlinked_parent_directory(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    _write(
        outside / "decisions" / "mem_0123456789abcdef0123456789abcdef.json",
        _v2(),
    )
    scope = tmp_path / "project"
    scope.mkdir()
    try:
        (scope / "mnemosyne").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")
    reference = MemoryReference(
        scope=MemoryScope.PROJECT,
        namespace_id="mnemosyne",
        collection_id="decisions",
        id="mem_0123456789abcdef0123456789abcdef",
    )

    with pytest.raises(UnsafeMemoryPath):
        FilesystemMemoryStore(tmp_path).get(reference)


def test_store_gets_a_unique_legacy_record_by_scope_and_id(tmp_path: Path) -> None:
    _write(tmp_path / "preference" / "leisure" / "rainy.json", _v1("rainy"))

    stored = FilesystemMemoryStore(tmp_path).get(
        LegacyMemoryReference(scope=MemoryScope.PREFERENCE, id="rainy")
    )

    assert isinstance(stored.record, LegacyMemoryRecordV1)
    assert stored.relative_path == "preference/leisure/rainy.json"


def test_store_rejects_ambiguous_legacy_ids(tmp_path: Path) -> None:
    _write(tmp_path / "preference" / "a.json", _v1("duplicate"))
    _write(tmp_path / "preference" / "nested" / "b.json", _v1("duplicate"))

    with pytest.raises(AmbiguousMemoryReference):
        FilesystemMemoryStore(tmp_path).get(
            LegacyMemoryReference(scope=MemoryScope.PREFERENCE, id="duplicate")
        )


@pytest.mark.parametrize(
    "reference",
    [
        MemoryReference(
            scope=MemoryScope.PROJECT,
            namespace_id="mnemosyne",
            collection_id="decisions",
            id="mem_0123456789abcdef0123456789abcdef",
        ),
        LegacyMemoryReference(scope=MemoryScope.PREFERENCE, id="missing"),
    ],
)
def test_store_reports_missing_references(tmp_path: Path, reference: object) -> None:
    with pytest.raises(MemoryNotFound):
        FilesystemMemoryStore(tmp_path).get(reference)


def test_store_reports_an_unreadable_scope_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scope = tmp_path / "project"
    scope.mkdir()
    original_scandir = os.scandir

    def fail_for_scope(path: object):
        if Path(path) == scope:
            raise PermissionError("denied")
        return original_scandir(path)

    monkeypatch.setattr(os, "scandir", fail_for_scope)

    with pytest.raises(MemorySourceUnavailable):
        FilesystemMemoryStore(tmp_path).discover(MemoryScope.PROJECT)

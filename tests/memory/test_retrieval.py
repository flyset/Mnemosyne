import json
from pathlib import Path

from mymcp.memory.records import (
    LegacyMemoryRecordV1,
    MemoryRecordV2,
    parse_memory_record,
)
from mymcp.memory.retrieval import MemoryMatch, rank_memories
from mymcp.memory.scopes import MemoryScope
from mymcp.memory.service import MemoryService
from mymcp.memory.store import FilesystemMemoryStore, StoredMemory


def _legacy(
    record_id: str,
    *,
    title: str | None = None,
    content: str = "Memory content",
    tags: tuple[str, ...] = (),
    relative_path: str | None = None,
) -> StoredMemory:
    return StoredMemory(
        record=LegacyMemoryRecordV1(
            id=record_id,
            title=title,
            content=content,
            tags=tags,
        ),
        scope=MemoryScope.PREFERENCE,
        relative_path=relative_path or f"preference/{record_id}.json",
        fingerprint="test",
    )


def _v2(*, state: str = "active") -> StoredMemory:
    record = parse_memory_record(
        {
            "schema_version": 2,
            "id": "mem_0123456789abcdef0123456789abcdef",
            "scope": "preference",
            "namespace": {
                "kind": "domain",
                "id": "leisure",
                "label": "Leisure",
            },
            "collection": None,
            "kind": "preference",
            "language": "en",
            "title": "Rainy plans",
            "content": "A rainy afternoon at the museum.",
            "tags": ["rainy-day", "leisure"],
            "provenance": {
                "origin": "explicit_user_statement",
                "recorded_via": "memory_remember",
            },
            "lifecycle": {"state": state, "revision": 1},
            "created_at": "2026-07-18T12:00:00Z",
            "updated_at": "2026-07-18T12:00:00Z",
        }
    )
    assert isinstance(record, MemoryRecordV2)
    return StoredMemory(
        record=record,
        scope=MemoryScope.PREFERENCE,
        relative_path=(
            "preference/leisure/"
            "mem_0123456789abcdef0123456789abcdef.json"
        ),
        fingerprint="test",
    )


def test_shared_ranking_applies_the_declared_field_weights() -> None:
    memory = _legacy(
        "rainy-weekend",
        title="Rainy plans",
        content="A rainy afternoon at the museum.",
        tags=("rainy-day", "leisure"),
        relative_path="preference/leisure/rainy.json",
    )

    assert rank_memories(
        [memory],
        "What rainy afternoon leisure museum?",
        ["LEISURE", "rainy-day", "absent"],
    ) == [
        MemoryMatch(
            memory=memory,
            score=18,
            matched_terms=("afternoon", "leisure", "museum", "rainy"),
            matched_tags=("leisure", "rainy-day"),
        )
    ]


def test_shared_ranking_casefolds_unicode_and_splits_path_punctuation() -> None:
    memory = _legacy(
        "cafe",
        title="CAFÉ choices",
        content="A quiet afternoon.",
        relative_path="preference/free_time/weekend-plan.json",
    )

    assert rank_memories(
        [memory],
        "What is the café free time weekend plan?",
        [],
    ) == [
        MemoryMatch(
            memory=memory,
            score=11,
            matched_terms=("café", "free", "plan", "time", "weekend"),
            matched_tags=(),
        )
    ]


def test_shared_ranking_removes_question_words_and_requires_positive_score() -> None:
    generic = _legacy("generic", content="The user is available.")

    assert rank_memories([generic], "What is the user?", []) == []


def test_shared_ranking_uses_record_tags_for_query_terms() -> None:
    memory = _legacy(
        "weekend",
        content="A saved preference.",
        tags=("rainy-day",),
    )

    assert rank_memories([memory], "rainy day", []) == [
        MemoryMatch(
            memory=memory,
            score=4,
            matched_terms=("day", "rainy"),
            matched_tags=(),
        )
    ]


def test_shared_ranking_breaks_ties_by_scope_relative_path_then_id() -> None:
    memories = [
        _legacy("z", content="Matched", relative_path="preference/z.json"),
        _legacy("b", content="Matched", relative_path="preference/same.json"),
        _legacy("a", content="Matched", relative_path="preference/same.json"),
    ]

    assert [
        match.memory.record.id
        for match in rank_memories(memories, "matched", [])
    ] == ["a", "b", "z"]


def test_shared_ranking_returns_only_five_results() -> None:
    memories = [
        _legacy(
            f"memory-{index}",
            content="Match",
            relative_path=f"preference/{index}.json",
        )
        for index in range(1, 8)
    ]

    matches = rank_memories(memories, "match", [])

    assert [match.memory.record.id for match in matches] == [
        "memory-1",
        "memory-2",
        "memory-3",
        "memory-4",
        "memory-5",
    ]


def test_shared_ranking_excludes_archived_version_two_records() -> None:
    assert rank_memories([_v2(state="archived")], "rainy", []) == []
    assert len(rank_memories([_v2(state="active")], "rainy", [])) == 1


def test_shared_ranking_does_not_treat_scope_directory_as_a_path_term() -> None:
    memory = _legacy(
        "neutral",
        content="Unrelated content",
        relative_path="preference/neutral.json",
    )

    assert rank_memories([memory], "preference", []) == []


def test_version_one_and_two_records_use_the_same_content_ranking() -> None:
    legacy = _legacy("legacy", content="A rainy afternoon.")
    current = _v2()

    matches = rank_memories([legacy, current], "afternoon", [])

    assert [(match.memory.record.id, match.score) for match in matches] == [
        ("legacy", 1),
        ("mem_0123456789abcdef0123456789abcdef", 1),
    ]


def test_memory_service_recall_is_scope_isolated_and_read_only(tmp_path: Path) -> None:
    preference = tmp_path / "preference" / "leisure" / "rainy.json"
    preference.parent.mkdir(parents=True)
    preference.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "rainy",
                "content": "Rainy leisure memory",
            }
        ),
        encoding="utf-8",
    )
    project = tmp_path / "project" / "rainy.json"
    project.parent.mkdir()
    project.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "project-rainy",
                "content": "Rainy project memory",
            }
        ),
        encoding="utf-8",
    )
    service = MemoryService(FilesystemMemoryStore(tmp_path))

    matches = service.recall(
        MemoryScope.PREFERENCE,
        "rainy",
        [],
    )

    assert [match.memory.record.id for match in matches] == ["rainy"]
    assert len(list(tmp_path.rglob("*.json"))) == 2

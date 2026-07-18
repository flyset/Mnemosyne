import json
import logging
from pathlib import Path

import pytest

from mnemosyne.mcp.tools.memory_recall.retrieval import (
    CandidateLimitExceeded,
    MemoryMatch,
    MemoryRecord,
    discover_records,
    rank_records,
)


def _write_record(path: Path, **overrides: object) -> None:
    record: dict[str, object] = {
        "schema_version": 1,
        "id": path.stem,
        "content": f"Memory from {path.stem}",
    }
    record.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record), encoding="utf-8")


def _memory(
    record_id: str,
    *,
    title: str | None = None,
    content: str = "Memory content",
    tags: tuple[str, ...] = (),
    relative_path: str | None = None,
) -> MemoryRecord:
    return MemoryRecord(
        id=record_id,
        title=title,
        content=content,
        tags=tags,
        relative_path=relative_path or f"{record_id}.json",
    )


def test_discover_records_reads_only_the_selected_scope_in_path_order(
    tmp_path: Path,
) -> None:
    _write_record(
        tmp_path / "preference" / "weekends" / "rainy.json",
        id="rainy-weekend",
        title="Rainy weekends",
        content="The user prefers museums on rainy weekends.",
        tags=["leisure", "rainy-day"],
    )
    _write_record(
        tmp_path / "preference" / "communication.json",
        id="communication",
    )
    _write_record(tmp_path / "self" / "identity.json", id="identity")
    (tmp_path / "preference" / "ignored.txt").write_text(
        "not a memory record",
        encoding="utf-8",
    )

    assert discover_records(tmp_path, "preference") == [
        MemoryRecord(
            id="communication",
            title=None,
            content="Memory from communication",
            tags=(),
            relative_path="communication.json",
        ),
        MemoryRecord(
            id="rainy-weekend",
            title="Rainy weekends",
            content="The user prefers museums on rainy weekends.",
            tags=("leisure", "rainy-day"),
            relative_path="weekends/rainy.json",
        ),
    ]


def test_discover_records_returns_empty_for_a_missing_scope_directory(
    tmp_path: Path,
) -> None:
    assert discover_records(tmp_path, "knowledge") == []


def test_discover_records_rejects_a_non_scope_value(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown memory scope"):
        discover_records(tmp_path, "../preference")


@pytest.mark.parametrize(
    "record",
    [
        [],
        {},
        {"schema_version": True, "id": "valid", "content": "Valid"},
        {"schema_version": 1, "id": "invalid/id", "content": "Valid"},
        {"schema_version": 1, "id": "x" * 101, "content": "Valid"},
        {"schema_version": 1, "id": "valid", "content": "   "},
        {"schema_version": 1, "id": "valid", "content": "x" * 4001},
        {
            "schema_version": 1,
            "id": "valid",
            "content": "Valid",
            "title": "",
        },
        {
            "schema_version": 1,
            "id": "valid",
            "content": "Valid",
            "title": "x" * 201,
        },
        {
            "schema_version": 1,
            "id": "valid",
            "content": "Valid",
            "tags": [],
        },
        {
            "schema_version": 1,
            "id": "valid",
            "content": "Valid",
            "tags": ["duplicate", "duplicate"],
        },
        {
            "schema_version": 1,
            "id": "valid",
            "content": "Valid",
            "unexpected": "field",
        },
    ],
)
def test_discover_records_skips_schema_invalid_files(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    record: object,
) -> None:
    path = tmp_path / "preference" / "invalid.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(record), encoding="utf-8")
    caplog.set_level(logging.WARNING, logger="mcp.memory_recall.retrieval")

    assert discover_records(tmp_path, "preference") == []
    assert caplog.messages == [
        "skipped scope='preference' path='invalid.json' reason='invalid_record'"
    ]


def test_discover_records_skips_invalid_json_and_encoding(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    scope = tmp_path / "preference"
    scope.mkdir()
    (scope / "bad-encoding.json").write_bytes(b"\xff")
    (scope / "bad-json.json").write_text("{", encoding="utf-8")
    caplog.set_level(logging.WARNING, logger="mcp.memory_recall.retrieval")

    assert discover_records(tmp_path, "preference") == []
    assert caplog.messages == [
        "skipped scope='preference' path='bad-encoding.json' "
        "reason='invalid_encoding'",
        "skipped scope='preference' path='bad-json.json' reason='invalid_json'",
    ]


def test_discover_records_skips_oversized_and_too_deep_sources(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    scope = tmp_path / "preference"
    scope.mkdir()
    (scope / "oversized.json").write_bytes(b"x" * 65_537)
    _write_record(scope / "one" / "two" / "three" / "four" / "valid.json")
    _write_record(
        scope / "one" / "two" / "three" / "four" / "five" / "ignored.json"
    )
    caplog.set_level(logging.WARNING, logger="mcp.memory_recall.retrieval")

    records = discover_records(tmp_path, "preference")

    assert [record.id for record in records] == ["valid"]
    assert caplog.messages == [
        "skipped scope='preference' path='one/two/three/four/five' "
        "reason='too_deep'",
        "skipped scope='preference' path='oversized.json' reason='oversized'",
    ]


def test_discover_records_rejects_symlink_files_and_directories(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    scope = tmp_path / "preference"
    scope.mkdir()
    outside_file = tmp_path / "outside.json"
    _write_record(outside_file)
    outside_directory = tmp_path / "outside"
    _write_record(outside_directory / "memory.json")
    try:
        (scope / "linked-file.json").symlink_to(outside_file)
        (scope / "linked-directory").symlink_to(outside_directory, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")
    caplog.set_level(logging.WARNING, logger="mcp.memory_recall.retrieval")

    assert discover_records(tmp_path, "preference") == []
    assert caplog.messages == [
        "skipped scope='preference' path='linked-directory' reason='symlink'",
        "skipped scope='preference' path='linked-file.json' reason='symlink'",
    ]


def test_discover_records_rejects_more_than_one_thousand_candidates(
    tmp_path: Path,
) -> None:
    scope = tmp_path / "preference"
    scope.mkdir()
    for index in range(1_001):
        (scope / f"{index:04}.json").write_text("{}", encoding="utf-8")

    with pytest.raises(CandidateLimitExceeded):
        discover_records(tmp_path, "preference")


def test_rank_records_applies_the_declared_field_weights() -> None:
    record = _memory(
        "rainy-weekend",
        title="Rainy plans",
        content="A rainy afternoon at the museum.",
        tags=("rainy-day", "leisure"),
        relative_path="leisure/rainy.json",
    )

    assert rank_records(
        [record],
        "What rainy afternoon leisure museum?",
        ["LEISURE", "rainy-day", "absent"],
    ) == [
        MemoryMatch(
            record=record,
            score=18,
            matched_terms=("afternoon", "leisure", "museum", "rainy"),
            matched_tags=("leisure", "rainy-day"),
        )
    ]


def test_rank_records_casefolds_unicode_and_splits_path_punctuation() -> None:
    record = _memory(
        "cafe",
        title="CAFÉ choices",
        content="A quiet afternoon.",
        relative_path="free_time/weekend-plan.json",
    )

    matches = rank_records(
        [record],
        "What is the café free time weekend plan?",
        [],
    )

    assert matches == [
        MemoryMatch(
            record=record,
            score=11,
            matched_terms=("café", "free", "plan", "time", "weekend"),
            matched_tags=(),
        )
    ]


def test_rank_records_removes_question_words_and_requires_a_positive_score() -> None:
    generic = _memory(
        "generic",
        content="The user is available.",
    )

    assert rank_records([generic], "What is the user?", []) == []


def test_rank_records_uses_record_tags_for_query_terms_without_requiring_tags() -> None:
    record = _memory(
        "weekend",
        content="A saved preference.",
        tags=("rainy-day",),
    )

    assert rank_records([record], "rainy day", []) == [
        MemoryMatch(
            record=record,
            score=4,
            matched_terms=("day", "rainy"),
            matched_tags=(),
        )
    ]


def test_rank_records_breaks_score_ties_by_path_then_id() -> None:
    records = [
        _memory("z", content="Matched", relative_path="z.json"),
        _memory("b", content="Matched", relative_path="same.json"),
        _memory("a", content="Matched", relative_path="same.json"),
    ]

    assert [
        match.record.id for match in rank_records(records, "matched", [])
    ] == ["a", "b", "z"]


def test_rank_records_returns_only_the_five_highest_ranked_records() -> None:
    records = [
        _memory(
            f"memory-{index}",
            content="Match " * index,
            relative_path=f"{index}.json",
        )
        for index in range(1, 8)
    ]

    matches = rank_records(records, "match", [])

    assert len(matches) == 5
    assert [match.record.id for match in matches] == [
        "memory-1",
        "memory-2",
        "memory-3",
        "memory-4",
        "memory-5",
    ]

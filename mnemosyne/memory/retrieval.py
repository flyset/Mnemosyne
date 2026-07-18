import re
from collections.abc import Sequence
from dataclasses import dataclass

from mnemosyne.memory.records import LifecycleState, MemoryRecordV2
from mnemosyne.memory.store import StoredMemory


MAX_RESULTS = 5
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "do",
    "does",
    "for",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "user",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
}
TOKEN_PATTERN = re.compile(r"[^\W_]+", re.UNICODE)


@dataclass(frozen=True)
class MemoryMatch:
    memory: StoredMemory
    score: int
    matched_terms: tuple[str, ...]
    matched_tags: tuple[str, ...]


def _terms(text: str) -> set[str]:
    return {
        term
        for term in TOKEN_PATTERN.findall(text.casefold())
        if len(term) > 1 and term not in STOP_WORDS
    }


def _normalize_tag(tag: str) -> str:
    return " ".join(tag.casefold().split())


def rank_memories(
    memories: Sequence[StoredMemory],
    query: str,
    request_tags: Sequence[str],
) -> list[MemoryMatch]:
    query_terms = _terms(query)
    normalized_request_tags = {_normalize_tag(tag) for tag in request_tags}
    matches: list[MemoryMatch] = []

    for memory in memories:
        record = memory.record
        if (
            isinstance(record, MemoryRecordV2)
            and record.lifecycle.state is LifecycleState.ARCHIVED
        ):
            continue

        title_terms = _terms(record.title or "")
        content_terms = _terms(record.content)
        path_terms = _terms(memory.scope_relative_path)
        record_tag_terms = {
            term
            for tag in record.tags
            for term in _terms(tag)
        }
        normalized_record_tags = {_normalize_tag(tag) for tag in record.tags}

        title_matches = query_terms & title_terms
        path_or_tag_matches = query_terms & (path_terms | record_tag_terms)
        content_matches = query_terms & content_terms
        matched_tags = normalized_request_tags & normalized_record_tags
        score = (
            4 * len(matched_tags)
            + 3 * len(title_matches)
            + 2 * len(path_or_tag_matches)
            + len(content_matches)
        )
        if score <= 0:
            continue

        matched_terms = title_matches | path_or_tag_matches | content_matches
        matches.append(
            MemoryMatch(
                memory=memory,
                score=score,
                matched_terms=tuple(sorted(matched_terms)),
                matched_tags=tuple(sorted(matched_tags)),
            )
        )

    matches.sort(
        key=lambda match: (
            -match.score,
            match.memory.scope_relative_path,
            match.memory.record.id,
        )
    )
    return matches[:MAX_RESULTS]

import json
import logging
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mnemosyne.mcp.tools.memory_recall.definition import SCOPES


logger = logging.getLogger("mcp.memory_recall.retrieval")

MAX_CANDIDATES = 1_000
MAX_CONTENT_LENGTH = 4_000
MAX_DIRECTORY_DEPTH = 4
MAX_FILE_BYTES = 65_536
MAX_ID_LENGTH = 100
MAX_RESULTS = 5
MAX_TAGS = 10
MAX_TAG_LENGTH = 50
MAX_TITLE_LENGTH = 200

ID_PATTERN = re.compile(r"[A-Za-z0-9._-]+")
RECORD_FIELDS = {"schema_version", "id", "content", "title", "tags"}
REQUIRED_RECORD_FIELDS = {"schema_version", "id", "content"}
SCOPE_DIRECTORIES = {scope: scope for scope in SCOPES}
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


class CandidateLimitExceeded(Exception):
    pass


class MemorySourceUnavailable(Exception):
    pass


@dataclass(frozen=True)
class MemoryRecord:
    id: str
    title: str | None
    content: str
    tags: tuple[str, ...]
    relative_path: str


@dataclass(frozen=True)
class MemoryMatch:
    record: MemoryRecord
    score: int
    matched_terms: tuple[str, ...]
    matched_tags: tuple[str, ...]


def _log_skipped(scope: str, relative_path: str, reason: str) -> None:
    logger.warning(
        "skipped scope=%r path=%r reason=%r",
        scope,
        relative_path,
        reason,
    )


def _discover_candidates(scope_directory: Path, scope: str) -> list[Path]:
    candidates: list[Path] = []

    def walk(directory: Path, relative_directory: Path, depth: int) -> None:
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as error:
            raise MemorySourceUnavailable from error

        for entry in entries:
            relative_path = relative_directory / entry.name
            display_path = relative_path.as_posix()
            try:
                if entry.is_symlink():
                    _log_skipped(scope, display_path, "symlink")
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if depth >= MAX_DIRECTORY_DEPTH:
                        _log_skipped(scope, display_path, "too_deep")
                    else:
                        walk(Path(entry.path), relative_path, depth + 1)
                    continue
                is_json_file = (
                    entry.is_file(follow_symlinks=False)
                    and Path(entry.name).suffix == ".json"
                )
            except OSError:
                _log_skipped(scope, display_path, "unreadable")
                continue

            if not is_json_file:
                continue

            candidates.append(Path(entry.path))
            if len(candidates) > MAX_CANDIDATES:
                raise CandidateLimitExceeded

    walk(scope_directory, Path(), 0)
    return candidates


def _valid_text(value: object, maximum_length: int) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and len(value) <= maximum_length
    )


def _parse_record(payload: Any, relative_path: str) -> MemoryRecord | None:
    if not isinstance(payload, dict):
        return None
    if set(payload) - RECORD_FIELDS or not REQUIRED_RECORD_FIELDS <= set(payload):
        return None
    if type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
        return None

    record_id = payload["id"]
    if (
        not isinstance(record_id, str)
        or len(record_id) > MAX_ID_LENGTH
        or ID_PATTERN.fullmatch(record_id) is None
    ):
        return None

    content = payload["content"]
    if not _valid_text(content, MAX_CONTENT_LENGTH):
        return None

    title = payload.get("title")
    if title is not None and not _valid_text(title, MAX_TITLE_LENGTH):
        return None

    tags = payload.get("tags", [])
    if (
        not isinstance(tags, list)
        or ("tags" in payload and not 1 <= len(tags) <= MAX_TAGS)
        or any(not _valid_text(tag, MAX_TAG_LENGTH) for tag in tags)
        or len(set(tags)) != len(tags)
    ):
        return None

    return MemoryRecord(
        id=record_id,
        title=title,
        content=content,
        tags=tuple(tags),
        relative_path=relative_path,
    )


def _load_record(path: Path, scope_directory: Path, scope: str) -> MemoryRecord | None:
    relative_path = path.relative_to(scope_directory).as_posix()
    try:
        if path.is_symlink():
            _log_skipped(scope, relative_path, "symlink")
            return None
        if path.stat().st_size > MAX_FILE_BYTES:
            _log_skipped(scope, relative_path, "oversized")
            return None
        raw_record = path.read_bytes()
    except OSError:
        _log_skipped(scope, relative_path, "unreadable")
        return None

    if len(raw_record) > MAX_FILE_BYTES:
        _log_skipped(scope, relative_path, "oversized")
        return None

    try:
        text_record = raw_record.decode("utf-8")
    except UnicodeDecodeError:
        _log_skipped(scope, relative_path, "invalid_encoding")
        return None

    try:
        payload = json.loads(text_record)
    except json.JSONDecodeError:
        _log_skipped(scope, relative_path, "invalid_json")
        return None

    record = _parse_record(payload, relative_path)
    if record is None:
        _log_skipped(scope, relative_path, "invalid_record")
    return record


def discover_records(memory_root: Path, scope: str) -> list[MemoryRecord]:
    scope_directory_name = SCOPE_DIRECTORIES.get(scope)
    if scope_directory_name is None:
        raise ValueError("unknown memory scope")

    scope_directory = memory_root / scope_directory_name
    if not scope_directory.exists():
        return []
    if scope_directory.is_symlink():
        _log_skipped(scope, ".", "symlink")
        return []
    if not scope_directory.is_dir():
        raise MemorySourceUnavailable

    candidates = _discover_candidates(scope_directory, scope)
    records = [
        record
        for path in candidates
        if (record := _load_record(path, scope_directory, scope)) is not None
    ]
    return records


def _terms(text: str) -> set[str]:
    return {
        term
        for term in TOKEN_PATTERN.findall(text.casefold())
        if len(term) > 1 and term not in STOP_WORDS
    }


def _normalize_tag(tag: str) -> str:
    return " ".join(tag.casefold().split())


def rank_records(
    records: Sequence[MemoryRecord],
    query: str,
    request_tags: Sequence[str],
) -> list[MemoryMatch]:
    query_terms = _terms(query)
    normalized_request_tags = {_normalize_tag(tag) for tag in request_tags}
    matches: list[MemoryMatch] = []

    for record in records:
        title_terms = _terms(record.title or "")
        content_terms = _terms(record.content)
        path_terms = _terms(record.relative_path)
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
                record=record,
                score=score,
                matched_terms=tuple(sorted(matched_terms)),
                matched_tags=tuple(sorted(matched_tags)),
            )
        )

    matches.sort(
        key=lambda match: (
            -match.score,
            match.record.relative_path,
            match.record.id,
        )
    )
    return matches[:MAX_RESULTS]

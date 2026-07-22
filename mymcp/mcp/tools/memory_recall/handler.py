import json
import logging
from collections.abc import Callable
from typing import Any

from mymcp.memory.errors import (
    CandidateLimitExceeded,
    MemorySourceUnavailable,
)
from mymcp.memory.records import MemoryRecordV2
from mymcp.memory.retrieval import MemoryMatch
from mymcp.memory.scopes import MemoryScope, SCOPE_VALUES, parse_scope


logger = logging.getLogger("mcp.memory_recall")
RecallOperation = Callable[[MemoryScope, str, list[str]], list[MemoryMatch]]

INVALID_QUERY_MESSAGE = (
    "query must be a non-empty string of at most 1000 characters"
)
INVALID_SCOPE_MESSAGE = (
    "scope must be one of: self, relationship, preference, practice, project, "
    "knowledge"
)
INVALID_TAGS_MESSAGE = (
    "tags must be an array of 1 to 10 unique non-empty strings of at most 50 "
    "characters"
)
MEMORY_SOURCE_UNAVAILABLE_MESSAGE = "memory source could not be read"
CANDIDATE_LIMIT_EXCEEDED_MESSAGE = (
    "memory scope contains more than 1000 candidate files"
)


def _text_content(payload: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "type": "text",
            "text": json.dumps(payload, separators=(",", ":")),
        }
    ]


def _error(code: str, message: str, *, status: str) -> dict[str, Any]:
    return {
        "content": _text_content(
            {
                "status": status,
                "code": code,
                "message": message,
            }
        ),
        "isError": True,
    }


def _serialize_match(match: MemoryMatch, scope: str) -> dict[str, Any]:
    record = match.memory.record
    reference = (
        {
            "schema_version": 2,
            "scope": record.scope.value,
            "namespace_id": record.namespace.id,
            "collection_id": (
                record.collection.id if record.collection is not None else None
            ),
            "id": record.id,
        }
        if isinstance(record, MemoryRecordV2)
        else {
            "schema_version": 1,
            "scope": scope,
            "id": record.id,
        }
    )
    return {
        "reference": reference,
        "id": record.id,
        "scope": scope,
        "title": record.title,
        "content": record.content,
        "tags": list(record.tags),
        "match": {
            "terms": list(match.matched_terms),
            "tags": list(match.matched_tags),
        },
    }


def handle(
    arguments: dict[str, Any],
    *,
    recall_operation: RecallOperation,
) -> dict[str, Any]:
    query = arguments.get("query")

    logger.info(
        "request message=%r scope=%r tags=%r",
        query,
        arguments.get("scope"),
        arguments.get("tags", []),
    )

    if not isinstance(query, str) or not query.strip() or len(query) > 1000:
        return _error(
            "invalid_query",
            INVALID_QUERY_MESSAGE,
            status="invalid_request",
        )

    scope = arguments.get("scope")
    if scope not in SCOPE_VALUES:
        return _error(
            "invalid_scope",
            INVALID_SCOPE_MESSAGE,
            status="invalid_request",
        )

    request_tags: list[str] = []
    if "tags" in arguments:
        tags = arguments["tags"]
        if (
            not isinstance(tags, list)
            or not 1 <= len(tags) <= 10
            or any(
                not isinstance(tag, str)
                or not tag.strip()
                or len(tag) > 50
                for tag in tags
            )
            or len(set(tags)) != len(tags)
        ):
            return _error(
                "invalid_tags",
                INVALID_TAGS_MESSAGE,
                status="invalid_request",
            )
        request_tags = tags

    try:
        matches = recall_operation(
            parse_scope(scope),
            query,
            request_tags,
        )
    except CandidateLimitExceeded:
        return _error(
            "candidate_limit_exceeded",
            CANDIDATE_LIMIT_EXCEEDED_MESSAGE,
            status="retrieval_error",
        )
    except (MemorySourceUnavailable, OSError):
        return _error(
            "memory_source_unavailable",
            MEMORY_SOURCE_UNAVAILABLE_MESSAGE,
            status="retrieval_error",
        )

    if not matches:
        return {
            "content": _text_content(
                {
                    "status": "no_matches",
                    "memories": [],
                }
            )
        }

    return {
        "content": _text_content(
            {
                "status": "ok",
                "memories": [_serialize_match(match, scope) for match in matches],
            }
        )
    }

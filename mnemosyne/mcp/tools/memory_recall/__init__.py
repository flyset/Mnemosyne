import json
import logging
from typing import Any


logger = logging.getLogger("mcp.memory_recall")

SCOPES = (
    "self",
    "relationship",
    "preference",
    "practice",
    "project",
    "knowledge",
)


TOOL = {
    "name": "memory_recall",
    "description": (
        "Submit a narrowly scoped request for user-approved memory that could "
        "materially improve or change the response. Select exactly one scope according "
        "to what the memory concerns, not how it was learned. Use separate calls for "
        "different scopes. Do not use for ordinary general-knowledge questions. Do not "
        "include the full conversation, unrelated personal details, secrets, or "
        "sensitive personal data."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Describe only the user-specific information needed for the current "
                    "request."
                ),
                "minLength": 1,
                "maxLength": 1000,
            },
            "scope": {
                "description": (
                    "Select the high-level domain that best describes the requested "
                    "memory."
                ),
                "oneOf": [
                    {
                        "const": "self",
                        "description": (
                            "Who the user is and their enduring circumstances."
                        ),
                    },
                    {
                        "const": "relationship",
                        "description": (
                            "People, relationships, and the user's perspective about "
                            "others."
                        ),
                    },
                    {
                        "const": "preference",
                        "description": "Choices the user explicitly wants respected.",
                    },
                    {
                        "const": "practice",
                        "description": (
                            "Routines, methods, habits, and actual ways of working."
                        ),
                    },
                    {
                        "const": "project",
                        "description": (
                            "Goals, state, decisions, and constraints of a bounded "
                            "endeavor."
                        ),
                    },
                    {
                        "const": "knowledge",
                        "description": (
                            "User-approved reference material useful beyond one project, "
                            "not ordinary general knowledge."
                        ),
                    },
                ],
            },
            "tags": {
                "type": "array",
                "description": (
                    "Optional free-form descriptive labels for the requested memory."
                ),
                "items": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 50,
                    "pattern": "\\S",
                },
                "minItems": 1,
                "maxItems": 10,
                "uniqueItems": True,
            },
        },
        "required": ["query", "scope"],
        "additionalProperties": False,
    },
}

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


def _text_content(payload: dict[str, str]) -> list[dict[str, str]]:
    return [
        {
            "type": "text",
            "text": json.dumps(payload, separators=(",", ":")),
        }
    ]


def handle(arguments: dict[str, Any]) -> dict[str, Any]:
    query = arguments.get("query")
    logger.info("request query=%r", query)
    if not isinstance(query, str) or not query.strip() or len(query) > 1000:
        return {
            "content": _text_content(
                {
                    "status": "invalid_request",
                    "code": "invalid_query",
                    "message": INVALID_QUERY_MESSAGE,
                }
            ),
            "isError": True,
        }

    scope = arguments.get("scope")
    if scope not in SCOPES:
        return {
            "content": _text_content(
                {
                    "status": "invalid_request",
                    "code": "invalid_scope",
                    "message": INVALID_SCOPE_MESSAGE,
                }
            ),
            "isError": True,
        }

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
            return {
                "content": _text_content(
                    {
                        "status": "invalid_request",
                        "code": "invalid_tags",
                        "message": INVALID_TAGS_MESSAGE,
                    }
                ),
                "isError": True,
            }

    return {
        "content": _text_content({"status": "retrieval_unavailable"}),
    }

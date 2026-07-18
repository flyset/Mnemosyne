import json

import pytest

from mnemosyne.mcp.tools.memory_recall import TOOL, handle


def test_memory_recall_exposes_the_selected_tool_definition() -> None:
    assert TOOL == {
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


@pytest.mark.parametrize(
    "arguments",
    [
        {"query": "preferred response style", "scope": "preference"},
        {
            "query": "current project constraints",
            "scope": "project",
            "tags": ["storage", "constraints"],
        },
    ],
)
def test_memory_recall_returns_retrieval_unavailable_for_valid_arguments(
    arguments: dict[str, object],
) -> None:
    assert handle(arguments) == {
        "content": [
            {
                "type": "text",
                "text": '{"status":"retrieval_unavailable"}',
            }
        ]
    }


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"query": None},
        {"query": 42},
        {"query": ""},
        {"query": "   "},
        {"query": "x" * 1001},
    ],
)
def test_memory_recall_rejects_invalid_queries(arguments: dict[str, object]) -> None:
    result = handle(arguments)

    assert result["isError"] is True
    assert json.loads(result["content"][0]["text"]) == {
        "status": "invalid_request",
        "code": "invalid_query",
        "message": "query must be a non-empty string of at most 1000 characters",
    }


@pytest.mark.parametrize(
    "scope",
    [None, 42, "", "missing"],
)
def test_memory_recall_rejects_missing_or_unknown_scopes(scope: object) -> None:
    arguments = {"query": "relevant memory"}
    if scope is not None:
        arguments["scope"] = scope

    result = handle(arguments)

    assert result["isError"] is True
    assert json.loads(result["content"][0]["text"]) == {
        "status": "invalid_request",
        "code": "invalid_scope",
        "message": (
            "scope must be one of: self, relationship, preference, practice, project, "
            "knowledge"
        ),
    }


@pytest.mark.parametrize(
    "tags",
    [
        None,
        "python",
        [],
        ["tag"] * 11,
        [42],
        [""],
        ["   "],
        ["x" * 51],
        ["python", "python"],
    ],
)
def test_memory_recall_rejects_invalid_tags(tags: object) -> None:
    result = handle(
        {
            "query": "relevant memory",
            "scope": "knowledge",
            "tags": tags,
        }
    )

    assert result["isError"] is True
    assert json.loads(result["content"][0]["text"]) == {
        "status": "invalid_request",
        "code": "invalid_tags",
        "message": (
            "tags must be an array of 1 to 10 unique non-empty strings of at most 50 "
            "characters"
        ),
    }

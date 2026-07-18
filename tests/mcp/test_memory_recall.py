import json
import logging
from pathlib import Path

import pytest

from mnemosyne.mcp.tools.memory_recall import TOOL, handle
from mnemosyne.mcp.tools.memory_recall import handler as handler_module
from mnemosyne.mcp.tools.memory_recall.definition import TOOL as DEFINED_TOOL
from mnemosyne.memory.errors import (
    CandidateLimitExceeded,
    MemorySourceUnavailable,
)
from mnemosyne.settings import get_memory_root


def _write_memory(path: Path, record: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record), encoding="utf-8")


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


def test_memory_recall_package_reexports_definition_and_handler() -> None:
    assert TOOL is DEFINED_TOOL
    assert handle is handler_module.handle


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
def test_memory_recall_returns_no_matches_for_valid_arguments_without_memories(
    arguments: dict[str, object],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    assert handle(arguments) == {
        "content": [
            {
                "type": "text",
                "text": '{"status":"no_matches","memories":[]}',
            }
        ]
    }


def test_memory_recall_returns_ranked_memories_without_paths_or_scores(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_memory(
        tmp_path / "preference" / "leisure" / "rainy-weekend.json",
        {
            "schema_version": 1,
            "id": "rainy-weekend",
            "title": "Rainy weekend activities",
            "content": "The user prefers museums on a rainy weekend.",
            "tags": ["leisure", "rainy-day", "weekend"],
        },
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    result = handle(
        {
            "query": "What does the user prefer doing on rainy Saturday afternoons?",
            "scope": "preference",
            "tags": ["leisure", "rainy-day", "weekend"],
        }
    )

    assert "isError" not in result
    assert json.loads(result["content"][0]["text"]) == {
        "status": "ok",
        "memories": [
            {
                "reference": {
                    "schema_version": 1,
                    "scope": "preference",
                    "id": "rainy-weekend",
                },
                "id": "rainy-weekend",
                "scope": "preference",
                "title": "Rainy weekend activities",
                "content": "The user prefers museums on a rainy weekend.",
                "tags": ["leisure", "rainy-day", "weekend"],
                "match": {
                    "terms": ["rainy"],
                    "tags": ["leisure", "rainy-day", "weekend"],
                },
            }
        ],
    }
    assert "path" not in result["content"][0]["text"]
    assert "score" not in result["content"][0]["text"]


def test_memory_recall_returns_active_version_two_memory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory_id = "mem_0123456789abcdef0123456789abcdef"
    _write_memory(
        tmp_path / "preference" / "leisure" / f"{memory_id}.json",
        {
            "schema_version": 2,
            "id": memory_id,
            "scope": "preference",
            "namespace": {
                "kind": "domain",
                "id": "leisure",
                "label": "Leisure",
            },
            "collection": None,
            "kind": "preference",
            "language": "en",
            "title": "Rainy activities",
            "content": "The user prefers museums on rainy days.",
            "tags": ["leisure", "rainy-day"],
            "provenance": {
                "origin": "explicit_user_statement",
                "recorded_via": "memory_remember",
            },
            "lifecycle": {"state": "active", "revision": 1},
            "created_at": "2026-07-18T12:00:00Z",
            "updated_at": "2026-07-18T12:00:00Z",
        },
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    result = handle(
        {
            "query": "rainy leisure activities",
            "scope": "preference",
            "tags": ["leisure", "rainy-day"],
        }
    )

    assert json.loads(result["content"][0]["text"]) == {
        "status": "ok",
        "memories": [
            {
                "reference": {
                    "schema_version": 2,
                    "scope": "preference",
                    "namespace_id": "leisure",
                    "collection_id": None,
                    "id": memory_id,
                },
                "id": memory_id,
                "scope": "preference",
                "title": "Rainy activities",
                "content": "The user prefers museums on rainy days.",
                "tags": ["leisure", "rainy-day"],
                "match": {
                    "terms": ["activities", "leisure", "rainy"],
                    "tags": ["leisure", "rainy-day"],
                },
            }
        ],
    }


def test_memory_recall_excludes_archived_version_two_memory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory_id = "mem_0123456789abcdef0123456789abcdef"
    _write_memory(
        tmp_path / "preference" / "leisure" / f"{memory_id}.json",
        {
            "schema_version": 2,
            "id": memory_id,
            "scope": "preference",
            "namespace": {
                "kind": "domain",
                "id": "leisure",
                "label": "Leisure",
            },
            "collection": None,
            "kind": "preference",
            "language": "en",
            "title": None,
            "content": "Archived rainy memory.",
            "tags": [],
            "provenance": {
                "origin": "explicit_user_statement",
                "recorded_via": "memory_remember",
            },
            "lifecycle": {"state": "archived", "revision": 2},
            "created_at": "2026-07-18T12:00:00Z",
            "updated_at": "2026-07-18T13:00:00Z",
        },
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    result = handle({"query": "rainy", "scope": "preference"})

    assert json.loads(result["content"][0]["text"]) == {
        "status": "no_matches",
        "memories": [],
    }


def test_memory_recall_searches_only_the_requested_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_memory(
        tmp_path / "self" / "rainy.json",
        {
            "schema_version": 1,
            "id": "rainy-self",
            "content": "Rainy personal context.",
        },
    )
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    result = handle({"query": "rainy", "scope": "preference"})

    assert json.loads(result["content"][0]["text"]) == {
        "status": "no_matches",
        "memories": [],
    }


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            MemorySourceUnavailable(),
            {
                "status": "retrieval_error",
                "code": "memory_source_unavailable",
                "message": "memory source could not be read",
            },
        ),
        (
            CandidateLimitExceeded(),
            {
                "status": "retrieval_error",
                "code": "candidate_limit_exceeded",
                "message": "memory scope contains more than 1000 candidate files",
            },
        ),
    ],
)
def test_memory_recall_returns_stable_retrieval_errors(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    expected: dict[str, str],
) -> None:
    def fail_recall(*args: object) -> None:
        raise error

    monkeypatch.setattr(handler_module.MemoryService, "recall", fail_recall)

    result = handle({"query": "relevant memory", "scope": "knowledge"})

    assert result["isError"] is True
    assert json.loads(result["content"][0]["text"]) == expected


def test_memory_recall_logs_message_scope_and_tags(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))
    caplog.set_level(logging.INFO, logger="mcp.memory_recall")

    handle(
        {
            "query": "rainy weekend activities",
            "scope": "preference",
            "tags": ["leisure", "weekend"],
        }
    )

    assert (
        "request message='rainy weekend activities' scope='preference' "
        "tags=['leisure', 'weekend']"
    ) in caplog.messages


def test_memory_root_uses_operator_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MNEMOSYNE_MEMORY_ROOT", str(tmp_path))

    assert get_memory_root() == tmp_path


def test_memory_root_defaults_under_the_user_home(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MNEMOSYNE_MEMORY_ROOT", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    assert get_memory_root() == tmp_path / ".mnemosyne" / "memory"


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

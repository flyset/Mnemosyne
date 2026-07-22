import pytest

from mymcp.memory.errors import MemoryValidationError
from mymcp.memory.scopes import (
    SCOPE_DEFINITIONS,
    SCOPE_VALUES,
    MemoryScope,
    parse_scope,
)
from mymcp.mcp.tools.memory_recall import TOOL


def test_scope_registry_is_the_canonical_ordered_contract() -> None:
    assert [
        (
            definition.scope,
            definition.description,
            definition.directory,
            definition.namespace_kinds,
        )
        for definition in SCOPE_DEFINITIONS
    ] == [
        (
            MemoryScope.SELF,
            "Who the user is and their enduring circumstances.",
            "self",
            ("aspect",),
        ),
        (
            MemoryScope.RELATIONSHIP,
            "People, relationships, and the user's perspective about others.",
            "relationship",
            ("person", "group", "relationship"),
        ),
        (
            MemoryScope.PREFERENCE,
            "Choices the user explicitly wants respected.",
            "preference",
            ("domain",),
        ),
        (
            MemoryScope.PRACTICE,
            "Routines, methods, habits, and actual ways of working.",
            "practice",
            ("domain",),
        ),
        (
            MemoryScope.PROJECT,
            "Goals, state, decisions, and constraints of a bounded endeavor.",
            "project",
            ("project",),
        ),
        (
            MemoryScope.KNOWLEDGE,
            "User-approved reference material useful beyond one project, not ordinary "
            "general knowledge.",
            "knowledge",
            ("topic",),
        ),
    ]
    assert SCOPE_VALUES == (
        "self",
        "relationship",
        "preference",
        "practice",
        "project",
        "knowledge",
    )


def test_recall_tool_scope_schema_is_derived_as_a_portable_enum() -> None:
    scope_schema = TOOL["inputSchema"]["properties"]["scope"]

    assert scope_schema["type"] == "string"
    assert scope_schema["enum"] == [
        definition.scope.value for definition in SCOPE_DEFINITIONS
    ]
    assert all(
        definition.description in scope_schema["description"]
        for definition in SCOPE_DEFINITIONS
    )


@pytest.mark.parametrize("scope", SCOPE_VALUES)
def test_parse_scope_returns_the_canonical_enum(scope: str) -> None:
    assert parse_scope(scope) is MemoryScope(scope)


@pytest.mark.parametrize("scope", [None, 1, "", "missing"])
def test_parse_scope_rejects_unknown_values(scope: object) -> None:
    with pytest.raises(MemoryValidationError) as error:
        parse_scope(scope)

    assert error.value.code == "invalid_scope"
    assert error.value.field == "scope"

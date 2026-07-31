from mymcp.plugins.mnemosyne.memory.records import KIND_DEFINITIONS
from mymcp.plugins.mnemosyne.memory.scopes import SCOPE_DEFINITIONS
from mymcp.plugins.mnemosyne.mcp.tools import (
    memory_archive,
    memory_forget,
    memory_inspect,
    memory_list,
    memory_recall,
    memory_remember,
    memory_restore,
    memory_revise,
)


EXISTING_SCOPES = [
    "self",
    "relationship",
    "preference",
    "practice",
    "project",
    "knowledge",
]
EXISTING_SCOPE_DEFINITIONS = [
    (
        "self",
        "Who the user is and their enduring circumstances.",
        "self",
        ("aspect",),
    ),
    (
        "relationship",
        "People, relationships, and the user's perspective about others.",
        "relationship",
        ("person", "group", "relationship"),
    ),
    (
        "preference",
        "Choices the user explicitly wants respected.",
        "preference",
        ("domain",),
    ),
    (
        "practice",
        "Routines, methods, habits, and actual ways of working.",
        "practice",
        ("domain",),
    ),
    (
        "project",
        "Goals, state, decisions, and constraints of a bounded endeavor.",
        "project",
        ("project",),
    ),
    (
        "knowledge",
        "User-approved reference material useful beyond one project, not ordinary "
        "general knowledge.",
        "knowledge",
        ("topic",),
    ),
]
EXISTING_KINDS = {
    "self": ["attribute"],
    "relationship": ["perspective", "summary"],
    "preference": ["preference"],
    "practice": ["practice"],
    "project": [
        "decision",
        "constraint",
        "state",
        "event",
        "question",
        "reference",
        "summary",
    ],
    "knowledge": ["reference", "summary"],
}


def _scope_values(scope_schema: dict[str, object]) -> list[str]:
    return [branch["const"] for branch in scope_schema["oneOf"]]


def test_original_scope_domain_contract_is_unchanged_before_agent() -> None:
    assert [
        (
            definition.scope.value,
            definition.description,
            definition.directory,
            definition.namespace_kinds,
        )
        for definition in SCOPE_DEFINITIONS[:6]
    ] == EXISTING_SCOPE_DEFINITIONS
    assert SCOPE_DEFINITIONS[6].scope.value == "agent"

    assert {
        scope.value: [definition.kind.value for definition in definitions]
        for scope, definitions in KIND_DEFINITIONS.items()
        if scope.value in EXISTING_SCOPES
    } == EXISTING_KINDS


def test_original_scopes_remain_in_every_public_scope_schema() -> None:
    for tool in (memory_recall.TOOL, memory_list.TOOL):
        values = tool["inputSchema"]["properties"]["scope"]["enum"]
        assert values[:6] == EXISTING_SCOPES
        assert values[6:] == ["agent"]

    inspect_references = memory_inspect.TOOL["inputSchema"]["properties"][
        "reference"
    ]["oneOf"]
    for reference in inspect_references:
        values = _scope_values(reference["properties"]["scope"])
        assert values[:6] == EXISTING_SCOPES
        assert values[6:] == ["agent"]

    for tool in (
        memory_archive.TOOL,
        memory_restore.TOOL,
        memory_revise.TOOL,
        memory_forget.TOOL,
    ):
        reference = tool["inputSchema"]["properties"]["reference"]
        values = _scope_values(reference["properties"]["scope"])
        assert values[:6] == EXISTING_SCOPES
        assert values[6:] == ["agent"]


def test_original_remember_branches_are_unchanged_before_agent() -> None:
    branches = memory_remember.TOOL["inputSchema"]["oneOf"]
    by_scope = {
        branch["properties"]["scope"]["const"]: branch for branch in branches
    }

    assert list(by_scope)[:6] == EXISTING_SCOPES
    assert list(by_scope)[6:] == ["agent"]
    for scope, expected_kinds in EXISTING_KINDS.items():
        branch = by_scope[scope]
        scope_definition = EXISTING_SCOPE_DEFINITIONS[EXISTING_SCOPES.index(scope)]
        assert branch["properties"]["scope"] == {
            "const": scope,
            "description": scope_definition[1],
        }
        assert branch["properties"]["namespace"]["properties"]["kind"] == {
            "type": "string",
            "enum": list(scope_definition[3]),
        }
        assert branch["properties"]["kind"]["enum"] == expected_kinds

    project = by_scope["project"]
    assert project["allOf"] == [
        {
            "if": {"properties": {"kind": {"const": "event"}}},
            "then": {"required": ["occurred_at"]},
            "else": {"not": {"required": ["occurred_at"]}},
        }
    ]
    assert "occurred_at" in project["properties"]
    for scope in set(EXISTING_SCOPES) - {"project"}:
        assert "occurred_at" not in by_scope[scope]["properties"]

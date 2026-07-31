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


EXPECTED_SCOPES = [
    "self",
    "relationship",
    "preference",
    "practice",
    "project",
    "knowledge",
    "agent",
]


def _reference_scope_values(tool: dict[str, object]) -> list[str]:
    input_schema = tool["inputSchema"]
    assert isinstance(input_schema, dict)
    properties = input_schema["properties"]
    assert isinstance(properties, dict)
    reference = properties["reference"]
    assert isinstance(reference, dict)
    reference_properties = reference["properties"]
    assert isinstance(reference_properties, dict)
    scope = reference_properties["scope"]
    assert isinstance(scope, dict)
    return [branch["const"] for branch in scope["oneOf"]]


def test_all_eight_memory_tools_publish_the_agent_scope() -> None:
    for tool in (memory_recall.TOOL, memory_list.TOOL):
        assert tool["inputSchema"]["properties"]["scope"]["enum"] == EXPECTED_SCOPES

    inspect_references = memory_inspect.TOOL["inputSchema"]["properties"][
        "reference"
    ]["oneOf"]
    assert len(inspect_references) == 2
    for reference in inspect_references:
        assert [
            branch["const"]
            for branch in reference["properties"]["scope"]["oneOf"]
        ] == EXPECTED_SCOPES

    for tool in (
        memory_archive.TOOL,
        memory_restore.TOOL,
        memory_revise.TOOL,
        memory_forget.TOOL,
    ):
        assert _reference_scope_values(tool) == EXPECTED_SCOPES

    remember_schema = memory_remember.TOOL["inputSchema"]
    assert remember_schema["properties"]["scope"]["enum"] == EXPECTED_SCOPES
    branches = {
        branch["properties"]["scope"]["const"]: branch
        for branch in remember_schema["oneOf"]
    }
    assert list(branches) == EXPECTED_SCOPES
    agent = branches["agent"]
    assert agent["properties"]["namespace"]["properties"]["kind"] == {
        "type": "string",
        "enum": ["agent"],
    }
    assert agent["properties"]["kind"]["enum"] == [
        "persona",
        "policy",
        "checklist",
        "failure_mode",
    ]
    assert "occurred_at" not in agent["properties"]

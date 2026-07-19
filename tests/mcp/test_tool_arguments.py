from copy import deepcopy

import pytest

from mnemosyne.mcp import tool_arguments
from mnemosyne.mcp.tool_arguments import normalize_tool_arguments
from mnemosyne.mcp.tools.memory_list import TOOL as MEMORY_LIST_TOOL
from mnemosyne.mcp.tools.memory_list import handle as handle_memory_list
from mnemosyne.mcp.tools.memory_remember import TOOL as REMEMBER_TOOL
from mnemosyne.memory.listing import MemoryListPage, MemoryListResult


def _remember_arguments() -> dict[str, object]:
    return {
        "scope": "project",
        "namespace": {
            "kind": "project",
            "id": "mnemosyne",
            "label": "Mnemosyne",
        },
        "collection": {"id": "checkpoints", "label": "Checkpoints"},
        "kind": "state",
        "language": "en",
        "title": "Write-path validation test",
        "content": "Synthetic compatibility validation.",
        "tags": ["test", "validation"],
        "origin": "user_approved_proposal",
    }


def test_normalizer_decodes_captured_stringified_remember_fields_once() -> None:
    arguments = _remember_arguments()
    arguments.update(
        {
            "namespace": (
                '{"kind": "project", "id": "mnemosyne", '
                '"label": "Mnemosyne"}'
            ),
            "collection": '{"id": "checkpoints", "label": "Checkpoints"}',
            "tags": '["test", "validation"]',
        }
    )

    normalized = normalize_tool_arguments(arguments, REMEMBER_TOOL["inputSchema"])

    assert normalized == _remember_arguments()
    assert isinstance(arguments["namespace"], str)
    assert isinstance(arguments["collection"], str)
    assert isinstance(arguments["tags"], str)


def test_normalizer_leaves_native_arguments_unchanged_without_mutation() -> None:
    arguments = _remember_arguments()
    original = deepcopy(arguments)

    normalized = normalize_tool_arguments(arguments, REMEMBER_TOOL["inputSchema"])

    assert normalized == original
    assert arguments == original


def test_normalizer_never_decodes_schema_permitted_strings() -> None:
    arguments = _remember_arguments()
    arguments["title"] = '{"looks": "structured"}'
    arguments["content"] = '["must", "remain", "text"]'
    arguments["tags"] = '["{\\"tag\\": true}"]'

    normalized = normalize_tool_arguments(arguments, REMEMBER_TOOL["inputSchema"])

    assert normalized["title"] == '{"looks": "structured"}'
    assert normalized["content"] == '["must", "remain", "text"]'
    assert normalized["tags"] == ['{"tag": true}']


def test_normalizer_leaves_malformed_wrong_type_and_twice_stringified_values() -> None:
    schema = {
        "type": "object",
        "properties": {
            "object_value": {"type": "object", "properties": {}},
            "array_value": {"type": "array", "items": {"type": "string"}},
        },
    }
    arguments = {
        "object_value": '"{\\"nested\\": true}"',
        "array_value": '{"wrong": "type"}',
        "malformed": "[not-json",
    }

    normalized = normalize_tool_arguments(arguments, schema)

    assert normalized == arguments


def test_normalizer_does_not_descend_into_a_newly_decoded_value() -> None:
    schema = {
        "type": "object",
        "properties": {
            "reference": {
                "type": "object",
                "properties": {"revision": {"type": "integer"}},
            }
        },
    }
    arguments = {"reference": '{"revision": "2"}'}

    normalized = normalize_tool_arguments(arguments, schema)

    assert normalized == {"reference": {"revision": "2"}}


def test_normalizer_leaves_values_when_an_unconstrained_branch_permits_string() -> None:
    schema = {
        "type": "object",
        "properties": {
            "value": {
                "anyOf": [
                    {"type": "object", "properties": {}},
                    {},
                ]
            }
        },
    }

    normalized = normalize_tool_arguments({"value": '{"id": 1}'}, schema)

    assert normalized == {"value": '{"id": 1}'}


def test_normalizer_leaves_integer_strings_that_json_cannot_safely_decode() -> None:
    schema = {
        "type": "object",
        "properties": {"revision": {"type": "integer"}},
    }
    value = "1" * 5_000

    normalized = normalize_tool_arguments({"revision": value}, schema)

    assert normalized == {"revision": value}


def test_normalizer_leaves_json_when_decoder_exceeds_nesting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema = {
        "type": "object",
        "properties": {"value": {"type": "array"}},
    }

    def exceed_nesting(value: str) -> object:
        raise RecursionError

    monkeypatch.setattr(tool_arguments.json, "loads", exceed_nesting)
    value = "[]"

    normalized = normalize_tool_arguments({"value": value}, schema)

    assert normalized == {"value": value}


def test_normalizer_uses_const_discriminator_and_nullable_composition() -> None:
    arguments = _remember_arguments()
    arguments["collection"] = "null"

    normalized = normalize_tool_arguments(arguments, REMEMBER_TOOL["inputSchema"])

    assert normalized["collection"] is None


def test_normalizer_decodes_non_string_scalar_when_schema_requires_it() -> None:
    schema = {
        "type": "object",
        "properties": {
            "revision": {"type": "integer", "minimum": 1},
            "enabled": {"type": "boolean"},
        },
    }

    normalized = normalize_tool_arguments(
        {"revision": "2", "enabled": "true"},
        schema,
    )

    assert normalized == {"revision": 2, "enabled": True}


def test_normalizer_does_not_decode_when_any_branch_permits_string() -> None:
    schema = {
        "type": "object",
        "properties": {
            "value": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "object", "properties": {}},
                ]
            }
        },
    }

    normalized = normalize_tool_arguments({"value": '{"id": 1}'}, schema)

    assert normalized == {"value": '{"id": 1}'}


def test_normalizer_uses_json_numeric_type_semantics() -> None:
    schema = {
        "type": "object",
        "properties": {
            "number": {"type": "number"},
            "integer": {"type": "integer"},
        },
    }

    normalized = normalize_tool_arguments(
        {"number": "2", "integer": "2.0"},
        schema,
    )

    assert normalized == {"number": 2, "integer": 2.0}


def test_normalizer_distinguishes_boolean_and_numeric_const_types() -> None:
    schema = {
        "type": "object",
        "oneOf": [
            {
                "properties": {
                    "selector": {"const": 1},
                    "value": {"type": "object", "properties": {}},
                }
            },
            {
                "properties": {
                    "selector": {"const": True},
                    "value": {"type": "string"},
                }
            },
        ],
    }

    normalized = normalize_tool_arguments(
        {"selector": True, "value": '{"must": "remain text"}'},
        schema,
    )

    assert normalized == {
        "selector": True,
        "value": '{"must": "remain text"}',
    }


def test_normalizer_preserves_memory_list_string_selectors_and_decodes_page_size() -> None:
    arguments = {
        "scope": "project",
        "namespace_id": "mnemosyne",
        "collection_id": "null",
        "page_size": "2",
    }
    original = deepcopy(arguments)

    normalized = normalize_tool_arguments(
        arguments,
        MEMORY_LIST_TOOL["inputSchema"],
    )

    assert normalized == {
        "scope": "project",
        "namespace_id": "mnemosyne",
        "collection_id": "null",
        "page_size": 2,
    }
    assert arguments == original


def test_normalizer_preserves_native_null_and_cursor_text_for_memory_list() -> None:
    arguments = {
        "scope": "project",
        "namespace_id": "mnemosyne",
        "collection_id": None,
        "cursor": '{"looks":"structured"}',
    }

    normalized = normalize_tool_arguments(
        arguments,
        MEMORY_LIST_TOOL["inputSchema"],
    )

    assert normalized == arguments


def test_normalized_memory_list_arguments_reach_handler_validation() -> None:
    normalized = normalize_tool_arguments(
        {"scope": "project", "page_size": "2"},
        MEMORY_LIST_TOOL["inputSchema"],
    )

    result = handle_memory_list(
        normalized,
        list_operation=lambda selector, page_size, cursor: MemoryListResult(
            memories=(),
            page=MemoryListPage(
                number=1,
                count=0,
                total_count=0,
                total_pages=0,
                truncated=False,
                next_cursor=None,
            ),
        ),
    )

    assert result.get("isError") is not True

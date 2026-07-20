from typing import Any

from mnemosyne.memory.records import (
    ALLOWED_KINDS,
    KIND_DEFINITIONS,
    KindDefinition,
    MemoryOrigin,
)
from mnemosyne.memory.scopes import MemoryScope, SCOPE_DEFINITIONS, ScopeDefinition


IDENTIFIER_SCHEMA = {
    "type": "string",
    "minLength": 1,
    "maxLength": 64,
    "pattern": "^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$",
}
PUBLIC_ORIGINS = [
    MemoryOrigin.EXPLICIT_USER_STATEMENT.value,
    MemoryOrigin.USER_APPROVED_PROPOSAL.value,
]
PUBLIC_SCOPES = [definition.scope.value for definition in SCOPE_DEFINITIONS]
PUBLIC_NAMESPACE_KINDS = list(
    dict.fromkeys(
        kind
        for definition in SCOPE_DEFINITIONS
        for kind in definition.namespace_kinds
    )
)
PUBLIC_MEMORY_KINDS = list(
    dict.fromkeys(
        kind.value
        for definition in SCOPE_DEFINITIONS
        for kind in ALLOWED_KINDS[definition.scope]
    )
)
REQUIRED_FIELDS = [
    "scope",
    "namespace",
    "collection",
    "kind",
    "language",
    "title",
    "content",
    "tags",
    "origin",
]


def _format_kind_guidance(definitions: tuple[KindDefinition, ...]) -> str:
    return "; ".join(
        f"{definition.kind.value}: {definition.guidance}"
        for definition in definitions
    )


def _kind_description(definition: ScopeDefinition | None) -> str:
    if definition is not None:
        return (
            f"Writing guidance for {definition.scope.value} memory kinds: "
            f"{_format_kind_guidance(KIND_DEFINITIONS[definition.scope])}"
        )
    groups = " | ".join(
        f"{scope_definition.scope.value}: "
        f"{_format_kind_guidance(KIND_DEFINITIONS[scope_definition.scope])}"
        for scope_definition in SCOPE_DEFINITIONS
    )
    return (
        "Memory kind must match scope; the complete schema narrows this enum for "
        f"each scope. Writing guidance by scope: {groups}"
    )


def _nullable_text(maximum_length: int) -> dict[str, Any]:
    return {
        "anyOf": [
            {
                "type": "string",
                "minLength": 1,
                "maxLength": maximum_length,
                "pattern": "\\S",
            },
            {"type": "null"},
        ]
    }


def _scope_schema() -> dict[str, Any]:
    return {
        "type": "string",
        "description": (
            "Select the high-level domain that best describes the requested memory. "
            "Allowed values: "
            + "; ".join(
                f"{definition.scope.value}: {definition.description}"
                for definition in SCOPE_DEFINITIONS
            )
        ),
        "enum": PUBLIC_SCOPES,
    }


def _namespace_schema(
    definition: ScopeDefinition | None = None,
) -> dict[str, Any]:
    namespace_kinds = (
        list(definition.namespace_kinds)
        if definition is not None
        else PUBLIC_NAMESPACE_KINDS
    )
    kind_schema: dict[str, Any] = {
        "type": "string",
        "enum": namespace_kinds,
    }
    if definition is None:
        kind_schema["description"] = (
            "Namespace kind must match scope; the complete schema narrows this enum "
            "for each scope."
        )
    return {
        "type": "object",
        "properties": {
            "kind": kind_schema,
            "id": dict(IDENTIFIER_SCHEMA),
            "label": _nullable_text(100),
        },
        "required": ["kind", "id", "label"],
        "additionalProperties": False,
    }


def _collection_schema() -> dict[str, Any]:
    return {
        "anyOf": [
            {"type": "null"},
            {
                "type": "object",
                "properties": {
                    "id": dict(IDENTIFIER_SCHEMA),
                    "label": _nullable_text(100),
                },
                "required": ["id", "label"],
                "additionalProperties": False,
            },
        ]
    }


def _properties(
    definition: ScopeDefinition | None = None,
) -> dict[str, Any]:
    if definition is None:
        scope_schema = _scope_schema()
        memory_kinds = PUBLIC_MEMORY_KINDS
    else:
        scope_schema = {
            "const": definition.scope.value,
            "description": definition.description,
        }
        memory_kinds = [
            kind.value for kind in ALLOWED_KINDS[definition.scope]
        ]
    kind_schema: dict[str, Any] = {
        "type": "string",
        "enum": memory_kinds,
        "description": _kind_description(definition),
    }
    properties: dict[str, Any] = {
        "scope": scope_schema,
        "namespace": _namespace_schema(definition),
        "collection": _collection_schema(),
        "kind": kind_schema,
        "language": {
            "anyOf": [
                {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 35,
                    "pattern": "^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$",
                },
                {"type": "null"},
            ]
        },
        "title": _nullable_text(200),
        "content": {
            "type": "string",
            "minLength": 1,
            "maxLength": 4_000,
            "pattern": "\\S",
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1,
                "maxLength": 50,
                "pattern": "\\S",
            },
            "minItems": 0,
            "maxItems": 10,
            "uniqueItems": True,
        },
        "origin": {
            "type": "string",
            "enum": PUBLIC_ORIGINS,
        },
    }
    if definition is None or definition.scope is MemoryScope.PROJECT:
        properties["occurred_at"] = {
            "type": "string",
            "description": (
                "Required exactly for project event memory; omit it for every other "
                "memory kind. Use strict UTC-second form YYYY-MM-DDTHH:MM:SSZ."
            ),
            "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$",
        }
    if definition is None:
        properties["origin"]["description"] = (
            "Caller-supplied provenance context, not consent. Use "
            "explicit_user_statement for a direct user statement or "
            "user_approved_proposal for an approved proposed memory."
        )
    return properties


def _scope_branch(definition: ScopeDefinition) -> dict[str, Any]:
    branch: dict[str, Any] = {
        "type": "object",
        "properties": _properties(definition),
        "required": REQUIRED_FIELDS,
        "additionalProperties": False,
    }
    if definition.scope is MemoryScope.PROJECT:
        branch["allOf"] = [
            {
                "if": {"properties": {"kind": {"const": "event"}}},
                "then": {"required": ["occurred_at"]},
                "else": {"not": {"required": ["occurred_at"]}},
            }
        ]
    return branch


TOOL = {
    "name": "memory_remember",
    "description": (
        "Propose one bounded, non-sensitive memory for durable local storage. The "
        "exact arguments require user approval through the MCP client before every "
        "call. Never include secrets, credentials, private keys, payment-card or "
        "government-identifier values, unrelated personal details, paths, or "
        "server-owned record fields. Do not call when the client cannot require "
        "approval for this exact invocation."
    ),
    "inputSchema": {
        "type": "object",
        "properties": _properties(),
        "required": REQUIRED_FIELDS,
        "additionalProperties": False,
        "oneOf": [_scope_branch(definition) for definition in SCOPE_DEFINITIONS],
    },
}

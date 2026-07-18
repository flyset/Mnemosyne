from typing import Any

from mnemosyne.memory.records import ALLOWED_KINDS, MemoryOrigin
from mnemosyne.memory.scopes import SCOPE_DEFINITIONS, ScopeDefinition


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


def _namespace_schema(definition: ScopeDefinition) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "kind": {
                "type": "string",
                "enum": list(definition.namespace_kinds),
            },
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


def _scope_branch(definition: ScopeDefinition) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "scope": {
                "const": definition.scope.value,
                "description": definition.description,
            },
            "namespace": _namespace_schema(definition),
            "collection": _collection_schema(),
            "kind": {
                "type": "string",
                "enum": [
                    kind.value for kind in ALLOWED_KINDS[definition.scope]
                ],
            },
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
        },
        "required": REQUIRED_FIELDS,
        "additionalProperties": False,
    }


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
        "oneOf": [_scope_branch(definition) for definition in SCOPE_DEFINITIONS],
    },
}

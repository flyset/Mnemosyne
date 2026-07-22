from mymcp.memory.listing import (
    DEFAULT_MEMORY_LIST_PAGE_SIZE,
    MAX_MEMORY_LIST_CURSOR_LENGTH,
    MAX_MEMORY_LIST_PAGE_SIZE,
    MIN_MEMORY_LIST_PAGE_SIZE,
)
from mymcp.memory.normalization import IDENTIFIER_PATTERN
from mymcp.memory.scopes import SCOPE_DEFINITIONS


REQUEST_VARIANTS_DESCRIPTION = (
    "Valid argument combinations: (1) scope with optional page_size; "
    "(2) scope and namespace_id with optional collection_id and page_size; "
    "(3) scope and cursor; or (4) scope, namespace_id, and cursor with optional "
    "collection_id."
)


def _scope_schema() -> dict[str, object]:
    return {
        "type": "string",
        "description": (
            "Select the high-level memory scope to inventory. Allowed values: "
            + "; ".join(
                f"{definition.scope.value}: {definition.description}"
                for definition in SCOPE_DEFINITIONS
            )
            + f" {REQUEST_VARIANTS_DESCRIPTION}"
        ),
        "enum": [
            definition.scope.value for definition in SCOPE_DEFINITIONS
        ],
    }


IDENTIFIER_SCHEMA = {
    "type": "string",
    "pattern": f"^{IDENTIFIER_PATTERN.pattern}$",
}
NAMESPACE_SCHEMA = {
    **IDENTIFIER_SCHEMA,
    "description": (
        "Optional canonical namespace selector. Omit for scope-wide listing. It is "
        "required when collection_id is present and must repeat unchanged on a "
        "namespace continuation request."
    ),
}
COLLECTION_SCHEMA = {
    "description": (
        "Use only with namespace_id. When omitted, select collectionless records and "
        "every collection; null selects collectionless records only; a string selects "
        "one exact collection. On continuation, repeat the same presence and value."
    ),
    "oneOf": [IDENTIFIER_SCHEMA, {"type": "null"}],
}
PAGE_SIZE_SCHEMA = {
    "type": "integer",
    "description": (
        "Optional for initial requests only; omit when cursor is present."
    ),
    "minimum": MIN_MEMORY_LIST_PAGE_SIZE,
    "maximum": MAX_MEMORY_LIST_PAGE_SIZE,
    "default": DEFAULT_MEMORY_LIST_PAGE_SIZE,
}
CURSOR_SCHEMA = {
    "type": "string",
    "description": (
        "For continuation requests only, repeat the exact selector from the initial "
        "request and omit page_size."
    ),
    "minLength": 1,
    "maxLength": MAX_MEMORY_LIST_CURSOR_LENGTH,
}


TOOL = {
    "name": "memory_list",
    "description": (
        "List a complete bounded inventory of valid memories in one scope or canonical "
        "container. This read-only Tool returns compact selection metadata and "
        "inspect-compatible references without memory content, filesystem paths, or "
        "retrieval ranking. Use memory_inspect to retrieve one selected memory. "
        f"{REQUEST_VARIANTS_DESCRIPTION}"
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "scope": _scope_schema(),
            "namespace_id": NAMESPACE_SCHEMA,
            "collection_id": COLLECTION_SCHEMA,
            "page_size": PAGE_SIZE_SCHEMA,
            "cursor": CURSOR_SCHEMA,
        },
        "required": ["scope"],
        "additionalProperties": False,
        "oneOf": [
            {
                "not": {
                    "anyOf": [
                        {"required": ["namespace_id"]},
                        {"required": ["collection_id"]},
                        {"required": ["cursor"]},
                    ],
                }
            },
            {
                "required": ["namespace_id"],
                "not": {"required": ["cursor"]},
            },
            {
                "required": ["cursor"],
                "not": {
                    "anyOf": [
                        {"required": ["namespace_id"]},
                        {"required": ["collection_id"]},
                        {"required": ["page_size"]},
                    ]
                },
            },
            {
                "required": ["namespace_id", "cursor"],
                "not": {"required": ["page_size"]},
            },
        ],
    },
}

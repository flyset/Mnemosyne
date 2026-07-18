from mnemosyne.memory.normalization import IDENTIFIER_PATTERN, MEMORY_ID_PATTERN
from mnemosyne.memory.scopes import SCOPE_DEFINITIONS


def _scope_schema() -> dict[str, object]:
    return {
        "oneOf": [
            {
                "const": definition.scope.value,
                "description": definition.description,
            }
            for definition in SCOPE_DEFINITIONS
        ]
    }


IDENTIFIER_SCHEMA = {
    "type": "string",
    "pattern": f"^{IDENTIFIER_PATTERN.pattern}$",
}

TOOL = {
    "name": "memory_inspect",
    "description": (
        "Inspect one exact user-visible memory through a structured reference. "
        "This read-only Tool accepts no filesystem path or broad list selector and "
        "does not create, change, migrate, or delete memory."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "reference": {
                "description": (
                    "Select one canonical version-2 or legacy version-1 memory."
                ),
                "oneOf": [
                    {
                        "type": "object",
                        "properties": {
                            "schema_version": {"const": 2},
                            "scope": _scope_schema(),
                            "namespace_id": IDENTIFIER_SCHEMA,
                            "collection_id": {
                                "oneOf": [IDENTIFIER_SCHEMA, {"type": "null"}]
                            },
                            "id": {
                                "type": "string",
                                "pattern": f"^{MEMORY_ID_PATTERN.pattern}$",
                            },
                        },
                        "required": [
                            "schema_version",
                            "scope",
                            "namespace_id",
                            "collection_id",
                            "id",
                        ],
                        "additionalProperties": False,
                    },
                    {
                        "type": "object",
                        "properties": {
                            "schema_version": {"const": 1},
                            "scope": _scope_schema(),
                            "id": {
                                "type": "string",
                                "pattern": "^[A-Za-z0-9._-]{1,100}$",
                            },
                        },
                        "required": ["schema_version", "scope", "id"],
                        "additionalProperties": False,
                    },
                ],
            }
        },
        "required": ["reference"],
        "additionalProperties": False,
    },
}

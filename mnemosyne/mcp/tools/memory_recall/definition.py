from mnemosyne.memory.scopes import SCOPE_DEFINITIONS


TOOL = {
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
                "type": "string",
                "description": (
                    "Select the high-level domain that best describes the requested "
                    "memory. Allowed values: "
                    + "; ".join(
                        f"{definition.scope.value}: {definition.description}"
                        for definition in SCOPE_DEFINITIONS
                    )
                ),
                "enum": [
                    definition.scope.value for definition in SCOPE_DEFINITIONS
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

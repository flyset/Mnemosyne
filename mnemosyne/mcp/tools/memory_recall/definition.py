SCOPES = (
    "self",
    "relationship",
    "preference",
    "practice",
    "project",
    "knowledge",
)


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

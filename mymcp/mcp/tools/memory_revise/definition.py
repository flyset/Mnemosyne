from mymcp.mcp.tools._memory_revise import revise_input_schema


TOOL = {
    "name": "memory_revise",
    "description": (
        "Replace the complete mutable text of one exact canonical version-2 memory "
        "at its current revision. Every exact call requires MCP-client approval and "
        "preserves stable identity, language, provenance, lifecycle state, and "
        "creation time. Never include secrets, sensitive personal data, paths, "
        "legacy identities, immutable fields, lifecycle targets, or model-provided "
        "confirmation. Omit collection_label only when reference.collection_id is "
        "null; otherwise provide its complete string-or-null replacement. A "
        "disallowed_content refusal returns only a bounded field and reason for "
        "reviewing the original arguments. Do not obfuscate suspected sensitive "
        "data; retry only when the user confirms that the formatting is benign and "
        "approves the exact revised call."
    ),
    "inputSchema": revise_input_schema(),
}

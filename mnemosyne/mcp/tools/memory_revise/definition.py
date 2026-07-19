from mnemosyne.mcp.tools._memory_revise import revise_input_schema


TOOL = {
    "name": "memory_revise",
    "description": (
        "Replace the complete mutable text of one exact canonical version-2 memory "
        "at its current revision. Every exact call requires MCP-client approval and "
        "preserves stable identity, language, provenance, lifecycle state, and "
        "creation time. Never include secrets, sensitive personal data, paths, "
        "legacy identities, immutable fields, lifecycle targets, or model-provided "
        "confirmation."
    ),
    "inputSchema": revise_input_schema(),
}

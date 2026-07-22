from mymcp.mcp.tools._memory_lifecycle import lifecycle_input_schema


TOOL = {
    "name": "memory_restore",
    "description": (
        "Restore one exact archived canonical version-2 memory at its expected "
        "revision. This mutation returns the record to normal recall and accepts "
        "no filesystem path, legacy reference, or record content."
    ),
    "inputSchema": lifecycle_input_schema(),
}

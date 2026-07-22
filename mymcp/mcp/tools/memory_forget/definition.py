from mymcp.mcp.tools._memory_lifecycle import lifecycle_input_schema


TOOL = {
    "name": "memory_forget",
    "description": (
        "Permanently forget one exact archived canonical version-2 memory at its "
        "expected revision. This irreversible mutation physically removes the "
        "source record without creating a tombstone and accepts no filesystem "
        "path, legacy reference, record content, or confirmation field."
    ),
    "inputSchema": lifecycle_input_schema(),
}

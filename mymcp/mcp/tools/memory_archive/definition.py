from mymcp.mcp.tools._memory_lifecycle import lifecycle_input_schema


TOOL = {
    "name": "memory_archive",
    "description": (
        "Archive one exact canonical version-2 memory at its expected revision. "
        "This mutation excludes the record from normal recall without deleting it "
        "and accepts no filesystem path, legacy reference, or record content."
    ),
    "inputSchema": lifecycle_input_schema(),
}

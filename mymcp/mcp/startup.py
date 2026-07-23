from mymcp.mcp.composition import compose_tool_registry
from mymcp.mcp.integrations.mnemosyne import mnemosyne_integration


REGISTRY = compose_tool_registry((mnemosyne_integration,))

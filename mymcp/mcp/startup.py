from mymcp.mcp.integrations.mnemosyne import compose_mnemosyne_registry
from mymcp.settings import get_memory_tool_settings


REGISTRY = compose_mnemosyne_registry(get_memory_tool_settings())

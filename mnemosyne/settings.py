import os
from pathlib import Path


SERVER_NAME = "mnemosyne"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"
APP_TITLE = "Mnemosyne MCP Server"

MEMORY_ROOT_ENV = "MNEMOSYNE_MEMORY_ROOT"


def get_memory_root() -> Path:
    configured_root = os.getenv(MEMORY_ROOT_ENV)
    if configured_root:
        return Path(configured_root).expanduser()
    return Path.home() / ".mnemosyne" / "memory"

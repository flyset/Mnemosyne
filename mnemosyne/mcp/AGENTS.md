# MCP Scope Rules

- Own MCP message normalization, JSON-RPC response helpers, method dispatch, tool registration, and tool handlers here.
- Keep tool behavior narrowly scoped, explicit, and independently callable through the registry.
- Preserve stable public tool names, schemas, result shapes, and JSON-RPC error behavior; document migration when changing any of them.
- Validate tool-owned user inputs. Do not add broad ambient access, shell execution, or unrestricted filesystem access.
- Keep HTTP transport concerns in `mnemosyne/routes/`.

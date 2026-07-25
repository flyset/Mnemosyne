# MCP Scope Rules

- This is the MyMCP host's MCP layer, currently dispatching a runtime-bound
  Mnemosyne 0.1.4-compatible surface through the trusted 0.1.0 adapter; do not
  assume plugin extraction or external activation exists.
- Own MCP message normalization, JSON-RPC response helpers, method dispatch, tool registration, and tool handlers here.
- Keep tool behavior narrowly scoped, explicit, and independently callable through the registry.
- Dispatch only through an explicitly supplied runtime; generic MCP modules must
  not import concrete Mnemosyne adapters or bootstrap production state.
- Keep trusted effect and consent metadata internal; do not project it as public
  MCP annotations without an explicit public-contract change.
- Preserve stable public tool names, schemas, result shapes, and JSON-RPC error behavior; document migration when changing any of them.
- Validate tool-owned user inputs. Do not add broad ambient access, shell execution, or unrestricted filesystem access.
- Keep HTTP transport concerns in `mymcp/routes/`.

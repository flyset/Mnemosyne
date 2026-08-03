# MCP Scope Rules

- This is the MyMCP host's MCP layer, dispatching the runtime-bound
  MyMCP/`mymcp` `0.6.0` endpoint surface through the extracted trusted bundled
  Mnemosyne 0.3.0 adapter. Static bootstrap validates bundled parity and enabled
  schema-2 external manifests before any external import, then composes one
  immutable runtime. Mnemosyne Tool and domain compatibility remain preserved;
  schema 1 retains `enabled_plugin_unsupported` compatibility. Authentication
  remains upstream and supplies only normalized principal context.
- Own MCP message normalization, JSON-RPC response helpers, method dispatch,
  generic tool registration, schema-aware argument normalization, and host-owned
  `list_tools` here. Mnemosyne Tool definitions and handlers belong under
  `mymcp/plugins/mnemosyne/mcp/tools/`.
- Keep tool behavior narrowly scoped, explicit, and independently callable through the registry.
- Dispatch only through an explicitly supplied runtime; generic MCP modules must
  not import concrete Mnemosyne adapters or bootstrap production state.
- Keep trusted effect and consent metadata internal; do not project it as public
  MCP annotations without an explicit public-contract change.
- Preserve stable public tool names, schemas, result shapes, and JSON-RPC error behavior; document migration when changing any of them.
- Validate tool-owned user inputs. Do not add broad ambient access, shell execution, or unrestricted filesystem access.
- Keep HTTP transport concerns in `mymcp/routes/`.
- Remain Authentication-protocol-neutral; principal carrying belongs to the
  host-owned application boundary.

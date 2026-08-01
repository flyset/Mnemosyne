# Route Scope Rules

- This is the MyMCP host's HTTP transport layer for the runtime-bound
  MyMCP/`mymcp` `0.4.0` external startup-composition runtime and its compatible
  bundled Mnemosyne plugin surface. Host configuration schemas 1 and 2 are
  startup-only; external composition is bootstrap-owned. The public-host cutover was released as `0.2.0`; its
  extraction, repository migration, operational verification, and release
  publication are complete. The prior `0.2.1` compatibility build remains
  historical; gateway governance remains deferred.
- Own HTTP paths, request and response transport, and lightweight operational endpoints here.
- Keep routes thin: delegate MCP parsing, dispatch, and tool execution to `mymcp/mcp/`.
- Bind routers to an explicitly supplied dispatcher; routes must not bootstrap or
  cache a global runtime. Production bootstrap belongs to the application factory
  and `mymcp/host/bootstrap.py`.
- Do not put memory policy, tool business logic, or protocol semantics in route handlers.
- Preserve the intentionally small HTTP surface; prefer MCP methods and tools over new HTTP endpoints.

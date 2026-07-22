# Route Scope Rules

- This is the MyMCP host's HTTP transport layer for the currently in-process
  Mnemosyne memory domain; do not assume plugin extraction exists.
- Own HTTP paths, request and response transport, and lightweight operational endpoints here.
- Keep routes thin: delegate MCP parsing, dispatch, and tool execution to `mymcp/mcp/`.
- Do not put memory policy, tool business logic, or protocol semantics in route handlers.
- Preserve the intentionally small HTTP surface; prefer MCP methods and tools over new HTTP endpoints.

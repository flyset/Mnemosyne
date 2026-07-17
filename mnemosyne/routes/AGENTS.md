# Route Scope Rules

- Own HTTP paths, request and response transport, and lightweight operational endpoints here.
- Keep routes thin: delegate MCP parsing, dispatch, and tool execution to `mnemosyne/mcp/`.
- Do not put memory policy, tool business logic, or protocol semantics in route handlers.
- Preserve the intentionally small HTTP surface; prefer MCP methods and tools over new HTTP endpoints.

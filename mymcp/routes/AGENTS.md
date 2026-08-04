# Route Scope Rules

- This is the MyMCP host's HTTP transport layer for the runtime-bound
  MyMCP/`mymcp` `0.8.0` Authentication and registered-session surface and its compatible bundled
  Mnemosyne plugin surface. Host configuration schemas 1 through 5 are
  startup-only; external composition is bootstrap-owned. The public-host cutover was released as `0.2.0`; its
  extraction, repository migration, operational verification, and release
  publication are complete. The prior `0.2.1` compatibility build remains
  historical; `operator-bearer-v1` and the schema-5 `oauth-jwt-jwks-v1`
  (enabled OAuth) production registered adapters are mutually exclusive under
  schema 5. Enabled OAuth conditionally adds only RFC 9728 protected-resource
  metadata and its exact body-free 401 Bearer challenge; its loopback HTTP
  resource is a local interoperability exception. Registered sessions are
  host-owned and reauthenticated per request; Governance remains deferred.
- Own HTTP paths, request and response transport, and lightweight operational endpoints here.
- Extract bounded host-defined Authentication evidence and return an empty `401`
  before MCP streaming, body parsing, logging, or dispatch on failure.
- Keep routes thin: delegate MCP parsing, dispatch, and tool execution to `mymcp/mcp/`.
- Extract only bounded singleton session transport headers after Authentication;
  delegate session lifecycle to the host application boundary and never log them.
- Bind routers to an explicitly supplied dispatcher; routes must not bootstrap or
  cache a global runtime. Production bootstrap belongs to the application factory
  and `mymcp/host/bootstrap.py`.
- Do not put memory policy, tool business logic, or protocol semantics in route handlers.
- Preserve the intentionally small HTTP surface; prefer MCP methods and tools over new HTTP endpoints.

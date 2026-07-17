# Glossary

- **Awareness** — read-only, least-privilege inspection of safe local environment signals.
- **Cold memory** — durable memory retrieved only when relevant; it remains user-governed and easy to delete.
- **Consent** — explicit user authorization for a durable memory or state-changing action.
- **Hot memory** — a small, bounded working set loaded at session start from durable memory.
- **MCP tool** — a narrowly scoped capability exposed through the Model Context Protocol.
- **Memory** — user-approved durable context, such as a preference or stable fact; never a secret store.
- **Reflection** — operational agent configuration, such as policies, checklists, and failure-mode mitigations; not personal facts.
- **Session context** — selectively retrieved summaries or excerpts from prior agent sessions.

## Contract Terms

- **Public MCP contract** — the externally observable behavior of endpoints, protocol methods, tool names, input schemas, and result or error shapes.
- **Tool schema** — the declared name, description, and input contract for an MCP tool.
- **JSON-RPC error** — a protocol-shaped error response with a stable code and explanatory message.
- **Invalid parameters** — JSON-RPC error `-32602`, returned when a request supplies a non-object `params` value; the valid request ID is preserved.
- **Invalid request** — JSON-RPC error `-32600`, returned with `id: null` when the top-level request envelope is not an object.

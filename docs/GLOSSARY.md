# Glossary

- **Awareness** — read-only, least-privilege inspection of safe local environment signals.
- **Cold memory** — durable memory retrieved only when relevant; it remains user-governed and easy to delete.
- **Consent** — explicit user authorization for a durable memory or state-changing action.
- **Hot memory** — a small, bounded working set loaded at session start from durable memory.
- **MCP tool** — a narrowly scoped capability exposed through the Model Context Protocol.
- **Memory** — user-approved durable context, such as a preference or stable fact; never a secret store.
- **Memory recall request** — a narrow, model-generated description of user-specific context that could materially affect the current response.
- **Memory scope** — the single required high-level category describing what a memory recall request concerns: `self`, `relationship`, `preference`, `practice`, `project`, or `knowledge`.
- **Recall tags** — optional, bounded, free-form descriptive labels attached to a memory recall request; they currently define no filtering, ranking, or other retrieval behavior.
- **Recall request surface** — a non-retrieving MCP tool that validates memory recall requests and returns a stable unavailable result without server-side request persistence.
- **Reflection** — operational agent configuration, such as policies, checklists, and failure-mode mitigations; not personal facts.
- **Session context** — selectively retrieved summaries or excerpts from prior agent sessions.

## Contract Terms

- **Public MCP contract** — the externally observable behavior of endpoints, protocol methods, tool names, input schemas, and result or error shapes.
- **Tool schema** — the declared name, description, and input contract for an MCP tool.
- **JSON-RPC error** — a protocol-shaped error response with a stable code and explanatory message.
- **MCP notification** — an MCP message without an `id`; it receives HTTP `202` with no JSON-RPC response body.
- **Invalid parameters** — JSON-RPC error `-32602`, returned when a request supplies a non-object `params` value; the valid request ID is preserved.
- **Invalid request** — JSON-RPC error `-32600`, returned with `id: null` when the top-level request envelope is not an object.

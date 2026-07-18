# Glossary

- **Awareness** — read-only, least-privilege inspection of safe local environment signals.
- **Cold memory** — durable memory retrieved only when relevant; it remains user-governed and easy to delete.
- **Consent** — explicit user authorization for a durable memory or state-changing action; for future mutation Tools it is enforced by per-call MCP-client approval, not a model-provided field.
- **Hot memory** — a small, bounded working set loaded at session start from durable memory.
- **MCP tool** — a narrowly scoped capability exposed through the Model Context Protocol.
- **Memory** — user-approved durable context, such as a preference or stable fact; never a secret store.
- **Legacy memory record** — a compatible schema-version-1 JSON record with ID, content, and optional title/tags; it remains readable without background rewriting or invented metadata.
- **Memory collection** — an optional stable organizational partition beneath a version-2 namespace; its ID affects the path while its mutable label does not.
- **Memory kind** — the controlled semantic role of a version-2 record, such as `preference`, `decision`, `constraint`, or `reference`; it is constrained by scope and is not a path segment.
- **Memory lifecycle** — the active/archived state and positive revision of a version-2 record; archived records are inspectable but excluded from normal recall, while forgotten records are physically absent.
- **Memory namespace** — the required stable routing identity beneath a scope, such as a project, relationship subject, preference domain, practice domain, self aspect, or knowledge topic.
- **Memory provenance** — bounded metadata describing an approved record's origin and server-controlled recording mechanism; it contains no prompt, transcript, or unverifiable consent claim.
- **Memory record** — one user-visible, versioned JSON source-of-truth file; canonical version-2 records separate scope, namespace, collection, kind, language, content, tags, provenance, timestamps, and lifecycle.
- **Memory reference** — a structured scope, namespace ID, optional collection ID, and record ID used by lifecycle operations instead of a client-supplied path.
- **Memory root** — the operator-controlled local directory containing the six fixed memory scope directories; it defaults to `~/.mnemosyne/memory`.
- **Memory recall request** — a narrow, model-generated description of user-specific context that could materially affect the current response.
- **Memory scope** — the single required high-level category describing what a memory recall request concerns: `self`, `relationship`, `preference`, `practice`, `project`, or `knowledge`.
- **Memory scope directory** — one fixed top-level directory beneath the memory root selected by a validated memory scope; recall never accepts a client-supplied path.
- **Shared memory domain** — the tool-independent `mnemosyne/memory/` package that owns scopes, records, normalization, paths, storage, retrieval, lifecycle policy, and shared errors.
- **Recall tags** — optional, bounded, free-form descriptive labels attached to a memory recall request; exact normalized overlap with record tags is a ranking signal, not a required filter.
- **Recall match evidence** — the sorted terms and tags explaining which request signals matched a returned memory record; it excludes paths and internal scores.
- **Memory recall** — read-only retrieval that validates a recall request, searches only its selected scope directory, and returns bounded approved records without persisting the request.
- **Memory mutation** — an explicit create, revise, archive, restore, relocate, or physical-forget operation; domain primitives are disabled by default and no mutation MCP Tool is currently exposed.
- **Reflection** — operational agent configuration, such as policies, checklists, and failure-mode mitigations; not personal facts.
- **Session context** — selectively retrieved summaries or excerpts from prior agent sessions.

## Contract Terms

- **Public MCP contract** — the externally observable behavior of endpoints, protocol methods, tool names, input schemas, and result or error shapes.
- **Tool schema** — the declared name, description, and input contract for an MCP tool.
- **JSON-RPC error** — a protocol-shaped error response with a stable code and explanatory message.
- **MCP notification** — an MCP message without an `id`; it receives HTTP `202` with no JSON-RPC response body.
- **Invalid parameters** — JSON-RPC error `-32602`, returned when a request supplies a non-object `params` value; the valid request ID is preserved.
- **Invalid request** — JSON-RPC error `-32600`, returned with `id: null` when the top-level request envelope is not an object.
- **No matches** — a successful memory recall result with `status: no_matches` and an empty `memories` array when the selected scope is absent or contains no positively ranked valid record.
- **Retrieval error** — a Tool error indicating that a validated recall request could not safely read its source or exceeded the candidate limit; it does not expose internal filesystem details.

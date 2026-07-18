# TRACK 003 [COMPLETED]: memory recall request surface

Track
- ID: TRACK_003
- Repository: Mnemosyne
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_003_COMPLETED_memory_recall_request_surface.md

Problems (PORE)
- P1: As an agent developer, I cannot observe how models request memory through the MCP client because Mnemosyne exposes no recall request surface.

Objective
- Expose a read-only `memory_recall` MCP request surface that validates model calls and returns a stable unavailable result without retrieving or persisting memory requests.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Preserve local-first, single-user, least-privilege, and explicit-user-governance principles.
- The capability must not create, update, or delete memory records.
- The capability must not access a memory source, generate embeddings, search, rank, or return memory records.
- Do not store secrets, credentials, or unrestricted conversation transcripts.
- The server must not persist recall requests in this Track.

Acceptance criteria
- [x] A1) [P1] `tools/list` exposes a documented `memory_recall` Tool definition with a narrow input schema.
- [x] A2) [P1] Calls are validated without accessing any memory source or retrieval dependency.
- [x] A3) [P1] Every valid call returns a stable, documented `retrieval_unavailable` outcome containing no memory records.
- [x] A4) [P1] Calls remain visible through the MCP client's existing Tool-call/session representation, while Mnemosyne creates no dedicated recall-request record.
- [x] A5) [P1] Automated tests cover Tool registration, request validation, the no-retrieval and no-persistence boundaries, and placeholder outcomes.
- [x] A6) [P1] Public documentation explains the probe's purpose and the limitation that exposing its Tool definition may itself influence model behavior.

Why now / impact
- Memory is Mnemosyne's core intended capability. A narrow request surface makes model calls visible through the MCP client before retrieval, storage, embedding, or task-dependency mechanics are chosen.

Scope
- In scope:
  - The initial `memory_recall` MCP Tool definition, registration, dispatch, handler, and request validation.
  - A stable placeholder outcome that clearly states retrieval is unavailable and returns no memories.
  - Focused automated tests and required public-contract documentation updates.
- Out of scope:
  - Memory records, schemas, sources, storage, indexing, and lifecycle behavior.
  - Retrieval engines, datastore adapters, embeddings, search, ranking, thresholds, match explanations, and returned memories.
  - `memory_remember`, `memory_forget`, mutation, deletion, compaction, automated hygiene, or automatic conversation extraction.
  - Dependency graphs, task-specific retrieval rules, or silent context injection.
  - Selecting, installing, provisioning, or operating any memory, retrieval, or embedding technology.
  - A dedicated recall-request event store, retention system, redaction pipeline, or analysis capability.

Milestones
- [x] M1) Define the Tool, placeholder-result, and client-visibility contracts.
- [x] M2) Implement and test the probe registration, validation, and no-retrieval boundary.
- [x] M3) Validate and document the end-to-end request-surface behavior.

Risks / decisions
- Risk: Prematurely encoding task dependencies duplicates model reasoning and hardens unproven assumptions.
- Decision: The agent decides whether and how to call `memory_recall`; this Track observes that request without implementing retrieval.
- Risk: A placeholder outcome may teach agents that recall is unavailable and affect subsequent calls.
- Decision: Treat the initial call decision as the primary observation and distinguish later behavior after the placeholder response.
- Risk: The Tool definition enters model context and may influence the behavior being observed.
- Decision: Document this observer effect; Track 003 exposes the request surface but does not claim that visible calls represent behavior without the Tool present.
- Risk: Visibility depends on the MCP client retaining or displaying Tool calls.
- Decision: Use OpenCode's existing Tool-call/session visibility for now; Mnemosyne does not duplicate those records.

Open questions
- [x] Q1) What exact `memory_recall` Tool definition and input schema should be exposed to models?
- [x] Q2) What exact placeholder result and error outcomes clearly distinguish unavailable retrieval from invalid requests?
- [x] Q3) How are recall calls observed without adding server-side persistence?

Decision log
- Decision: Start with read-only recall to observe actual agent queries before introducing memory writes or dependency-resolution rules.
- Decision: Track 003 stops at request receipt and observation; it does not connect code to memory data or choose retrieval technology.
- Decision: Valid calls return a stable `retrieval_unavailable` outcome with no memory records.
- Decision: Track 003 provides the request surface only; visible client-side calls may inform later retrieval decisions outside this Track.
- Decision: The Tool definition's observer effect is an explicit limitation, not an experiment performed by this Track.
- Decision (Q1): Start with one free-form `query` argument and the following Tool definition; it may be revised after evidence accumulates during normal use.

```json
{
  "name": "memory_recall",
  "description": "Submit a narrowly scoped request for user-approved memory that could materially improve or change the response. Use when user-specific facts, preferences, constraints, prior decisions, or ongoing projects are relevant, or when the user asks what is remembered. Do not use for general-knowledge questions. Do not include the full conversation or unrelated personal details.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Describe only the user-specific information needed for the current request.",
        "minLength": 1,
        "maxLength": 1000
      }
    },
    "required": ["query"],
    "additionalProperties": false
  }
}
```

- Decision (Q2): A valid call returns a normal MCP Tool result whose text content is `{"status":"retrieval_unavailable"}`. It is not a Tool error because the instrumentation request succeeded. Invalid Tool arguments return `isError: true` with text content containing `status: invalid_request`, code `invalid_query`, and the stable message `query must be a non-empty string of at most 1000 characters`. JSON-RPC errors remain reserved for protocol-level failures and unknown tools.
- Decision (Q3): For now, recall calls are observed only through OpenCode's existing Tool-call and session representation. Mnemosyne creates no dedicated recall-request record.

Plan (execution steps)
- [x] S1) Resolve Q1-Q3 and record the Tool, placeholder-result, and client-visibility decisions.
- [x] S2) Move Track 003 to ACTIVE (folder, filename, and title status).
- [x] S3) Read the ACTIVE Track and write focused failing tests for the selected probe contract and no-retrieval boundary.
- [x] S4) Implement the smallest Tool definition, registration, validation, and stable no-retrieval outcome that pass S3.
- [x] S5) Run the full relevant validation suite, perform a direct MCP protocol check, finalize documentation, and update inventory and evidence.
- [x] S6) Move Track 003 to COMPLETED (folder, filename, and title status) and record completion notes.

Current inventory
- `mnemosyne/mcp/` owns MCP parsing, method dispatch, protocol helpers, tool registry, and tool handlers.
- `mnemosyne/mcp/tools/list_tools/` exposes the existing `list_tools` capability.
- `mnemosyne/mcp/tools/memory_recall/` exposes the selected Tool definition, validates `query`, and returns stable `retrieval_unavailable` or `invalid_query` outcomes without accessing memory data.
- `mnemosyne/mcp/tools/registry.py` registers and dispatches both Tools.
- `mnemosyne/routes/mcp.py` provides the `/mcp` transport; `mnemosyne/app.py` remains transport assembly.
- No memory storage, retrieval provider, embedding provider, recall-request event store, or memory MCP contract currently exists.
- Mnemosyne does not persist `memory_recall` requests; visibility remains the MCP client's responsibility.
- `README.md`, `VISION.md`, `docs/ARCHITECTURE.md`, `docs/AI_WORKFLOW.md`, and `docs/GLOSSARY.md` define local-first, user-governed, explicit-tool, and contract/documentation requirements.

Artifacts
- Design discussion: session `ses_08f493016ffe3gMRm2mT0ckhxS`.
- TDD evidence: focused tests initially failed because `mnemosyne.mcp.tools.memory_recall` did not exist; after the smallest implementation, 22 focused tests passed.
- Final validation evidence: `PYENV_VERSION=3.13.5 python -m pytest tests` passed 33 tests.
- Final direct MCP evidence: a temporary local server returned `memory_recall` from `tools/list` and returned `{"status":"retrieval_unavailable"}` for a valid `tools/call` request.

Completion notes
- Completed the non-retrieving `memory_recall` request surface with the selected model-facing Tool definition and one required free-form `query` argument.
- Valid calls return `{"status":"retrieval_unavailable"}`; invalid queries return the stable `invalid_query` Tool error.
- Mnemosyne does not access memory data or create a dedicated recall-request record; call visibility remains with the MCP client.
- Final automated validation passed all 33 tests, and direct MCP checks verified Tool discovery and the placeholder call result.

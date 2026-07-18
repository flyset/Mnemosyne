# TRACK 007 [DRAFT]: consent-gated memory remember

Track
- ID: TRACK_007
- Repository: Mnemosyne
- Branch: main
- Current path: .backlog/DRAFT/2026/TRACK_007_DRAFT_consent_gated_memory_remember.md

Problems (PORE)
- P1: As a user, I cannot ask an MCP-compatible agent to save an approved memory, because Mnemosyne exposes recall but no durable creation Tool.
- P2: As an operator, I cannot safely enable agent-initiated memory creation, because mutation is disabled inside the shared service and there is no server-side Tool gate paired with an MCP-client per-call approval rule.
- P3: As a Tool caller, I cannot reliably distinguish creation, active duplicate, archived duplicate, validation refusal, policy refusal, conflict, disabled, and storage-failure outcomes, because no public `memory_remember` contract exists.
- P4: As a user governing durable context, I cannot verify that remember calls avoid secrets, uncontrolled paths, hidden operational fields, and content-bearing logs, because those public mutation boundaries have not been specified or tested.

Objective
- Expose one narrow, disabled-by-default `memory_remember` MCP Tool that persists an explicitly approved canonical version-2 record through the shared memory service only when the operator enables the Tool and the MCP client asks for approval on every exact call.

Non-negotiables
- This Track remains planning-only while DRAFT; no implementation or implementation-driving tests begin until all blocking questions are resolved and the Track is moved to ACTIVE.
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- `mnemosyne/memory/` remains the owner of memory meaning, validation, duplicate policy, atomic persistence, and mutation-disabled lifecycle behavior; the MCP package is a thin adapter.
- `memory_remember` is disabled and absent from Tool discovery by default. Enabling the MCP server itself does not enable memory mutation.
- Durable mutation requires the MCP client's approval of the exact Tool call. No `confirmed`, `approved`, `consent`, or equivalent model-supplied argument is accepted as evidence of consent.
- Clients that cannot require per-call approval, and OpenCode sessions running auto-approval, must not be used with the mutation Tool enabled.
- The Tool accepts no filesystem path, record ID, timestamp, lifecycle state, revision, or `recorded_via` value from the caller; those operational fields remain server-controlled.
- Memory remains local-first, single-user, filesystem-backed, directly visible, and easy to delete.
- The Tool must not store secrets, tokens, private keys, credentials, or disallowed sensitive personal data. The enforceable refusal boundary must be resolved before activation.
- Validation, errors, results, and logs must not disclose absolute paths or unrelated records. Logs must not include title, content, tags, complete arguments, or rejected secret material.
- Automated tests use temporary roots only. Direct MCP checks may write only approved temporary records and must remove all resulting data.
- No commit or push occurs unless explicitly requested.

Acceptance criteria
- [ ] A1) [P1, P2] With mutation enablement absent or false, `tools/list` and `list_tools` do not advertise `memory_remember`, direct dispatch treats it as unknown, and no memory directory or file is created.
- [ ] A2) [P1, P2] With explicit operator enablement true, Tool discovery advertises exactly one new `memory_remember` Tool with a bounded schema derived from canonical shared scopes and dimensions; it accepts no path or server-owned operational field.
- [ ] A3) [P1] An approved valid call persists exactly one canonical active version-2 record at the deterministic shared-domain location with server-generated ID, provenance mechanism, timestamps, and revision, using existing private atomic store behavior.
- [ ] A4) [P3] Exact active and archived duplicates return distinct stable non-writing outcomes identifying the existing record without creating a second file or exposing its path.
- [ ] A5) [P3, P4] Invalid scope dimensions, malformed or oversized input, forbidden fields, disallowed content, disabled mutation, candidate overflow, write conflict, and storage failure produce stable bounded Tool outcomes and leave durable memory unchanged.
- [ ] A6) [P2, P4] The repository OpenCode configuration uses the validated prefixed permission key for `memory_remember` with action `ask`; documentation states that configuration reload requires restart and that OpenCode auto-approval defeats `ask` and therefore must not be used while mutation is enabled.
- [ ] A7) [P2] Client denial results in no request reaching Mnemosyne and no durable write; approved execution presents the exact scope, namespace, optional collection, kind, language, title, content, tags, and origin to the user before execution.
- [ ] A8) [P3, P4] Success, duplicate, refusal, conflict, and failure logs contain only the approved bounded operational metadata and never memory content, title, tags, absolute paths, complete arguments, or rejected sensitive values.
- [ ] A9) [P1, P2, P3, P4] Focused automated tests, the full suite, whitespace validation, direct temporary-root MCP checks, and configured-client checks when available pass without altering recall behavior or retaining test memory.
- [ ] A10) [P1, P2, P4] `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` describe the exact Tool contract, default-off enablement, client approval boundary, filesystem effects, outcomes, no-secret policy, logging, and limitations.

Why now / impact
- Track 006 established and tested the canonical shared record, path, store, duplicate, and lifecycle service contracts. Exposing remember now can reuse those foundations without duplicating domain logic, and it is the smallest step that turns Mnemosyne from externally read-only recall into user-governed durable memory.
- Defining operator enablement, client approval, refusal policy, and observable outcomes before the first public mutation prevents accidental writes and incompatible durable records from becoming part of the contract.

Scope
- In scope:
  - One public MCP Tool named `memory_remember`.
  - A dedicated `mnemosyne/mcp/tools/memory_remember/` definition, handler, and package export.
  - Explicit server-side operator configuration that controls Tool discovery and dispatch and defaults to disabled.
  - Thin conversion of validated Tool arguments into the existing shared `MemoryDraft` and `MemoryService.remember()` contracts.
  - Canonical scope, namespace, optional collection, kind, language, title, content, tags, and bounded origin inputs.
  - Stable result and error mapping for remembered, active duplicate, archived duplicate, validation/policy refusal, disabled mutation, candidate overflow, conflict, and storage failure.
  - Content-free mutation logging with exact allowed metadata and outcomes.
  - OpenCode per-call `ask` permission for the prefixed mutation Tool, schema validation, restart instructions, and explicit auto-approval warning.
  - Temporary-root automated and direct MCP validation, plus configured-client approval/denial checks when available.
  - Public documentation and architecture/glossary updates.
- Out of scope:
  - `memory_inspect`, `memory_revise`, `memory_archive`, `memory_restore`, `memory_forget`, relocation, reclassification, migration, or bulk mutation Tools.
  - Automatic extraction from conversations, background writes, implicit consent, scheduled memory creation, or agent-authored approval claims.
  - Revising or migrating legacy version-1 records.
  - Caller-selected IDs, paths, timestamps, revisions, lifecycle states, or provenance mechanisms.
  - Semantic duplicate detection, contradiction resolution, embeddings, vector search, persistent indexes, manifests, tombstones, or hidden history.
  - Multi-user authorization, remote storage, encryption, cross-process writer coordination, or audit-log infrastructure.
  - Storing secrets, credentials, private keys, or disallowed sensitive personal data.

Milestones
- [ ] M1) Complete public Tool, enablement, consent, refusal, result, error, and logging contracts are resolved and the Track is eligible for ACTIVE.
- [ ] M2) Default-off Tool registration and OpenCode per-call approval configuration are implemented and tested without exposing mutation by default.
- [ ] M3) Enabled `memory_remember` validation and shared-service adaptation pass focused TDD, duplicate, refusal, conflict, and logging coverage.
- [ ] M4) Documentation, full validation, temporary direct MCP checks, and configured-client approval/denial evidence are complete and no test memory remains.

Risks / decisions
- Risk: Merely exposing a mutation Tool can permit automatic durable writes when a client defaults unknown Tools to allow or runs in auto-approval mode.
- Risk: A model-provided confirmation field creates the appearance of consent without an enforceable user boundary.
- Risk: A broad or hand-maintained Tool schema can drift from shared scope, namespace, kind, and normalization rules.
- Risk: Returning or logging complete records can unnecessarily duplicate sensitive memory content outside the visible source-of-truth file.
- Risk: Naive secret detection can both miss dangerous values and reject harmless memory; the enforceable policy and its limitations must be explicit.
- Risk: Dynamic Tool availability may be cached by a running MCP client, requiring server and client restart/reconnection after enablement changes.
- Risk: Duplicate discovery remains bounded by the shared store candidate limit and can refuse creation rather than risk an unchecked duplicate.
- Decision: This Track exposes remember only; lifecycle mutation Tools require later independent Tracks and approval contracts.
- Decision: The existing shared domain and filesystem files remain the only source of memory truth; the MCP adapter introduces no second schema or index.
- Decision: The exact proposed memory is visible in Tool arguments before client approval, while the Tool result and server logs remain minimized.
- Decision: Server-generated IDs, timestamps, lifecycle, revision, and `recorded_via` remain outside the public input schema.
- Decision: Default-off means absent from both discovery and dispatch, not merely a handler that advertises itself and then returns `mutation_disabled`.
- Decision: Automated and direct protocol validation use isolated temporary roots and physically remove resulting files.

Open questions
- [ ] Q1) What is the exact JSON Schema for each caller-owned field, including required versus nullable labels/title/collection, enum derivation, and whether `origin` permits both explicit statements and user-approved proposals?
- [ ] Q2) What is the exact operator setting name, accepted true/false syntax, invalid-value behavior, and startup/discovery behavior for enabling only `memory_remember` without implicitly enabling future mutation Tools?
- [ ] Q3) How will registry construction remain deterministic and independently testable when Tool availability depends on runtime settings?
- [ ] Q4) What exact success and duplicate result envelopes expose enough identity and lifecycle state for later inspection while omitting path and unnecessary content?
- [ ] Q5) Which shared validation/domain errors become ordinary structured Tool outcomes versus `isError` Tool failures, and what stable codes/messages does each use?
- [ ] Q6) What conservative, testable no-secret and sensitive-data policy is enforceable at the server boundary, what fields does it inspect, and how are unavoidable false positives/negatives documented without logging rejected values?
- [ ] Q7) What exact mutation log events, levels, fields, and bounded formatting prove an operation occurred without retaining memory content or absolute paths?
- [ ] Q8) What exact OpenCode permission key is produced from server name `mnemosyne` and Tool name `memory_remember`, and how will schema validity, interactive `ask`, denial/no-call, one-call approval, session-wide approval, auto-mode risk, and restart behavior be verified?
- [ ] Q9) Should the Tool be omitted entirely when disabled or represented in any operator-only diagnostic surface, and how is stale client Tool discovery handled after toggling the setting?
- [ ] Q10) What focused package/import-boundary tests ensure the remember adapter consumes shared records/service/errors without moving MCP or client-policy concerns into `mnemosyne/memory/`?
- [ ] Q11) What direct MCP checks are safe and sufficient to prove one approved write, duplicate idempotence, default-off behavior, recall compatibility, and cleanup without creating real user memory?

Decision log
- Decision (prior Track 006): Durable writes require per-call MCP-client approval after the exact proposed memory is visible; denial produces no server call, and a model-provided confirmation field is never consent.
- Decision (prior Track 006): Mutation Tools are disabled by default and clients that cannot enforce per-call approval must leave them disabled.
- Decision (prior Track 006): `MemoryService.remember()` owns mutation enablement, duplicate detection, server-generated operational fields, and canonical persistence; MCP handlers adapt but do not redefine those behaviors.
- Decision (prior Track 006): Exact active duplicates return `already_exists`; exact archived duplicates return `existing_archived`; neither creates another record.
- Decision (prior Track 006): Files are the only durable source of truth, writes are private and atomic, and mutation logs omit title, content, tags, deleted data, absolute paths, and complete arguments.
- Decision (Track 007 draft): OpenCode's current published schema permits arbitrary Tool-name permission keys with `ask`, and MCP Tools are prefixed by server name. The exact generated key and runtime behavior must still be verified before ACTIVE.
- Decision (Track 007 draft): OpenCode configuration changes are loaded only at startup, and `--auto` or interactive auto-approval automatically approves `ask`; enablement documentation and acceptance checks must make that limitation explicit.

Plan (execution steps)
- [ ] S1) Resolve Q1-Q11 and record the complete Tool schema, operator gate, consent/client configuration, refusal policy, result/error, logging, restart, and validation contracts.
- [ ] S2) Move Track 007 to ACTIVE (folder, filename, title, and current path status) and check this step before implementation begins.
- [ ] S3) Execute one TDD chunk for strict operator setting parsing plus default-off conditional Tool discovery and dispatch, preserving the existing default Tool list.
- [ ] S4) Execute one TDD chunk for the `memory_remember` definition, shared-derived schema branches, bounded MCP argument validation, package exports, and import boundaries without persistence.
- [ ] S5) Execute one TDD chunk adapting validated arguments to `MemoryDraft` and the enabled shared `MemoryService`, mapping success, duplicate, refusal, conflict, candidate, and storage outcomes with content-free logs.
- [ ] S6) Execute one TDD chunk for the validated OpenCode prefixed `ask` permission and configuration contract, including default-off, restart, denial/no-call, and auto-approval safety documentation.
- [ ] S7) Update `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md`; run focused and full automated validation plus whitespace checks; perform isolated temporary-root direct MCP checks and configured-client checks when available; remove all generated memory and record evidence.
- [ ] S8) Confirm all acceptance criteria and milestones, move Track 007 to COMPLETED with synchronized status, and record final outcomes and evidence.

Current inventory
- Commit `d86ac6c` completed Track 006 and is synchronized on `main`/`origin/main`; the working tree was clean before this DRAFT Track was created.
- `memory_recall` and `list_tools` are the only registered Tools. `mnemosyne/mcp/tools/registry.py` currently uses a static `TOOLS` list and `TOOL_HANDLERS` mapping.
- `mnemosyne/settings.py` resolves only `MNEMOSYNE_MEMORY_ROOT`; no mutation or remember enablement setting exists.
- `mnemosyne/memory/records.py` already owns strict `MemoryDraft.from_dict()` validation for scope, namespace, optional collection, kind, language, title, content, tags, and origin, plus canonical version-2 serialization.
- `mnemosyne/memory/service.py` defaults `mutations_enabled` to false. Its tested `remember()` operation requires enablement, serializes duplicate discovery, generates ID/timestamps/provenance/lifecycle, and returns `remembered`, `already_exists`, or `existing_archived`.
- `mnemosyne/memory/store.py` already owns bounded discovery, private directory/file permissions, canonical pre-publication validation, same-directory temporary writes, no-overwrite atomic publication, conflict detection, and cleanup.
- `mnemosyne/memory/errors.py` exposes structured validation plus mutation-disabled, candidate-limit, storage, unsafe-path, write-conflict, revision-conflict, not-found, and ambiguous-reference errors.
- `tests/memory/test_service.py` and `tests/memory/test_store_mutations.py` cover shared remember behavior only against temporary roots; no MCP remember tests or Tool package exist.
- `opencode.json` registers the remote `mnemosyne` server but has no Tool-specific permission rule. Current OpenCode documentation states that MCP Tool names are server-prefixed, arbitrary Tool names may be permission keys, `ask` prompts per request, configuration requires restart, and auto mode approves otherwise-ask requests.
- The consolidated baseline is 186 passing tests. Track 006 direct MCP validation proved v1/v2 recall compatibility and absence of mutation Tools but did not exercise a configured client.

Artifacts
- Shared-domain prerequisite: `.backlog/COMPLETED/2026/TRACK_006_COMPLETED_shared_memory_domain_architecture.md`.
- Current public behavior and boundaries: `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` at commit `d86ac6c`.
- OpenCode permission reference reviewed 2026-07-18: `https://opencode.ai/docs/permissions/`.
- OpenCode MCP Tool-prefix reference reviewed 2026-07-18: `https://opencode.ai/docs/mcp-servers/`.
- OpenCode configuration schema reviewed 2026-07-18: `https://opencode.ai/config.json`.

Completion notes
- Not started. This Track is DRAFT and no implementation is permitted.

# TRACK 011 [COMPLETED]: consent-gated memory archive and restore

Track
- ID: TRACK_011
- Repository: Mnemosyne
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_011_COMPLETED_consent_gated_memory_archive_restore.md

Problems (PORE)
- P1: As a user governing durable context, I cannot remove a stale canonical memory from normal recall without deleting its source file, because archive and restore exist only as unexposed shared-domain primitives.
- P2: As a user reviewing an exact memory before lifecycle mutation, I need archive and restore to operate on the inspected stable reference and expected revision, because acting on stale or ambiguous identity could change the wrong record state.
- P3: As a user requiring explicit control over durable mutation, I need every archive and restore call to remain disabled unless the operator enables it and the MCP client obtains approval for that exact call, because model intent is not consent.
- P4: As a Tool caller, I need bounded idempotent outcomes and stable conflicts across active, archived, missing, stale-revision, invalid, unsafe, unavailable, and unexpected cases, because lifecycle state can change between inspection and mutation.
- P5: As a user protecting memory contents, I need lifecycle results and logs to reveal only the minimum operational metadata, because archive/restore must not become a content, path, or argument disclosure channel.

Objective
- Expose narrow consent-gated `memory_archive` and `memory_restore` MCP Tools over the existing revisioned shared-domain lifecycle primitives so canonical memory can be reversibly excluded from or returned to recall without accepting paths, mutating legacy records, or weakening per-call approval.

Non-negotiables
- This Track remains planning-only while DRAFT; no implementation or implementation-driving tests begin until all blocking questions are resolved and the Track is moved to ACTIVE with its Move-to-ACTIVE step checked.
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- `mnemosyne/memory/` remains the owner of canonical reference validation, revision conflicts, lifecycle transitions, atomic replacement, timestamps, storage safety, and mutation-disabled policy; MCP Tools remain thin adapters.
- Archive and restore accept no filesystem path, memory root, filename, query, broad selector, record content, lifecycle target, model confirmation, or server-owned timestamp.
- Only canonical version-2 records are eligible. Legacy version-1 mutation, migration, and invented revision/lifecycle metadata remain prohibited.
- Every state-changing call requires both explicit operator enablement and MCP-client approval for the complete exact arguments. A model-provided consent field is never accepted.
- Clients that cannot enforce per-call approval must leave archive and restore disabled. OpenCode `always`, `--auto`, and interactive auto-approval remain unsupported while mutation is enabled.
- Results and logs must not contain title, content, tags, labels, complete arguments, paths, fingerprints, exception text, or tracebacks.
- Automated and direct checks use isolated temporary roots and remove all resulting fixtures and logs.
- No commit or push occurs unless explicitly requested.

Acceptance criteria
- [x] A1) [P1, P3] Default discovery and dispatch omit `memory_archive` and `memory_restore`; explicit operator enablement exposes each definition and handler together without changing read-only Tool availability or remember consent boundaries.
- [x] A2) [P1, P2] One approved archive call on the exact active canonical reference and current expected revision atomically changes lifecycle to archived, increments revision once, updates `updated_at`, preserves all other record identity/content, and removes the record from normal recall while retaining exact inspection.
- [x] A3) [P1, P2] One approved restore call on the exact archived canonical reference and current expected revision atomically changes lifecycle to active, increments revision once, updates `updated_at`, preserves all other record identity/content, and returns the record to normal recall.
- [x] A4) [P2, P4] Archive of an already archived record and restore of an already active record return explicit idempotent outcomes without another write or revision increment when the supplied expected revision is current.
- [x] A5) [P2, P4] Invalid arguments, legacy references, unknown fields, missing records, stale revisions, unsafe paths, unavailable storage, write conflicts, disabled mutation, and unexpected failures return stable bounded Tool errors without leaking submitted values, paths, memory content, or exception details.
- [x] A6) [P3] Project OpenCode policy denies the broad server prefix, explicitly allows read-only Tools, and asks for each archive, restore, and remember mutation after the broad rule; documentation requires `once` per exact call and treats `reject` as no server call/write.
- [x] A7) [P5] Archive and restore results contain only status, canonical structured reference, and lifecycle; terminal logs contain only an approved operation/outcome allowlist and never record content, labels, tags, complete arguments, paths, exception details, or tracebacks.
- [x] A8) [P1, P2, P4] Disabled, invalid, client-rejected, conflict, and idempotent calls create no root or files and do not alter source bytes/metadata; successful transitions modify only the selected canonical file atomically and retain no hidden prior content.
- [x] A9) [P1, P2, P3, P4, P5] Focused automated tests, import-boundary checks, the full suite, whitespace validation, isolated direct MCP checks, configured-client checks when available, and complete cleanup pass.
- [x] A10) [P1, P2, P3, P4, P5] `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` document exact requests, outcomes, lifecycle/revision behavior, enablement, consent, failures, logging, no-path/no-legacy boundaries, restart requirements, and relation to recall/inspect.

Why now / impact
- Track 010 added exact inspection and recall-to-inspect reference continuity. A real stale bug memory demonstrated the next user need: stop obsolete canonical context from influencing recall without immediately destroying it. Reversible lifecycle mutation establishes revision and consent behavior before a later physical-forget Track.

Scope
- In scope:
  - Separate public MCP Tools tentatively named `memory_archive` and `memory_restore`.
  - Strict canonical version-2 reference plus positive `expected_revision` request contracts derived from shared memory definitions.
  - Thin adaptation to `MemoryService.archive()` and `MemoryService.restore()` and the existing atomic store replacement.
  - Explicit archived/restored and already-archived/already-active outcomes with minimal reference/lifecycle projections.
  - A fail-closed operator enablement design and immutable startup registration for both lifecycle Tools.
  - Per-call OpenCode approval ordering and restart/unsafe-auto-approval documentation.
  - Stable validation, disabled, not-found, revision-conflict, write-conflict, unsafe/unavailable-storage, and internal-error mappings.
  - Content-free terminal logging with a reviewed metadata allowlist.
  - Focused domain-characterization, schema, handler, registry, settings, import-boundary, logging, route, client-policy, and isolated direct MCP coverage.
  - Public documentation and architecture/glossary updates.
- Out of scope:
  - Physical `memory_forget`, revise, relocate, reclassify, migrate, remember changes, or any other mutation Tool.
  - Legacy version-1 archive/restore or automatic migration to version 2.
  - Scope-wide bulk archive/restore, listing, pagination, arbitrary search, lifecycle query filters, background cleanup, or automatic stale-memory detection.
  - Caller-supplied paths, roots, filenames, content, tags, labels, timestamps, target lifecycle state, or client/model confirmation fields.
  - Hidden history, tombstones, event sourcing, retained prior record bodies, multi-process locking, or a database/index.
  - Automatically archiving duplicates, contradictions, old memories, or records after recall/inspection.
  - Physical deletion; a later Track should build `memory_forget` only after archive/restore behavior is validated.

Milestones
- [x] M1) Tool split, request/results, enablement, consent, revision/idempotency, errors, logs, registration, and direct-validation decisions are complete and the Track is eligible for ACTIVE.
- [x] M2) Focused TDD exposes consent-gated canonical archive/restore while preserving shared-domain ownership, atomic lifecycle semantics, and all read-only/remember contracts.
- [x] M3) Documentation, full validation, configured/direct checks, cleanup, and completion transition are recorded.

Risks / decisions
- Risk: Reusing remember-only enablement could surprise operators by enabling new mutations; introducing another setting increases configuration and registry complexity.
- Risk: Separate archive/restore Tools are explicit and least-privilege but require duplicated schemas, handlers, settings, permissions, and tests unless a narrow shared adapter is designed carefully.
- Risk: Expected revision prevents stale mutation but callers need inspection immediately before approval and must understand revision-conflict recovery.
- Risk: Idempotent domain outcomes still require a current expected revision; treating stale requests as idempotent could conceal a concurrent change.
- Risk: Archive removes records from recall, so users need exact references or another explicit lifecycle discovery seam to find archived records for restore.
- Risk: Mutation logs that include complete IDs or namespaces may disclose more durable identity than operationally necessary.
- Decision (prior Track 006): Canonical archive/restore are explicit revision-checked operations; archive changes active to archived, restore changes archived to active, and achieved states return idempotent outcomes without another revision.
- Decision (prior Track 006): Archive/restore accept only canonical `MemoryReference`; legacy mutation requires explicit migration and is outside the lifecycle Tool contract.
- Decision (prior Track 006): Successful state change atomically replaces the same file, increments revision, updates `updated_at`, and retains no hidden prior content.
- Decision (prior Tracks 007-010): Mutation remains default-off, operator-enabled, and separately subject to exact per-call MCP-client approval; public Tools accept structured references rather than paths; results/logs remain content-minimized.
- Decision (initial direction): Implement reversible archive/restore before physical forget so lifecycle, revision, stale-reference, consent, and recovery behavior are proven before irreversible deletion.

Open questions
- [x] Q1) Are `memory_archive` and `memory_restore` separate Tools, one discriminated lifecycle Tool, or another narrower public shape that best preserves explicit least privilege?
- [x] Q2) Is the request exactly `{reference: <canonical version-2 reference>, expected_revision: <positive integer>}`, and should `schema_version: 2` remain inside the reference for continuity with inspect?
- [x] Q3) What exact success statuses and minimal result shape represent `archived`, `already_archived`, `restored`, and `already_active`?
- [x] Q4) Does a stale expected revision always return `revision_conflict`, including when the current record has already reached the requested state?
- [x] Q5) What stable Tool status/code/message/field mapping applies to invalid reference/revision, legacy reference, disabled mutation, not found, revision conflict, write conflict, unsafe/unavailable storage, and unexpected failure?
- [x] Q6) What operator setting model enables archive/restore without silently widening the existing remember-only gate: one lifecycle-specific boolean, separate per-Tool booleans, or an explicit mutation Tool allowlist?
- [x] Q7) How does environment precedence, strict fixed-file configuration, startup-fixed registration, restart behavior, and fail-closed parsing evolve without weakening Track 009?
- [x] Q8) What exact OpenCode top-level/agent permission order makes both lifecycle Tools `ask` while keeping read-only Tools allowed and remember independently ask-gated?
- [x] Q9) Which logger names, levels, event/outcome names, and reference/lifecycle fields are necessary and safe for each terminal call?
- [x] Q10) Should archive and restore share private MCP schema/result/error/logging helpers, and if so where can they live without creating a broad lifecycle Tool or violating three-file package boundaries?
- [x] Q11) Which import-boundary and package-shape tests preserve shared-domain ownership and keep HTTP transport thin?
- [x] Q12) What isolated direct MCP and configured-client sequence proves default omission, enabled discovery/dispatch, `once` success, `reject` no-call, active-to-archived recall exclusion, archived inspection, restore-to-active recall return, stale conflict, idempotency, atomic/no-hidden-history behavior, content-free logs, and complete cleanup?

Decision log
- Decision (initial inspection): `MemoryService.archive()` and `restore()` already require mutation enablement and a canonical `MemoryReference`, compare `expected_revision` with the current record, and serialize one service instance through its lock and `FilesystemMemoryStore.replace()`; they do not yet enforce exact positive-integer revision type.
- Decision (initial inspection): The shared state transition increments revision and updates time only when lifecycle changes. Current-state requests return `already_archived` or `already_active` without replacing the file.
- Decision (initial inspection): `MemoryService._current()` maps non-canonical identity to validation failure and checks the persisted revision before lifecycle idempotency, so stale requests conflict rather than being treated as achieved-state success.
- Decision (initial inspection): The current public setting and registry gate only `memory_remember`; Track planning must not assume that remember enablement authorizes archive/restore.
- Decision (initial inspection): Track 010 provides exact versioned references and lifecycle/revision inspection for active and archived canonical records; recall provides references only for active/legacy matches because archived records remain ineligible.
- Decision (Q1): Expose separate `memory_archive` and `memory_restore` Tools. Do not expose an action discriminator or broad lifecycle Tool; client permissions remain independently explicit.
- Decision (Q2): Each request has exactly two required top-level fields: `reference` and `expected_revision`. `reference` is the strict canonical version-2 inspect reference, including `schema_version: 2`; legacy references and unknown fields are invalid. `expected_revision` must have exact integer type, excluding booleans, and be at least one.
- Decision (Q3): Normal Tool results contain only `status`, a canonical reference including `schema_version: 2`, and lifecycle state/revision. Archive returns `archived` or `already_archived`; restore returns `restored` or `already_active`. Idempotent results return unchanged current lifecycle.
- Decision (Q4): Revision is checked before target lifecycle state. Every stale expected revision returns `revision_conflict`, including when the persisted record has already reached the requested state.
- Decision (Q5): Invalid or legacy references return `invalid_request` / `invalid_reference`, with a bounded `reference` subfield and `reference is invalid`; invalid revision returns `invalid_request` / `invalid_expected_revision`, field `expected_revision`, and `expected revision is invalid`. Disabled mutation returns `policy_error` / `mutation_disabled`; missing memory returns `not_found` / `not_found`; stale revision and external atomic-replace races return `conflict` with `revision_conflict` and `write_conflict`; unsafe paths, unavailable sources, and `OSError` return `storage_error` / `memory_source_unavailable`; unexpected failures return `internal_error` / `internal_error`. Operation-specific messages are bounded and exception-free. Candidate limits, ambiguous legacy identity, and remember-content refusal are not lifecycle Tool outcomes.
- Decision (Q6): One archive/restore-specific operator gate enables the reversible pair together without widening remember or authorizing future mutation Tools. Its process override is `MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED`; its fixed-file key is `[memory].archive_restore_enabled`; both default false.
- Decision (Q7): Resolve remember and archive/restore into one immutable startup settings snapshot and read the fixed file at most once. Each supplied environment variable overrides only its corresponding file key; only exact lowercase `true` and `false` are accepted, and any invalid supplied value fails startup closed before file parsing. The strict optional `[memory]` table allows only optional boolean `remember_enabled` and `archive_restore_enabled`. Existing source safety, size, UTF-8/TOML, stable-error, no-write, restart, and startup-fixed registry guarantees remain unchanged.
- Decision (Q8): Top-level OpenCode policy has exact `ask` entries for remember, archive, and restore. Agent policy orders broad `mnemosyne_*` denial first, exact read-only allows next, and all three exact mutation `ask` rules last. Every call uses `once`; `reject` causes no server call or write; `always`, `--auto`, and interactive auto-approval remain prohibited while any mutation is enabled.
- Decision (Q9): Use loggers `mcp.memory_archive` and `mcp.memory_restore` and emit exactly one terminal event per server call. Ordinary changed/idempotent outcomes log at INFO, bounded expected failures at WARNING, and unexpected failures at ERROR without traceback. The allowlist is event, outcome, stable code/field when applicable, schema version, scope, and result lifecycle state/revision; IDs, namespace/collection identity, complete arguments, content metadata, paths, exception details, and tracebacks are forbidden.
- Decision (Q10): Symmetric private MCP mechanics may live in `mnemosyne/mcp/tools/_memory_lifecycle.py`: canonical schema construction, strict request parsing, minimal projections, bounded errors, and logging. It exposes no `TOOL`, operation discriminator, storage, or broad public capability. Each public Tool package remains exactly `__init__.py`, `definition.py`, and `handler.py`.
- Decision (Q11): Import-boundary tests require both Tool packages to keep the three-file shape and stable `TOOL`/`handle` exports, use shared normalization/scope/reference/error/service/store contracts, avoid routes/FastAPI and other public Tool internals, and keep the private lifecycle helper MCP-only with no persistence ownership. Existing shared-domain no-MCP/no-HTTP boundaries and thin unchanged routes remain enforced.
- Decision (Q12): Isolated validation first proves default omission and unknown dispatch without root creation, then enables the pair in a fresh process and verifies paired discovery. Starting from one active canonical fixture, configured/direct checks cover client reject as no call; approved archive once; recall exclusion and archived inspection; current-revision idempotency with unchanged bytes/mode/mtime; stale conflicts; approved restore once; recall return; restored idempotency; one selected atomic file change only; no history, temporary artifact, tombstone, unrelated-file change, or content-bearing log; and complete server/fixture/log cleanup. No ad-hoc protocol script is retained.
- Decision (inventory correction): Positive exact-integer revision validation is not currently enforced by `MemoryService.archive()` or `restore()`; booleans compare equal to integers. The MCP parser must enforce the public request immediately, and the lifecycle service invariant will receive focused characterization/validation in the service-adaptation chunk.
- Decision (inventory correction): Existing lifecycle tests do not yet prove stale target-state conflicts or idempotent byte/mode/mtime preservation; S5 must add that evidence. Service mutation locking is instance-local, so the Track claims no process-wide cross-call lock.

Plan (execution steps)
- [x] S1) Resolve Q1-Q12 and record exact Tool, request/result, enablement, consent, revision/idempotency, error/logging, registration, package-boundary, and isolated-validation contracts.
- [x] S2) Move Track 011 to ACTIVE (folder, filename, title, and current path status) and check this step before implementation begins.
- [x] S3) Execute one TDD chunk for strict archive/restore Tool definitions, canonical reference/expected-revision adaptation, package exports/import boundaries, and fail-closed paired registration seams without startup exposure.
- [x] S4) Execute one TDD chunk for bounded operator settings, immutable startup selection, both discovery surfaces, dispatch, restart behavior, and OpenCode per-call approval ordering.
- [x] S5) Execute one TDD chunk for shared-service archive adaptation, changed/idempotent projections, recall/inspect lifecycle behavior, revision/write conflicts, bounded failures, atomic/no-hidden-history guarantees, and content-free terminal logs.
- [x] S6) Update `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md`; run focused and full automated validation plus `git diff --check`; perform isolated direct MCP/configured-client checks and cleanup; record evidence.
- [x] S7) Confirm acceptance and milestones, move Track 011 to COMPLETED with synchronized status, and record final outcomes.

Current inventory
- Baseline commit `a3cea57` (`Add read-only memory inspection`) is synchronized on `main` and `origin/main` before this planning-only Track is added.
- `MemoryService.archive()` and `MemoryService.restore()` already implement mutation-disabled, canonical-only, revision-compared lifecycle transitions over `FilesystemMemoryStore.replace()`; exact positive-integer validation is not yet enforced, and mutation serialization is local to one service instance.
- Changed archive/restore transitions increment revision, preserve stable identity/content, update `updated_at`, atomically replace the same file, and retain no hidden prior record. Achieved-state calls return idempotent outcomes without write or revision increment.
- `MemoryService._current()` reads the canonical record and checks `expected_revision` before lifecycle state; missing records, stale revisions, unsafe paths, source failure, and external write conflicts use existing shared errors.
- `memory_recall` excludes archived version-2 records and now returns inspect-compatible references for active canonical and legacy matches. `memory_inspect` accepts exact active/archived canonical references and exposes lifecycle revision needed for a mutation request.
- `memory_remember` is the only current public mutation Tool. It is selected by one remember-specific startup setting and uses a separate client `ask` rule; neither contract currently authorizes lifecycle mutation.
- `mnemosyne/mcp/tools/registry.py` supports immutable startup-selected Tool/handler pairs and already proves that discovery and dispatch fail closed when one half is absent.
- `opencode.json` currently denies broad Mnemosyne access, allows list/recall/inspect, and asks for remember last. Archive/restore permissions do not exist.
- Shared service/store tests cover archive/restore state changes, current-state outcomes, revision increments, atomic replacement, and no hidden prior content. They do not yet prove stale lifecycle requests or byte/mode/mtime preservation for idempotent outcomes. No public schemas, handlers, settings, registry entries, route behavior, logs, client permissions, or direct MCP checks exist for lifecycle mutation.
- `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` identify archive/restore as future consent-gated mutation primitives and do not define public lifecycle Tools.
- S3 adds strict canonical-only schemas and a shared private lifecycle request parser under `mnemosyne/mcp/tools/_memory_lifecycle.py`; exact integer schema version and expected revision checks reject booleans, floats, legacy references, missing fields, unknown fields, paths, and content before mutation.
- `memory_archive/` and `memory_restore/` now each contain only `__init__.py`, `definition.py`, and `handler.py`, re-export stable `TOOL`/`handle` identities, and return bounded mutation-disabled results on valid direct calls. Enabled service execution intentionally remains unimplemented until S5.
- `build_tool_registry()` now has an injectable default-off archive/restore pair seam. Enabled incomplete registration fails closed; complete synthetic registration adds both Tools and handlers in archive/restore order. `build_startup_tool_registry()` intentionally does not connect or expose either Tool before S4 settings work.
- S4 adds immutable `MemoryToolSettings` resolution for independent remember and archive/restore gates. `MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED` and `[memory].archive_restore_enabled` are strict booleans defaulting false; each environment value overrides only its own file key, invalid supplied values fail before file access, and unresolved keys share at most one bounded settings-file read.
- Startup registry selection now connects archive and restore definition/handler pairs together only when archive/restore enablement is true. Both MCP `tools/list` and the `list_tools` Tool reflect the same startup-fixed tuple; disabled direct dispatch remains unknown, enabled invalid requests reach bounded validation, and valid requests remain mutation-disabled until S5 connects service execution.
- `opencode.json` now keeps the broad agent denial first, read-only allows next, and exact `ask` rules for remember, archive, and restore last; matching top-level mutation rules are also `ask`. Restart remains required for both server Tool selection and OpenCode policy/discovery refresh.
- S5 connects enabled startup handlers to `MemoryService.archive()` and `restore()` through the shared private MCP adapter while each public handler owns root resolution, store construction, and its operation-specific service call. The shared service now rejects non-positive and non-exact-integer lifecycle revisions before store access.
- Lifecycle results are validated against the requested identity, operation-specific status/state, and changed-versus-idempotent revision progression, then projected to only status, canonical versioned reference, and lifecycle. Archive/restore map validation, disabled, missing, revision, write, storage, and unexpected failures to the decided bounded Tool errors.
- Loggers `mcp.memory_archive` and `mcp.memory_restore` emit one terminal event with only outcome, stable code/field where applicable, schema version, scope, and successful lifecycle state/revision. Tests exclude IDs, namespaces, collections, content metadata, paths, exception details, and tracebacks.
- Focused integration proves archive changes one canonical file, leaves no temporary/history artifact or unrelated-file change, removes the record from recall while preserving archived inspection, and restore returns it to recall and active inspection. Service tests prove stale target-state conflicts and current-revision idempotency without byte, mode, mtime, revision, or clock changes.
- S6 updates all three required public documents with exact lifecycle requests, outcomes, gate independence, consent/restart rules, bounded failures/logging, and recall/inspect/storage relationships. No stale statement remains that remember is the sole mutation or archive/restore are future Tools.

Artifacts
- Shared lifecycle prerequisite: `.backlog/COMPLETED/2026/TRACK_006_COMPLETED_shared_memory_domain_architecture.md`.
- Consent and registry prerequisite: `.backlog/COMPLETED/2026/TRACK_007_COMPLETED_consent_gated_memory_remember.md`.
- Persistent settings prerequisite: `.backlog/COMPLETED/2026/TRACK_009_COMPLETED_local_settings_file.md`.
- Exact reference/inspection prerequisite: `.backlog/COMPLETED/2026/TRACK_010_COMPLETED_read_only_memory_inspection.md`.
- Baseline implementation: commit `a3cea57` (`Add read-only memory inspection`).

Completion notes
- DRAFT created on 2026-07-18 after TRACK_010 was committed and pushed. Existing shared archive/restore primitives were inspected, but no implementation or implementation-driving test was added.
- Activated on 2026-07-19 after Q1-Q12 were resolved, inventory gaps were recorded, M1 passed, and S1/S2 were checked. No implementation or implementation-driving test was added during activation.
- S3 TDD on 2026-07-19: focused tests initially failed during collection because `mnemosyne.mcp.tools._memory_lifecycle` and both Tool packages did not exist. Minimal implementation added strict definitions/parsing, three-file exports, disabled direct handlers, package boundaries, and fail-closed paired registry injection without startup exposure. Focused validation passed 45 tests; full automated validation passed 391 tests; `git diff --check` passed. No settings, startup exposure, persistence, lifecycle execution, logging, route, OpenCode, or documentation behavior changed in this chunk.
- S4 TDD on 2026-07-19: focused tests initially failed during collection because archive/restore settings and the combined startup resolver did not exist. Minimal implementation added the independent bounded gate, single-read settings snapshot, paired startup registration, discovery/dispatch and restart coverage, route compatibility, and exact OpenCode approval ordering. Focused validation passed 102 tests; full automated validation passed 416 tests; `git diff --check` passed. Valid lifecycle calls intentionally remain mutation-disabled and make no storage change pending S5.
- S5 TDD on 2026-07-19: focused tests first produced 26 expected failures for absent operation injection/execution and missing shared-service revision validation. Minimal implementation added enabled lifecycle service adaptation, strict result validation/projection, stable failure mappings, safe terminal logs, and exact revision validation before store reads. Refactoring kept storage/root ownership in public handlers and shared symmetric MCP behavior private. Focused validation passed 98 tests; full automated validation passed 444 tests; `git diff --check` passed. M2 is complete.
- S6 validation on 2026-07-19: focused lifecycle/settings/registry/route/client-policy validation passed 169 tests; the full suite passed 444 tests; `git diff --check` passed. Isolated direct HTTP MCP checks on temporary ports proved default omission/unknown dispatch and enabled paired discovery; active recall/inspection; archive to revision 2; recall exclusion with archived inspection; stale `revision_conflict`; `already_archived`; restore to revision 3; recall return; and `already_active`. Exactly one canonical file remained, no temporary/history artifact appeared, and lifecycle logs contained only the approved fields. `opencode mcp list` reported the configured Mnemosyne server connected after the user restarted OpenCode; no mutation was auto-approved during this check. The isolated server processes, roots, fixtures, homes, and logs were removed, and cleanup was verified. A1-A10 and S6 are complete; S7 remains the completion transition.
- Completed on 2026-07-19 after A1-A10, M1-M3, and S1-S7 passed. Mnemosyne now exposes separate default-off, operator-enabled, exact-approval `memory_archive` and `memory_restore` Tools over the shared canonical lifecycle domain. The final evidence is 444 passing automated tests, clean whitespace validation, successful isolated direct MCP lifecycle checks, connected configured-client visibility, and verified cleanup. No commit or push was performed.

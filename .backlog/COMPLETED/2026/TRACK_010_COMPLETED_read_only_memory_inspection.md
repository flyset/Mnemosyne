# TRACK 010 [COMPLETED]: read-only memory inspection

Track
- ID: TRACK_010
- Repository: Mnemosyne
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_010_COMPLETED_read_only_memory_inspection.md

Problems (PORE)
- P1: As a user governing durable context, I cannot inspect one exact memory with its canonical metadata and lifecycle, because `memory_recall` returns relevance-ranked minimized results rather than a complete exact-record view.
- P2: As a user preparing for future archive or physical-forget operations, I need to review the exact record and stable reference before approving mutation, because an ID or recall excerpt alone may not identify the intended canonical or legacy memory safely.
- P3: As a Tool caller, I need bounded behavior across canonical, archived, legacy, missing, ambiguous, invalid, and unavailable records, because the shared domain supports multiple record/reference forms but no public MCP inspection contract defines how they are selected or represented.
- P4: As a user protecting local memory, I need exact inspection to remain narrow and content-safe in results and logs, because a broad listing, caller-supplied path, or content-bearing log would expose more durable context than the request requires.

Objective
- Expose one narrow read-only `memory_inspect` MCP Tool over the shared memory domain that returns one explicitly selected user-visible record, including lifecycle where available, without accepting paths, mutating storage, dumping a scope, or weakening existing recall and consent boundaries.

Non-negotiables
- This Track remains planning-only while DRAFT; no implementation or implementation-driving tests begin until all blocking questions are resolved and the Track is moved to ACTIVE with its Move-to-ACTIVE step checked.
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- `mnemosyne/memory/` remains the owner of record/reference validation, exact lookup, legacy ambiguity, lifecycle meaning, and storage safety; the MCP Tool is a thin adapter.
- Inspection is read-only: it must not create, revise, archive, restore, delete, migrate, normalize, or rewrite any file or initialize the memory root.
- No MCP request may contain a filesystem path, memory root, arbitrary directory, glob, query language, or unrestricted list selector.
- Inspection returns only the selected memory and bounded public metadata; it never returns filesystem paths, fingerprints, internal storage objects, hidden history, unrelated records, or retrieval scores.
- Archived records remain user-governed durable memory and must not become invisible to exact inspection unless planning records a stronger reason.
- Logs must not contain memory title, content, tags, labels, complete arguments, absolute/relative paths, or underlying exception text.
- Automated and direct checks use isolated temporary roots and remove all resulting fixtures and logs.
- No commit or push occurs unless explicitly requested.

Acceptance criteria
- [x] A1) [P1, P4] Default Tool discovery exposes exactly one new read-only `memory_inspect` Tool with a narrow strict schema and no path, broad list, mutation, or server-owned storage input.
- [x] A2) [P1, P2] Inspecting one exact canonical active or archived record returns the agreed complete user-visible representation and stable structured reference without path, fingerprint, score, or unrelated memory.
- [x] A3) [P2, P3] Legacy version-1 inspection follows one explicit bounded selector/result contract, preserves the source file unchanged, and distinguishes not-found from ambiguous identity without inventing canonical metadata.
- [x] A4) [P3, P4] Invalid selectors, unknown fields, missing records, ambiguous legacy identity, unsafe paths, unavailable storage, and unexpected failures produce stable bounded Tool errors without leaking submitted values, paths, record content, or exception details.
- [x] A5) [P1, P4] Active and archived inspection, missing/invalid/error calls, discovery, and startup create, modify, or delete no settings, memory, application, or index path.
- [x] A6) [P4] Inspection logs contain only approved operation/outcome and bounded selector metadata and never record memory content, title, tags, labels, complete arguments, paths, fingerprints, or tracebacks.
- [x] A7) [P1, P2, P3, P4] Focused automated tests, import-boundary checks, the full suite, whitespace validation, and isolated direct MCP checks pass without retaining temporary memory or logs.
- [x] A8) [P1, P2, P3, P4] `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` document the exact selector, canonical and legacy results, archived behavior, bounded failures, read-only/no-path boundary, logging, and role before future mutation.

Why now / impact
- Track 009 completed persistent safe enablement for memory creation. Recall and remember now provide relevance retrieval and canonical creation, while the shared domain already contains exact read-only inspection. Exposing that capability before deletion gives users a review step and forces reference, legacy, result, and privacy contracts to be explicit before any irreversible MCP operation is designed.

Scope
- In scope:
  - One public read-only MCP Tool tentatively named `memory_inspect`.
  - A dedicated `mnemosyne/mcp/tools/memory_inspect/` definition, handler, and package export following existing Tool package boundaries.
  - Strict selector validation derived from shared `MemoryReference` and/or `LegacyMemoryReference` after planning resolves the public model.
  - Thin adaptation to `MemoryService.inspect()` and existing `FilesystemMemoryStore.get()` behavior.
  - Exact canonical active/archived results and an explicit non-invented legacy result.
  - Stable bounded validation, not-found, ambiguity, unsafe-source, unavailable-source, and internal-error mapping.
  - Content-free terminal logging with a reviewed allowlist of fields.
  - Default read-only Tool registration and matching `tools/list`, `list_tools`, and dispatch behavior if confirmed during planning.
  - Focused domain-adapter, schema, registry, import-boundary, logging, route, and isolated direct MCP coverage.
  - Public documentation and architecture/glossary updates.
- Out of scope:
  - `memory_forget`, archive, restore, revise, relocate, reclassify, migrate, or any other mutation Tool.
  - Scope-wide listing, browse-all, pagination, arbitrary search, query-language expansion, embeddings, or retrieval-ranking changes.
  - Caller-supplied paths, memory roots, filenames, fingerprints, timestamps, lifecycle state, or expected revision as inspection selectors unless planning proves a bounded need.
  - Automatic inspection before mutation, hidden background reads, automatic prompt injection, or client permission reconfiguration.
  - Inventing namespace, collection, kind, language, provenance, lifecycle, or timestamps for legacy version-1 records.
  - Changing memory storage format, deterministic paths, lifecycle policy, remember behavior, or filesystem initialization.
  - A broad redesign of recall results; a narrowly justified reference-continuity addition remains an open planning question.

Milestones
- [x] M1) Selector, reference continuity, canonical/legacy result, archived behavior, errors, logging, registration, and direct-validation decisions are complete and the Track is eligible for ACTIVE.
- [x] M2) Focused TDD exposes exact read-only inspection through MCP while preserving shared-domain ownership, no-write behavior, and existing Tool contracts.
- [x] M3) Documentation, full validation, isolated direct checks, and cleanup are recorded; only the separate completion transition remains.

Risks / decisions
- Risk: Requiring a full canonical reference is deterministic but existing recall results do not expose namespace/collection IDs, making pre-existing records difficult to select without reading files directly.
- Risk: Accepting only scope plus ID is convenient but may require bounded scope discovery, can hit the candidate limit, and can be ambiguous across canonical or legacy records.
- Risk: Returning complete memory content increases exposure compared with recall's minimized result, so exact selection and content-free logs are essential.
- Risk: Inventing canonical fields for legacy records would misrepresent provenance and lifecycle and create an unsafe basis for later deletion.
- Risk: Hiding archived records from exact inspection would prevent users from reviewing durable records excluded from normal recall.
- Risk: Adding reference fields to recall could be useful and additive but would change an existing public result contract beyond the smallest inspect adapter.
- Decision (prior Track 006): `MemoryService.inspect()` is read-only, accepts canonical or legacy references, and delegates exact lookup to the shared store without requiring mutation enablement.
- Decision (prior Track 006): Canonical version-2 identity is scope, namespace ID, optional collection ID, and memory ID; legacy identity is scope plus memory ID and can be ambiguous.
- Decision (prior Tracks 006-009): Files remain the only source of truth; public Tools accept no filesystem path; mutation remains independently gated and consent-based; logs omit memory content and paths.
- Decision (initial direction): Inspection precedes physical deletion so a later mutation flow can require review of one exact user-visible record and reference rather than acting on a relevance excerpt.

Open questions
- [x] Q1) Is the public selector a discriminated union of complete canonical `MemoryReference` and legacy `{scope, id}`, one common `{scope, id}` selector with bounded ambiguity, or another narrower model?
- [x] Q2) How does a caller obtain a complete canonical selector for pre-existing records when recall currently returns scope and ID but not namespace/collection IDs; should this Track add narrowly scoped reference continuity to recall results or rely on another explicit discovery seam?
- [x] Q3) What exact canonical result fields are returned: schema version, structured reference, namespace/collection labels and kinds, language, title, content, tags, provenance, lifecycle, and timestamps?
- [x] Q4) What exact legacy result represents only fields present in version 1, and how is its legacy schema/reference form made unmistakable without invented provenance or lifecycle?
- [x] Q5) Are active and archived canonical records inspected identically except for lifecycle, and does the request intentionally omit a lifecycle selector?
- [x] Q6) What stable Tool status/code/message/field mapping applies to invalid selector, not found, ambiguous reference, candidate overflow, unsafe source, unavailable source, and unexpected failure?
- [x] Q7) Which logger, levels, event/outcome names, and selector fields are permitted while guaranteeing that IDs or other metadata do not expose more than needed?
- [x] Q8) Is `memory_inspect` registered by default as a read-only Tool, and do any supported MCP clients require an additional privacy prompt despite the absence of mutation?
- [x] Q9) Should inspection serialize through a shared public projection helper, reuse canonical record serialization selectively, or remain an MCP-owned result adapter without duplicating record truth?
- [x] Q10) Which import-boundary and package-shape tests ensure the Tool consumes shared service/reference/errors without moving MCP semantics into the memory domain?
- [x] Q11) What isolated direct MCP sequence proves active and archived canonical inspection, agreed legacy behavior, bounded missing/ambiguous/error outcomes, both discovery surfaces, no-write behavior, content-free logs, and complete cleanup?

Decision log
- Decision (initial inspection): `MemoryReference.from_dict()` strictly requires scope, namespace ID, nullable collection ID, and ID; `LegacyMemoryReference.from_dict()` strictly requires scope and ID. Both reject unknown fields through shared validation.
- Decision (initial inspection): `FilesystemMemoryStore.get()` resolves canonical references through deterministic paths and resolves legacy references through bounded scope discovery, returning `MemoryNotFound` or `AmbiguousMemoryReference` as applicable.
- Decision (initial inspection): `MemoryService.inspect()` already returns either `MemoryRecordV2` or `LegacyMemoryRecordV1` and performs no mutation check, write, migration, or lifecycle filtering.
- Decision (initial inspection): Canonical record serialization contains all user-visible fields plus provenance/lifecycle/timestamps, while legacy serialization contains only schema version, ID, optional title, content, and optional tags. MCP planning must decide a minimized explicit projection rather than exposing filesystem/store metadata.
- Decision (Q1): `memory_inspect` accepts exactly one required `reference` object discriminated by literal `schema_version`. Version 2 requires `schema_version`, scope, namespace ID, nullable collection ID, and canonical memory ID; version 1 requires only `schema_version`, scope, and legacy memory ID. Unknown and server-owned fields are rejected, and the handler removes only the discriminator before constructing the existing strict shared reference type.
- Decision (Q2): S5 adds the same structured versioned reference to each `memory_recall` result as a narrow additive continuity change. This enables direct inspection of recalled active canonical and legacy records without adding broad listing; archived discovery remains outside this Track.
- Decision (Q3): A successful canonical result has `status: ok` and one `memory` containing a version-2 structured reference plus every user-visible canonical record field: schema version, ID, scope, namespace, collection, kind, language, nullable title, content, tags, provenance, lifecycle, and created/updated timestamps. It contains no path, fingerprint, storage wrapper, score, or unrelated record.
- Decision (Q4): A successful legacy result has `status: ok` and one `memory` containing a version-1 structured reference, schema version, ID, nullable title, content, and tags. The stable MCP projection uses null for an absent title and an empty array for absent tags and does not invent scope as record metadata, namespace, collection, kind, language, provenance, lifecycle, or timestamps.
- Decision (Q5): Active and archived canonical records use the same selector and result shape; persisted lifecycle state and revision distinguish them. Inspection applies no lifecycle selector or eligibility filter.
- Decision (Q6): Invalid argument or reference shape returns `status: invalid_request`, code `invalid_reference`, a bounded allowlisted field, and `reference is invalid`. Missing identity returns `status: not_found`, code `not_found`, and `memory was not found`. Ambiguous legacy identity returns `status: conflict`, code `ambiguous_reference`, and `legacy memory reference is ambiguous`. Candidate overflow returns `status: storage_error`, code `candidate_limit_exceeded`, and a bounded limit message. Unsafe, unavailable, or operating-system source failure returns `status: storage_error`, code `memory_source_unavailable`, and `memory could not be inspected`. Unexpected failure returns `status: internal_error`, code `internal_error`, and the same bounded message.
- Decision (Q7): Logger `mcp.memory_inspect` emits one terminal event per call: INFO for success/not-found, WARNING for invalid/conflict/storage outcomes, and ERROR without traceback for unexpected failure. Its allowlist is event, outcome, stable code/field where applicable, reference schema version, and validated scope; it never logs any memory, namespace, or collection ID, labels, title, content, tags, complete arguments, paths, fingerprints, exception text, or traceback. S4 also removes relative paths from shared store skip warnings so legacy inspection cannot indirectly create path-bearing logs.
- Decision (Q8): `memory_inspect` is registered by default beside the existing read-only Tools and needs no mutation enablement or additional privacy prompt. Project OpenCode policy explicitly allows `mnemosyne_memory_inspect` after the broad denial and before the existing remember `ask`; users must restart OpenCode after that configuration change.
- Decision (Q9): A private MCP-owned projection adapter uses shared record serialization and shared reference types as record truth, then adds the explicit versioned reference and stabilizes nullable/empty legacy fields. No MCP result semantics move into the shared memory domain.
- Decision (Q10): Import-boundary coverage requires the inspect package to contain only `__init__.py`, `definition.py`, and `handler.py`; re-export definition/handler identities; consume shared scopes, records, errors, service, store, and settings; and import no recall/remember internals, routes, FastAPI, or Tool-owned domain replacement. The shared memory package continues to import no MCP, HTTP, or FastAPI modules.
- Decision (Q11): Direct validation uses an isolated temporary HOME/root and alternate localhost server, calls `tools/list`, `list_tools`, and `memory_inspect` for active and archived canonical, unique legacy, missing, ambiguous, candidate-limit, and unsafe/unavailable cases, compares fixture trees/bytes/metadata before and after, checks logs against the allowlist, verifies missing-root calls initialize nothing, stops the server, verifies shutdown, and removes all temporary memory and logs. No ad-hoc script is retained.
- Decision (implementation chunking): The registry cannot safely advertise a Tool without a real callable handler. S3 therefore adds the strict definition/reference adapter and a fail-closed paired Tool/handler registry seam while leaving production startup discovery unchanged. S4 supplies the complete handler and atomically enables default discovery/dispatch plus the matching OpenCode read-only allow; no placeholder public behavior is exposed between chunks.

Plan (execution steps)
- [x] S1) Resolve Q1-Q11 and record the exact selector, reference-continuity decision, canonical/legacy results, archived behavior, error/logging contract, registration policy, package boundary, and isolated validation procedure.
- [x] S2) Move Track 010 to ACTIVE (folder, filename, title, and current path status) and check this step before implementation begins.
- [x] S3) Execute one TDD chunk for the strict `memory_inspect` definition, selected reference adapter, package exports/import boundaries, and a fail-closed paired discovery/dispatch registry seam without production startup exposure.
- [x] S4) Execute one TDD chunk for shared-service adaptation, canonical/legacy projections, archived behavior, bounded errors, no-write guarantees, content-free logs, atomic default discovery/dispatch registration, and the matching OpenCode read-only allow.
- [x] S5) Implement any explicitly approved narrow reference-continuity change identified by Q2 through a separate coherent TDD chunk; mark not applicable if planning resolves a usable selector without changing recall.
- [x] S6) Update `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md`; run focused and full automated validation plus `git diff --check`; perform isolated direct MCP checks and cleanup; record evidence.
- [x] S7) Confirm acceptance and milestones, move Track 010 to COMPLETED with synchronized status, and record final outcomes.

Current inventory
- `mnemosyne/memory/service.py:MemoryService.inspect()` is an existing read-only shared-domain primitive over `store.get()` and accepts both canonical and legacy reference types.
- `mnemosyne/memory/records.py` owns strict `MemoryReference`, `LegacyMemoryReference`, `MemoryRecordV2`, and `LegacyMemoryRecordV1` contracts plus versioned serialization. Canonical references contain scope, namespace ID, nullable collection ID, and ID; legacy references contain scope and ID.
- `mnemosyne/memory/store.py:FilesystemMemoryStore.get()` uses deterministic exact path projection for canonical records, while legacy lookup performs bounded scope discovery and reports missing or ambiguous identity. It rejects symlink components and invalid/mismatched records through existing bounded domain behavior.
- `mnemosyne/memory/errors.py` already defines validation, `MemoryNotFound`, `AmbiguousMemoryReference`, `CandidateLimitExceeded`, `UnsafeMemoryPath`, and `MemorySourceUnavailable` error types relevant to inspection.
- `memory_recall` continues to exclude archived records and return its existing minimized ID, scope, title, content, tags, and match evidence. Each successful result now also includes the same inspect-compatible versioned structured reference: scope/ID for legacy records and scope/namespace ID/nullable collection ID/ID for canonical records. It still returns no provenance, lifecycle, timestamps, path, fingerprint, or score.
- `memory_remember` returns a complete structured canonical reference and lifecycle for remembered and duplicate outcomes, providing one existing source of inspectable canonical identity.
- `mnemosyne/mcp/tools/memory_inspect/` contains only `__init__.py`, `definition.py`, and `handler.py`. Its strict Tool schema accepts one version-discriminated reference with no path or broad selector. The complete handler validates before root resolution, calls the shared read-only service/store, returns record-derived canonical or stable legacy projections, maps bounded failures, and emits one content-free terminal event.
- `mnemosyne/mcp/tools/registry.py` retains the fail-closed optional inspect Tool/handler pair and now supplies both real halves together at startup. Default order is list, recall, inspect, followed by remember only when independently enabled; the same immutable selection drives both discovery surfaces and dispatch.
- `mnemosyne/memory/store.py` now logs skipped candidate scope/reason only. Relative paths and candidate names are omitted for inspect, recall, and all shared discovery callers without changing eligibility or lookup behavior.
- `opencode.json` now explicitly allows `mnemosyne_memory_inspect` after the broad denial and existing read-only allows and before the final remember `ask`, preserving last-match consent ordering.
- Focused MCP, shared-domain, startup-subprocess, route, and OpenCode tests now cover exact active/archived canonical and stable legacy projections, strict validation, bounded domain/storage/internal failures, source and missing-root no-write behavior, content/path-free logs, package/import boundaries, both discovery surfaces, default dispatch, remember independence, and ordered client policy. S5 recall continuity and S6 documentation/full/direct validation remain.
- `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` now document the public inspect Tool, versioned canonical/legacy selectors and results, archived behavior, bounded failures/logs, read-only/no-path/no-initialization boundary, default registry role, OpenCode allow, and recall reference continuity.
- `main` is clean and synchronized with `origin/main` at commit `70f7857` before this planning-only Track is added.

Artifacts
- Shared-domain prerequisite: `.backlog/COMPLETED/2026/TRACK_006_COMPLETED_shared_memory_domain_architecture.md`.
- Recall prerequisite: `.backlog/COMPLETED/2026/TRACK_005_COMPLETED_filesystem_memory_retrieval.md`.
- Remember/reference prerequisite: `.backlog/COMPLETED/2026/TRACK_007_COMPLETED_consent_gated_memory_remember.md`.
- Current public memory and configuration contracts: `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` at commit `70f7857`.
- S3 red evidence (2026-07-18): `.venv/bin/python -m pytest -p no:cacheprovider tests/mcp/test_memory_inspect.py tests/memory/test_import_boundaries.py tests/mcp/test_registry.py` failed during collection with the expected `ModuleNotFoundError` because `mnemosyne.mcp.tools.memory_inspect` did not yet exist.
- S3 green evidence (2026-07-18): the same focused command passed all 26 tests after the minimal package and paired registry seam were added.
- S3 whitespace evidence (2026-07-18): `git diff --check` and explicit no-index checks for the untracked Track, Tool package, and focused test file produced no errors.
- S4 handler/privacy red evidence (2026-07-18): `.venv/bin/python -m pytest -p no:cacheprovider tests/mcp/test_memory_inspect.py tests/memory/test_import_boundaries.py tests/memory/test_store.py` produced the expected 32 failures and 20 passes against the S3-only adapter and path-bearing store warnings.
- S4 startup/client red evidence (2026-07-18): `.venv/bin/python -m pytest -p no:cacheprovider tests/mcp/test_registry.py tests/mcp/test_startup_settings.py tests/mcp/test_list_tools.py tests/routes/test_mcp.py tests/test_opencode_config.py` produced the expected 9 failures and 25 passes before startup registration and the OpenCode allow were changed.
- S4 handler/privacy green evidence (2026-07-18): the first focused command passed all 52 tests after the complete handler and path-minimized shared warnings were implemented.
- S4 startup/client green evidence (2026-07-18): the second focused command passed all 34 tests after atomic startup registration and the ordered OpenCode allow. The route discovery assertion was made process-configuration-aware because remember availability is independently startup-fixed; isolated subprocess tests prove both exact orders.
- S4 consolidated evidence (2026-07-18): the approved eight-file focused command passed all 86 tests in 2.35 seconds.
- S4 whitespace evidence (2026-07-18): `git diff --check` and explicit no-index checks for the untracked Track, Tool package, and focused test file produced no errors before the Track evidence update.
- S5 red evidence (2026-07-18): `.venv/bin/python -m pytest -p no:cacheprovider tests/mcp/test_memory_recall.py tests/routes/test_mcp.py` produced the expected 3 failures and 43 passes after legacy/canonical recall and route expectations required inspect-compatible references.
- S5 green evidence (2026-07-18): the same focused command passed all 46 tests after the minimal version-aware `_serialize_match()` projection was added.
- S5 whitespace evidence (2026-07-18): `git diff --check` and explicit no-index checks for the untracked Track and Tool/test files produced no errors before the Track evidence update.
- S6 focused automated evidence (2026-07-18): with exact `MNEMOSYNE_MEMORY_REMEMBER_ENABLED=false`, the approved inspection/recall/registry/startup/list/import/store/route/OpenCode command passed all 118 tests in 2.28 seconds.
- S6 full automated evidence (2026-07-18): with exact `MNEMOSYNE_MEMORY_REMEMBER_ENABLED=false`, the complete suite passed all 363 tests in 2.55 seconds.
- S6 direct MCP evidence (2026-07-18): an isolated Uvicorn server on port 8769 used a temporary HOME/root and exact disabled remember setting. `tools/list` and `list_tools` exposed exactly list, recall, and inspect. Recall returned an inspect-compatible canonical reference. Exact inspection returned the active canonical revision 1, archived canonical revision 2, and one stable legacy result. Ambiguous legacy, 1,001-candidate legacy scope, symlinked canonical namespace, and non-directory legacy scope returned respectively `ambiguous_reference`, `candidate_limit_exceeded`, and bounded `memory_source_unavailable` outcomes without paths or source details.
- S6 no-write/log evidence (2026-07-18): pre/post hashes, modes, mtimes, and relative file inventory matched for all 1,007 isolated fixture files; no temporary HOME application/settings path was created. The server log contained exactly seven bounded inspect terminal events and one shared `skipped scope='project' reason='symlink'` warning; searches found no synthetic content, IDs, candidate filenames, memory-root path, or traceback.
- S6 cleanup evidence (2026-07-18): Uvicorn stopped, port 8769 had no listener, the complete temporary HOME/root/results/snapshot/log directory was physically removed, and absence was verified. No ad-hoc script or user memory was retained.
- S6 whitespace evidence (2026-07-18): `git diff --check` and explicit no-index checks for all untracked Track/Tool/test files passed after documentation, automated validation, direct checks, and cleanup.

Completion notes
- DRAFT created on 2026-07-18 after read-only inspection confirmed that exact canonical/legacy inspection already exists in the shared domain but has no MCP adapter. No implementation or implementation-driving test was added.
- Planning completed and Track moved to ACTIVE on 2026-07-18 after Q1-Q11 fixed the versioned selector, reference continuity, projections, lifecycle behavior, bounded errors/logging, default registration, package boundary, and isolated validation contract. No implementation or implementation-driving test was added during activation.
- S3 completed on 2026-07-18 through one focused red/green TDD chunk. The strict definition, shared-reference adapter, three-file package boundary, and fail-closed paired registry seam are implemented and covered; production discovery remains unchanged until S4 can register the complete handler atomically.
- S4 completed on 2026-07-18 through focused red/green phases within one declared chunk. Exact active, archived, and legacy inspection is now publicly discoverable and dispatchable by default; failures, no-write behavior, logs, shared warnings, startup selection, route transport, and OpenCode read-only permission are bounded and covered. Remember remains independently gated and no S5 recall or S6 documentation/direct-validation work was included.
- S5 completed on 2026-07-18 through one focused red/green TDD chunk. Successful recall results now carry inspect-compatible record-derived references for active canonical and legacy memories without changing ranking, archived eligibility, request schema, errors, or minimized content/match fields.
- S6 completed on 2026-07-18: all public documentation was synchronized; 118 focused and 363 full automated tests passed; whitespace validation passed; isolated direct MCP checks proved both discovery surfaces, recall continuity, active/archived/legacy inspection, bounded ambiguous/candidate/unsafe/unavailable outcomes, no-write behavior, content/path-free logs, and complete cleanup. A1-A8, M1-M3, and S1-S6 are checked; only S7 completion review and status transition remain.
- S7 completed on 2026-07-18: all acceptance criteria, milestones, questions, and execution steps are checked; Track 010 moved to COMPLETED with synchronized folder, filename, title, and current path. Mnemosyne now exposes one default read-only `memory_inspect` Tool with strict versioned canonical/legacy references, complete bounded exact results including archived canonical memory, stable failures and content-free logs, no path or write capability, and recall-to-inspect reference continuity. Documentation, 363 automated tests, isolated direct MCP checks, no-write snapshots, log review, and complete cleanup all passed.

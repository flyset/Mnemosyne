# TRACK 021 [DRAFT]: Event kind and kind guidance

Track
- ID: TRACK_021
- Repository: Mnemosyne
- Branch: main
- Current path: `.backlog/DRAFT/2026/TRACK_021_DRAFT_event_kind.md`

Problems (PORE)
- P1: As an agent storing project memory, I cannot classify a completed occurrence separately from a current project condition, because the project scope has `state` but no `event` kind.
- P2: As a model choosing a memory kind, I receive scope descriptions and allowed kind enums but no per-(scope, kind) writing guidance, so shared kinds such as `summary` and `reference` do not explain their scope-specific meaning.
- P3: As an agent storing an event whose occurrence instant is known, I cannot preserve that instant separately from server-controlled creation and update times, because version 2 has no event-time field.
- P4: As a user reviewing project history, I cannot discover events by occurrence range or chronology, because recall ranks textual relevance, listing orders inventory by record identity, and inspection requires an already-known exact reference.

Objective
- Add a project-only `event` classification with an immutable structural occurrence timestamp, publish canonical per-(scope, kind) writing guidance through the portable `memory_remember` Tool schema, and provide a bounded read-only timeline for chronological event discovery and exact-inspection handoff.

Non-negotiables
- No implementation begins while this Track is DRAFT.
- All implementation follows TDD: write a focused failing test, make the smallest change that passes, refactor, validate, and update this Track after each ACTIVE chunk.
- Preserve the six fixed memory scopes, local-first filesystem source of truth, single-user assumptions, least privilege, default-off mutation, and exact per-call MCP-client approval.
- Add `event` only to the `project` scope; do not broaden it to other scopes without a concrete requirement.
- Keep kind policy and occurrence-time semantics in the shared memory domain; keep model-facing Tool-schema rendering under `mnemosyne/mcp/` and HTTP transport unchanged.
- Preserve existing canonical non-event version-2 records without background rewriting or invented occurrence timestamps.
- Keep timeline retrieval read-only, event-specific, path-free, bounded, deterministic, and distinct from relevance recall and complete identity-ordered inventory listing.
- Do not infer or persist causation, automatically group episodes, or turn chronological adjacency into a causal claim.
- Preserve all unrelated working-tree changes, including the existing user change to `AGENTS.md`.

Acceptance criteria
- [ ] A1) [P1, P2] The shared domain defines `KindDefinition(kind, guidance)` values keyed by the `(scope, kind)` pair, and derives `ALLOWED_KINDS` from that canonical table.
- [ ] A2) [P1] `MemoryKind.EVENT = "event"` follows `STATE` in the enum and is valid only for `MemoryScope.PROJECT`; existing scope-kind combinations remain valid and unchanged.
- [ ] A3) [P2] Every allowed scope-kind pair has bounded writing guidance, including scope-specific guidance for shared `summary` and `reference` kinds.
- [ ] A4) [P2] `memory_remember` renders scope-specific kind guidance into each complete scope branch and grouped guidance into the top-level `kind` schema retained by flat clients.
- [ ] A5) [P3] `occurred_at` uses strict UTC-second form `YYYY-MM-DDTHH:MM:SSZ`, is required for `event`, and is absent and rejected for every non-event kind in both drafts and persisted records.
- [ ] A6) [P3] Existing valid non-event version-2 records without `occurred_at` continue to parse and serialize without migration or an invented value.
- [ ] A7) [P1, P3] Event duplicate identity includes `occurred_at`, so otherwise identical events at different occurrence times remain distinct while exact event duplicates retain existing duplicate behavior; non-event draft and record keys use the same internal null position without changing duplicate equality, and non-event serialization still omits the field.
- [ ] A8) [P3] `occurred_at` is immutable after creation: revision exposes no replacement field, archive/restore preserve it, and the store's replacement invariant rejects any attempted change.
- [ ] A9) [P1, P3] An enabled `memory_remember` event call persists and exact inspection returns the structural occurrence timestamp; non-event remember behavior and existing result shapes remain unchanged.
- [ ] A10) [P4] The shared domain provides bounded deterministic selection of canonical project events by occurrence-time criteria without changing relevance recall or identity-ordered memory listing.
- [ ] A11) [P4] A separate read-only `memory_timeline` Tool exposes an explicit least-privilege temporal selector, accepts no free-form query, client path, arbitrary kind, or arbitrary sort key, and delegates memory semantics to the shared domain.
- [ ] A12) [P4] Timeline ordering uses `occurred_at` with a deterministic public-identity tie-breaker, and its bounded pagination cannot silently skip or duplicate selected events within one valid continuation snapshot.
- [ ] A13) [P3, P4] Timeline results expose enough compact occurrence metadata and inspect-compatible references for chronological discovery followed by exact inspection, without becoming a second full-content recall Tool.
- [ ] A14) [P4] Tool discovery, registry dispatch, argument compatibility, bounded errors, and content-free logging cover the new read-only capability without changing HTTP transport or mutation enablement.
- [ ] A15) [P1, P2, P3, P4] README, architecture, and glossary documentation describe event semantics, kind guidance, occurrence time, timeline behavior, compatibility, and the boundaries around relevance, inventory, chronology, causation, and episode construction.
- [ ] A16) [P1, P2, P3, P4] Focused domain/MCP tests, direct MCP checks where available, the full automated suite, and whitespace validation pass.

Why now / impact
- Project memory lacks an explicit semantic distinction between a current condition and a completed occurrence.
- `state` and `event` guide how records are written; existing remember, revision, and lifecycle behavior remains unchanged, so this Track neither automatically supersedes prior states nor makes complete event records append-only.
- Structural occurrence time makes event chronology representable without conflating event time with server write time, while preserving future room for explicit chronological query behavior.
- A dedicated timeline completes the practical record, discover chronologically, and inspect workflow without overloading existing Tools whose selectors and ordering have different meanings.

Scope
- In scope:
  - Project-only `event` memory kind.
  - Canonical per-(scope, kind) guidance and derived allowed-kind policy.
  - Strict structural `occurred_at` for event drafts and canonical event records.
  - Event duplicate identity and replacement immutability.
  - Portable `memory_remember` schema guidance and event timestamp input.
  - Remember persistence, exact inspection projection, tests, and public documentation.
  - Shared bounded temporal selection and deterministic chronological ordering for project events.
  - A separate read-only `memory_timeline` MCP Tool, registry integration, pagination, compact results, bounded errors, content-free logging, tests, and public documentation.
- Out of scope:
  - A seventh memory scope or event support outside `project`.
  - Chronological `memory_list` ordering, occurrence-time filtering in existing Tools, persistent indexes, or recall-ranking changes.
  - Migration or rewriting of existing version-2 files.
  - Mutable event occurrence time, event relocation, or kind reclassification.
  - Automatic state supersession and fully append-only event records.
  - Causal-link records, automatic causal inference, causal graph traversal, and automatic incident/session/episode construction or summarization.
  - HTTP routes, settings gates, mutation consent, storage backend replacement, or broad filesystem access.

Milestones
- [ ] M1) Establish the canonical kind-definition registry and project-only event kind.
- [ ] M2) Establish structural, compatible, immutable event occurrence time.
- [ ] M3) Publish guidance and occurrence time through `memory_remember` and verify exact inspection.
- [ ] M4) Establish bounded shared chronological event selection and pagination.
- [ ] M5) Publish and directly verify the read-only `memory_timeline` Tool.
- [ ] M6) Reconcile public documentation and complete validation.

Risks / decisions
- Risk: Adding an unconditional version-2 field would invalidate every existing canonical record; treat `occurred_at` as envelope-optional but semantically required exactly when `kind == event`.
- Risk: Flat MCP clients may discard conditional schema composition; publish `occurred_at` and explanatory guidance at top level while retaining strict complete-schema constraints and authoritative domain validation.
- Risk: Guidance duplicated between top-level and scope branches could drift; render both from the shared canonical kind-definition table.
- Risk: A new immutable field could be changed through a lower-level replacement call; include it in the store's immutable replacement comparison and cover it directly.
- Risk: Adding structural time and a timeline may imply broader temporal intelligence than this Track provides; document the bounded range/order capability and its lack of causal inference or automatic episode construction.
- Risk: A timeline could duplicate or weaken recall/list semantics; keep it event-only and temporal, with its own explicit selector and deterministic order.
- Risk: Occurrence-window pagination can drift as files change; bind continuation to the exact selector and selected valid-record snapshot rather than returning partial or unstable history.
- Risk: Chronological proximity may be mistaken for causation; results expose temporal order only and must not infer causal relations.
- Decision: Temporal/episodic meaning is a memory kind under `project`, not a new scope.
- Decision: `KindDefinition` is keyed by `(scope, kind)` and contains one `guidance` string using a shared-core plus scope-specific-delta writing convention without prematurely modeling core/delta as separate fields.
- Decision: Kind definitions live in `records.py` or a dependency-neutral `kinds.py`, never in `scopes.py`, because the current import direction is `records.py -> scopes.py`.
- Decision: The MCP renderer is `mnemosyne/mcp/tools/memory_remember/definition.py`; the shared memory domain must not import MCP schema concerns.
- Decision: Event occurrence time is a structural `occurred_at` value, not an unvalidated content convention.
- Decision: Persisted occurrence timestamps use the existing strict UTC-second representation `YYYY-MM-DDTHH:MM:SSZ`.
- Decision: `occurred_at` is required only for events, rejected for non-events, included in duplicate identity, and immutable after creation.
- Decision: Track 021 expands from storage preparation to an end-to-end event workflow with a separate read-only `memory_timeline` Tool.
- Decision: Timeline is a temporal read model, not an extension of relevance-based `memory_recall` or identity-ordered `memory_list`.
- Decision: Causal assertions should be designed later as independently approved link records rather than inferred from ordering or embedded into event mutation; they are not part of this Track.

Open questions
- [x] Q1) Which layer renders per-kind guidance into what the model reads at write time?
- [x] Q2) Does event occurrence time live in content or in a structural field?
- [ ] Q3) Should timeline requests publish an explicit constant `project` scope or make project scope implicit in the Tool?
- [ ] Q4) Must timeline selection require one project namespace, and should optional collection selection reuse `memory_list`'s omission-sensitive semantics?
- [ ] Q5) Are timeline results limited to active events like semantic recall, or do they include archived events with lifecycle state like governance inventory?
- [ ] Q6) What exact compact result fields should timeline return before the caller uses `memory_inspect`?
- [ ] Q7) What are the exact inclusive/exclusive range boundaries, default direction, page-size bounds, cursor snapshot semantics, and no-result shape?

Decision log
- Decision (Q1, 2026-07-20): The `memory_remember` definition renders canonical shared guidance into its top-level portable kind schema and strict scope branches.
- Decision (Q2, 2026-07-20): Use structural `occurred_at`; this is more complete than a content-only convention and preserves event time independently from persistence timestamps.
- Decision (scope expansion, 2026-07-20): Event storage alone does not provide temporal retrieval. Add a distinct `memory_timeline` capability to Track 021 while deferring causal-link records and automatic episode construction.

Plan (execution steps)
- [ ] S0) While DRAFT, resolve Q3-Q7, make the timeline contract and acceptance criteria exact, and synchronize the Track title/path slug with its expanded event-and-timeline outcome.
- [ ] S1) Move Track 021 to ACTIVE (folder, filename, title, and current path status) and check this step before implementation begins.
- [ ] S2) TDD the canonical kind registry: add focused failing domain tests, introduce project-only `EVENT` and complete per-(scope, kind) definitions, derive `ALLOWED_KINDS`, refactor, validate the focused slice, and update this Track.
- [ ] S3) TDD structural occurrence time: add focused failing record/draft/service/store tests proving both duplicate-key call sites use occurrence time, equal-time events duplicate, different-time events remain distinct, existing non-event duplicate equality is unchanged through an internal null key position, and non-event serialization omits the field; minimally implement compatible event-only `occurred_at`, persistence, and immutable replacement enforcement; refactor, validate the focused slice, resolve the matching verification memory, and update this Track.
- [ ] S4) TDD the public MCP contract: add focused failing portable/complete-schema and remember/inspect tests, render kind guidance and event occurrence input through `memory_remember`, preserve bounded validation/results/logging, refactor, validate the focused slice, and update this Track.
- [ ] S5) TDD the shared timeline domain: add focused failing selector, eligibility, occurrence-range, deterministic-order, page, cursor/snapshot, and compatibility tests; minimally implement bounded project-event timeline selection; refactor, validate the focused slice, and update this Track.
- [ ] S6) TDD the public timeline capability: add focused failing Tool-schema, argument-normalization, handler, registry/discovery/dispatch, result/error, logging, and direct-protocol coverage; minimally publish `memory_timeline` as a read-only adapter over the shared domain; refactor, validate the focused slice, and update this Track.
- [ ] S7) Update README, architecture, and glossary; run focused tests, direct MCP checks, the full suite, and `git diff --check`; record evidence and update this Track.
- [ ] S8) Confirm acceptance and, only when every criterion passes, move Track 021 to COMPLETED with synchronized folder, filename, title, current path, inventory, and completion evidence.

Current inventory
- `mnemosyne/memory/scopes.py` defines six `ScopeDefinition` values with scope-level descriptions and namespace kinds; it does not import memory kinds.
- `mnemosyne/memory/records.py` imports scopes, defines the bare `MemoryKind` enum and hand-maintained `ALLOWED_KINDS`, requires an exact version-2 field set, parses only persistence timestamps, and defines duplicate identity without event time.
- `MemoryRevision` contains no kind or occurrence-time field, so the public revision surface already excludes both forms of reclassification.
- `mnemosyne/memory/service.py` constructs canonical records from drafts, compares duplicate keys, and uses dataclass replacement for revision and lifecycle changes.
- `mnemosyne/memory/store.py` enforces immutable identity/metadata during atomic replacement but does not yet know about occurrence time.
- `mnemosyne/mcp/tools/memory_remember/definition.py` derives top-level and six scope-branch enums from `SCOPE_DEFINITIONS` and `ALLOWED_KINDS`; it currently renders scope descriptions but no kind guidance or occurrence-time property.
- `mnemosyne/mcp/tools/memory_remember/handler.py` delegates authoritative draft validation to the shared domain and currently recognizes exactly the existing nine caller-owned fields.
- Exact inspection serializes the complete user-visible canonical record, so a canonical structural field will flow through the existing record projection once serialization is extended and tested.
- `mnemosyne/memory/retrieval.py` ranks active memories by query relevance and is not a temporal selector; `mnemosyne/memory/listing.py` owns complete identity-ordered inventory pages and authenticated snapshot cursors that may inform, but must not dictate, timeline semantics.
- The immutable MCP registry has no timeline Tool. A new read-only definition/handler package must remain under `mnemosyne/mcp/tools/`, register without a mutation gate, and preserve schema-aware argument normalization and thin HTTP transport.
- `tests/memory/test_records.py`, service/store mutation tests, and `tests/mcp/test_memory_remember.py` hold the primary affected automated contracts; revise, archive, restore, list, retrieval, paths, and inspection tests provide compatibility coverage.
- `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` currently describe the six scopes, existing kind matrix, exact version-2 shape, portable remember schema, inspection projection, and immutable revision fields without event semantics.
- The working tree already contains a user-authored `AGENTS.md` modification adding the Project Memory instruction; this Track must not overwrite or revert it.

Artifacts
- Six project-memory design records were listed from namespace `mnemosyne`, collection `event-kind`, and inspected beginning with the summary anchor on 2026-07-20.
- User resolved Q1 affirmatively and selected structural option B for Q2 on 2026-07-20.
- User approved creation of this DRAFT Track on 2026-07-20; no implementation approval or ACTIVE transition is implied.
- A seventh open verification memory was inspected on 2026-07-20. It remains open until S3 proves event and non-event duplicate-key behavior; the user approved adding that requirement to this DRAFT Track.
- The user selected the end-to-end option on 2026-07-20: expand Track 021 with a separate read-only timeline rather than leave chronological retrieval to a dependent Track. The user also agreed that causal-link records belong in a deliberate follow-up and that ordering must not imply causation.

Completion notes
- DRAFT created and amended with explicit duplicate-key regression requirements plus the event-and-timeline scope expansion on 2026-07-20. No tests or implementation were changed or executed. The next planning step is S0; implementation remains prohibited until the Track later moves to ACTIVE through S1.

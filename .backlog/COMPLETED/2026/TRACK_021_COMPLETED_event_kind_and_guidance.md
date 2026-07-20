# TRACK 021 [COMPLETED]: Event kind and kind guidance

Track
- ID: TRACK_021
- Repository: Mnemosyne
- Branch: main
- Current path: `.backlog/COMPLETED/2026/TRACK_021_COMPLETED_event_kind_and_guidance.md`

Problems (PORE)
- P1: As an agent storing project memory, I cannot classify a completed occurrence separately from a current project condition, because the project scope has `state` but no `event` kind.
- P2: As a model choosing a memory kind, I receive allowed enums but no per-(scope, kind) writing guidance, so the intended meaning of each choice is not discoverable from the Tool schema.
- P3: As an agent storing a project event whose occurrence instant is known, I cannot preserve that instant separately from server-controlled creation and update times, because canonical version 2 has no event-time field.

Objective
- Add a project-only `event` kind with immutable structural `occurred_at` and publish canonical per-(scope, kind) guidance through the existing portable `memory_remember` contract, without adding scopes, temporal resources, or new Tool families.

Completion status
- All acceptance criteria and milestones passed on 2026-07-20; Track 021 is complete.
- The connected MCP server was restarted and directly verified at compatibility build `0.1.2` before completion.
- The first-class Timeline/Occurrence/TimelineMembership model remains deferred and was not implemented; no commit or push was performed.

Non-negotiables
- Preserve the six fixed semantic memory scopes, all existing version-1/version-2 records, and current local-first filesystem paths without migration or invented occurrence values.
- Add `event` only to `project`; do not broaden it until a concrete demonstrated use case exists.
- Keep canonical kind and occurrence semantics in `mnemosyne/memory/`; keep model-facing schema rendering under `mnemosyne/mcp/`; keep HTTP transport unchanged.
- Keep existing mutation gates, exact per-call client approval, bounded content policy, lifecycle semantics, structured references, logging restrictions, and no-secret contract.
- `state` versus `event` is writing guidance, not automatic state supersession or fully append-only event behavior.
- Every behavior change follows TDD and receives automated coverage; direct MCP checks supplement but never replace tests.
- Preserve the committed Project Memory instruction in `AGENTS.md` and unrelated working-tree changes.

Acceptance criteria
- [x] A1) [P1, P2] The shared memory domain defines `KindDefinition(kind, guidance)` for every allowed `(scope, kind)` pair and derives `ALLOWED_KINDS` from that canonical table.
- [x] A2) [P1] `MemoryKind.EVENT = "event"` follows `STATE`, is valid only for `MemoryScope.PROJECT`, and leaves every existing scope-kind combination unchanged.
- [x] A3) [P2] Every allowed pair has bounded writing guidance, including scope-specific guidance for shared `summary` and `reference` kinds.
- [x] A4) [P2] `memory_remember` renders scope-specific guidance into complete branches and grouped guidance into the top-level flat-client `kind` schema.
- [x] A5) [P3] Strict UTC-second `occurred_at` is required exactly for `event`, rejected for every non-event kind, and omitted from serialized non-event records.
- [x] A6) [P3] Existing non-event V2 records without `occurred_at` remain valid and serialize without migration or invented values.
- [x] A7) [P1, P3] Event duplicate identity includes occurrence time; equal events at equal times duplicate, otherwise-equal events at different times remain distinct, and existing non-event duplicate equality remains unchanged through an internal null key position.
- [x] A8) [P3] Occurrence time is immutable: revision exposes no replacement field, archive/restore preserve it, and store replacement rejects a changed value.
- [x] A9) [P1, P3] Enabled `memory_remember` persists project events and exact inspection returns `occurred_at`; existing non-event calls, results, errors, logs, and persistence remain compatible.
- [x] A10) [P3] Revision and lifecycle operations preserve event kind and occurrence time while retaining their current complete-state/no-op/revision-conflict behavior.
- [x] A11) [P1, P2, P3] README, architecture, glossary, focused tests, full suite, direct MCP checks, and whitespace validation document and prove the complete contract and deferred non-goals.

Why now / impact
- Project memory needs a usable distinction between current conditions and completed occurrences, and models already use `memory_remember` without requiring a separate temporal workflow.
- Structural occurrence time prevents persistence timestamps from being misread as event time while keeping event creation within one existing approved Tool call.
- The larger first-class model had cleaner orthogonality but imposed three-resource/multi-call authoring before a real many-to-many requirement was demonstrated.

Scope
- In scope:
  - Project-only `MemoryKind.EVENT`.
  - Canonical per-(scope, kind) guidance and derived allowed-kind policy.
  - Compatible event-only `occurred_at` in drafts, records, duplicate identity, persistence, revision/lifecycle preservation, remember schema/handler, and inspection.
  - Focused/compatibility/full tests, applicable public documentation, and direct MCP verification.
- Out of scope:
  - New memory scopes or event support outside `project`.
  - First-class Timeline, Occurrence, or TimelineMembership resources and their Tools.
  - Timeline IDs, many-to-many occurrence reuse, chronological range retrieval, persistent indexes, or cross-scope chronology.
  - Causality IDs/links/inference, automatic episode construction, state supersession, or fully append-only records.
  - HTTP routes, new mutation settings, storage backend replacement, or broad filesystem access.

Milestones
- [x] M1) Canonical kind-definition registry with unchanged existing public kinds.
- [x] M2) Project event and structural occurrence time delivered as one valid memory vertical.
- [x] M3) Kind guidance rendered through the portable remember schema.
- [x] M4) Documentation, direct protocol verification, and complete validation.

Risks / decisions
- Risk: Adding `EVENT` before the remember occurrence field would expose an unusable public schema; introduce the complete event vertical in one TDD chunk.
- Risk: Making `occurred_at` unconditional would invalidate existing V2 files; keep it envelope-optional but semantically required exactly for event.
- Risk: Flat clients may discard composition; publish occurrence input and guidance at top level while retaining strict complete-schema branches and authoritative domain validation.
- Risk: A new immutable field could change through lower-level replacement; include it in the store immutable comparison and test it directly.
- Risk: Event-kind cannot represent one occurrence in several histories without duplication; accept that limitation until an observed case justifies the deferred model.
- Decision: Event is a semantic kind under `project`, not a new scope or resource family.
- Decision: Occurrence time is strict structural UTC-second data, distinct from persistence timestamps and immutable after creation.
- Decision: Kind guidance is keyed by `(scope, kind)` and rendered by `memory_remember`; `scopes.py` remains free of `MemoryKind` imports.
- Decision: Existing memory Tools own event creation, inspection, revision, and lifecycle; no timeline Tool is added.

Plan (execution steps)
- [x] S0) Remove the uncommitted first-class temporal S3 code/tests, rewrite Track 021 to this event-kind plan with a deferred appendix, reconcile event-kind memories, run the baseline suite, and record evidence.
- [x] S1) TDD the canonical kind registry without changing the public kind matrix: focused failing domain tests, complete current pair guidance, derived unchanged `ALLOWED_KINDS`, focused remember-schema compatibility, refactor, validation, and Track update.
- [x] S2) TDD the complete event vertical in one coherent chunk: project-only `EVENT`, event guidance, compatible strict `occurred_at`, draft/record parsing and serialization, duplicate identity, service persistence, store immutability, portable remember schema/handler, exact inspection, focused compatibility tests, refactor, validation, and Track update.
- [x] S3) TDD model-facing guidance rendering for every pair through complete and flat `memory_remember` schemas, preserving runtime behavior; refactor, validate, and update the Track.
- [x] S4) Update README/architecture/glossary, run focused/full tests, direct MCP checks, and `git diff --check`, then record evidence.
- [x] S5) Confirm acceptance and move Track 021 to COMPLETED with synchronized status and final memory summary.

Current inventory
- `MemoryKind.EVENT` follows `STATE` and the canonical 14-pair kind registry allows it only under `project`; every pre-existing scope-kind pair and ordering remains unchanged.
- `MemoryRecordV2` and `MemoryDraft` carry trailing optional `occurred_at`, but authoritative parsing requires strict UTC-second presence exactly for event and rejects presence for non-events. Non-event serialization remains unchanged.
- Duplicate identity now has one occurrence position after kind: events use their parsed instant and non-events use `None`; draft/record call sites and service duplicate behavior are covered together.
- `MemoryService.remember()` persists occurrence time; revision and lifecycle dataclass replacements preserve it. Store replacement treats it as immutable.
- `MemoryRevision` and the public revise schema expose no occurrence replacement; explicit forbidden-field coverage locks that boundary.
- `memory_remember` publishes optional top-level `occurred_at` for flat clients and a strict project-branch event/non-event condition; enabled calls persist events while returning the existing minimal result.
- Every complete scope branch now renders its canonical ordered `<kind>: <guidance>` pairs in `kind.description`; the top-level flat-client kind description groups the same canonical guidance by scope without changing enums, fields, required keys, conditions, or runtime behavior.
- Exact inspection returns event `occurred_at` through shared canonical serialization; recall/list ordering and projections remain non-temporal.
- README, architecture, and glossary now document event semantics, strict structural occurrence time, guidance rendering, compatibility, immutable boundaries, and the deferred first-class temporal model.
- The public compatibility marker is `0.1.2` across package metadata, initialize, `/version`, and `list_tools`; the restarted connected server directly reports that current marker.
- `scopes.py` still defines exactly six scopes and imports no memory kind, preserving the current one-way dependency.
- No `mnemosyne/temporal/`, temporal test package, temporal setting, temporal Tool, or temporal storage path remains in the working tree after rollback.
- The event-kind memory collection contains eight active records. The implementation summary is current at revision 5, and the duplicate-key verification is resolved at revision 4.

Deferred future option: first-class temporal model
- Status: DEFERRED/YAGNI, not an executable requirement and not authoritative for current implementation.
- Revival gate: a concrete observed case must require one occurrence to participate in multiple independent histories, or repeated real usage must show that event-kind placement cannot satisfy the workflow. Do not revive for architectural neatness alone.
- Deferred model: independent Timeline (`tln_...`), Occurrence (`occ_...` with immutable occurrence time), and composite TimelineMembership record families under a visible non-scope temporal subtree.
- Deferred storage: one occurrence source, timeline-oriented membership files, bounded reverse membership scans, typed temporal repositories, and one-file atomic operations without hidden indexes or multi-file transaction claims.
- Deferred references/reads: family-specific exact references and inspection, timeline and directional membership inventories, active-only half-open-range chronology, deterministic ordering, and authenticated snapshot cursors.
- Deferred writes/lifecycle: caller-identified create operations, complete timeline/occurrence revision, family-specific archive/restore/forget, dormant memberships, dependency-blocked endpoint deletion, and independent default-off temporal gates.
- Deferred trade-off: cleaner scope-independent many-to-many chronology at the cost of a large Tool surface and multiple consent-gated calls before one useful event appears.
- Preservation: this appendix, Track history, commit `617426f`, and the authoritative revert decision retain the design rationale. The uncommitted S3 implementation was intentionally removed rather than preserved as dead code.

Design history
- The original event-kind design was accepted, then temporarily replaced by the first-class temporal model after a speculative knowledge-formation example.
- No concrete many-to-many occurrence case could be recalled on review. The user accepted event-kind's limitation in exchange for a design models can populate through existing memory behavior.
- First-class S3 reached 45 focused passing tests and 140 compatibility tests but was never committed or pushed; it was removed before repositories, Tools, settings, routes, or documentation were added.

Artifacts
- Commit `617426f` (`Draft event timeline track`) was pushed before either implementation path.
- User decision memory `Revert to event-kind approach; defer first-class timelines` is the authoritative pivot record.
- Current-code confirmation on 2026-07-20 found `records.py` and `scopes.py` unchanged from the original design assumptions.
- S0 repository rollback removed all six uncommitted `mnemosyne/temporal/` modules and five temporal test files, then rewrote/renamed Track 021 to the event-kind plan with the first-class model retained only as a deferred appendix.
- S0 memory reconciliation revised the summary and structural occurrence-time anchors to revision 4, restored five archived event-kind records at their exact revisions, and verified all eight collection records active plus both revised contents through direct MCP Tools.
- S0 baseline validation: `PYTHONPATH=. pytest -q` passed 708 tests in 8.45 seconds and `git diff --check` passed.
- S1 red evidence: `PYTHONPATH=. pytest -q tests/memory/test_records.py -k kind_definitions` failed during collection because `KIND_DEFINITIONS` did not exist.
- S1 focused green evidence: the two new kind-definition tests and the focused remember-schema compatibility test passed; the complete records/remember/import-boundary slice passed 88 tests in 0.27 seconds.
- S1 full validation: `PYTHONPATH=. pytest -q` passed 710 tests in 8.29 seconds and `git diff --check` passed.
- S2 red evidence: the focused event/occurrence slice failed during collection because `MemoryKind.EVENT` did not exist.
- S2 focused green evidence: 48 event/occurrence-selected tests passed, then the complete records/service/store/remember/inspect/revise/archive/restore slice passed 260 tests in 0.57 seconds.
- S2 full validation: `PYTHONPATH=. pytest -q` passed 729 tests in 8.42 seconds and `git diff --check` passed.
- S3 red evidence: `PYTHONPATH=. pytest -q tests/mcp/test_memory_remember.py -k renders_canonical_kind_guidance` failed because complete branch kind schemas had no description.
- S3 focused green evidence: the new guidance-rendering test passed; complete remember/tool-argument/registry/import-boundary compatibility passed 128 tests in 0.30 seconds.
- S3 full validation: `PYTHONPATH=. pytest -q` passed 730 tests in 8.47 seconds and `git diff --check` passed.
- S4 version-marker red evidence: `PYTHONPATH=. pytest -q tests/mcp/test_list_tools.py -k compatibility_build` failed because the test expected `0.1.2` while the server still reported `0.1.1`.
- S4 focused validation: list-tools, startup-settings, registry, remember, inspect, records, service, and store-mutation coverage passed 252 tests in 7.78 seconds.
- S4 full validation: `PYTHONPATH=. pytest -q` passed 730 tests in 8.43 seconds and `git diff --check` passed.
- S4 connected-client baseline: direct `list_tools` reported `Server: mnemosyne 0.1.1`, correctly identifying the existing client connection as stale after the contract/version update.
- S4 isolated direct MCP verification: a temporary server at `127.0.0.1:8772` reported initialize version `0.1.2`; `tools/list` exposed project `event`, top-level `occurred_at`, grouped flat guidance, and project event guidance; an enabled synthetic event returned `remembered`; exact inspection returned kind `event` and `occurred_at: 2026-07-20T15:00:00Z`. The server stopped and its temporary memory root was removed.
- S5 connected-server verification: after restart, direct `list_tools` reported `Server: mnemosyne 0.1.2` with the complete enabled Tool set.
- S5 memory reconciliation: the implementation summary advanced from revision 4 to 5; the duplicate-key verification advanced from revision 3 to 4 and now records the tested `None` position for non-events. An initial summary revision containing the dotted version literal was safely refused before write by the bounded token-signature policy; the approved semantically equivalent wording then succeeded.

Completion notes
- S0 rollback completed with a clean baseline and reconciled memory.
- S1 established the canonical pre-event guidance registry without changing the then-current public kind matrix.
- S2 delivered the complete event vertical through existing memory Tools: project-only event classification, strict structural occurrence time, duplicate identity, persistence, immutable replacement, exact inspection, and revision/lifecycle preservation. No first-class temporal resource or chronological query behavior was added.
- S3 rendered all canonical pair guidance into complete and flat `memory_remember` schema descriptions without changing execution behavior.
- S4 synchronized public documentation and version `0.1.2`, then passed focused, full, whitespace, and isolated direct MCP verification.
- S5 confirmed all acceptance criteria, reconciled the final project memories, verified the restarted server marker, and synchronized Track status/path/title to COMPLETED. Final result: project-only event memory with strict immutable occurrence time and canonical model-facing kind guidance, delivered through existing memory Tools while the first-class temporal model remains deferred.

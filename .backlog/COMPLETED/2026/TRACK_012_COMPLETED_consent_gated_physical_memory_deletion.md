# TRACK 012 [COMPLETED]: consent-gated physical memory deletion

Track
- ID: TRACK_012
- Repository: Mnemosyne
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_012_COMPLETED_consent_gated_physical_memory_deletion.md

Problems (PORE)
- P1: As a user governing durable context, I cannot permanently remove an obsolete canonical memory through MCP, because physical deletion exists only as an unregistered shared-domain primitive.
- P2: As a user approving irreversible deletion, I risk deleting an active, stale, or unintended record, because public forget has no archived-state, exact-reference, or expected-revision contract.
- P3: As a user requiring explicit control over destructive mutation, I need physical deletion absent unless separately operator-enabled and approved for that exact call, because archive/restore enablement and model intent are not deletion consent.
- P4: As a user expecting forgotten content to disappear, I need Mnemosyne to retain no tombstone, hidden history, copied record body, or content-bearing log, because deletion must not create another durable memory source.
- P5: As a Tool caller, I need bounded outcomes for invalid, active, missing, stale, changed, unavailable, uncertain, and unexpected deletion cases, because unlinking is irreversible and cannot use archive-style idempotency.
- P6: As a user deciding whether to approve deletion, I need exact recovery limitations documented, because Mnemosyne cannot restore a successfully forgotten record or guarantee erasure from external backups and storage remnants.

Objective
- Expose one narrow, canonical-only, archived-only, independently enabled `memory_forget` MCP Tool that revision-checks and physically removes one exact record after per-call approval, creates no tombstone, minimizes results and logs, and clearly communicates irreversibility and uncertain outcomes.

Non-negotiables
- Implementation begins only after the resolved contracts below are recorded and the Move-to-ACTIVE step is checked; ACTIVE work proceeds one declared TDD chunk at a time.
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- `mnemosyne/memory/` remains the owner of reference validation, revision and archived-state policy, fingerprint/write conflicts, physical deletion, storage safety, and deletion-outcome meaning; the MCP Tool remains a thin adapter.
- Public forget accepts no filesystem path, memory root, filename, query, broad selector, record content, lifecycle target, timestamp, fingerprint, model confirmation, or server-owned field.
- Public forget is limited to canonical version-2 memory. Legacy version-1 deletion, ambiguity resolution, and automatic migration remain prohibited.
- Active memory cannot be forgotten directly; it must first pass through the reversible archive flow and be inspected again at its current revision.
- Every forget call requires both independent explicit operator enablement and MCP-client approval for the complete exact arguments. A model-provided consent field is never accepted.
- Clients that cannot enforce per-call approval must leave forget disabled. OpenCode `always`, `--auto`, and interactive auto-approval remain unsupported while mutation is enabled.
- Results and logs must not contain title, content, tags, labels, complete arguments, paths, fingerprints, exception text, tracebacks, or a copied deleted record body.
- Mnemosyne creates no tombstone, hidden history, backup, deletion manifest, retained hash, or content-bearing index entry; this does not claim secure erasure from filesystem journals, snapshots, backups, MCP-client history, or external copies.
- Automated and direct checks use isolated temporary roots and remove all resulting fixtures and logs.
- No commit or push occurs unless explicitly requested.

Acceptance criteria
- [x] A1) [P1, P3] Default discovery and dispatch omit `memory_forget`; exact independent operator enablement exposes its definition and handler without enabling or changing remember, archive, restore, or read-only Tool behavior.
- [x] A2) [P2, P5] The Tool accepts exactly one canonical version-2 reference and exact positive-integer `expected_revision`; legacy references, paths, content, confirmation fields, missing fields, booleans, floats, and unknown fields are rejected before root resolution.
- [x] A3) [P1, P2] One approved forget call on an archived canonical record at its current revision removes exactly its source file, returns `forgotten` plus the same versioned reference, and leaves empty organizational directories intact.
- [x] A4) [P2, P6] A current active record returns bounded `conflict` / `not_archived`, remains byte-for-byte unchanged, and can first be archived through the established reversible flow.
- [x] A5) [P2, P5] A stale revision always returns `revision_conflict`; an external fingerprint/content change returns `write_conflict`; neither deletes the current changed record.
- [x] A6) [P5, P6] A second call after successful deletion returns `not_found`, not an idempotent forgotten outcome or fabricated tombstone-backed confirmation.
- [x] A7) [P2, P5] Public legacy references return `invalid_reference` without legacy discovery, ambiguity resolution, migration, or deletion.
- [x] A8) [P3] Project OpenCode policy denies the broad server prefix, explicitly allows read-only Tools, and asks for forget after the other exact mutation rules; documentation requires `once` and treats `reject` as no server request or write.
- [x] A9) [P4] Successful deletion creates no tombstone, hidden history, temporary artifact, backup, index entry, retained hash, or copied content; unrelated files remain unchanged apart from necessary parent-directory metadata.
- [x] A10) [P4] Success contains only status and canonical versioned reference. One terminal log contains only an approved operation/outcome allowlist and never records identity details beyond approved scope/schema metadata, content, complete arguments, paths, exception details, or tracebacks.
- [x] A11) [P5, P6] Failure after unlink but before confirmed directory durability has a distinct bounded uncertain-outcome contract with inspect-before-retry recovery instructions and no false guarantee that the record remains present.
- [x] A12) [P1, P2, P3, P4, P5, P6] Focused automated tests, import-boundary checks, the full suite, whitespace validation, isolated direct MCP checks, configured-client checks when available, and complete cleanup pass.
- [x] A13) [P1, P2, P3, P4, P5, P6] `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` document the exact request, independent gate, archived prerequisite, consent, outcomes, failures, no-tombstone boundary, irreversibility, external-copy limitations, restart requirements, and recovery procedure.

Why now / impact
- Track 011 established exact inspection, reversible archive/restore, revision conflicts, independent enablement, and per-call approval. A stale bug memory was successfully archived through the new Tool, proving the recoverable staging flow; permanent deletion is now the next explicit governance capability rather than an ad-hoc filesystem action.

Scope
- In scope:
  - One public MCP Tool tentatively named `memory_forget`.
  - Strict canonical version-2 reference plus positive exact-integer `expected_revision` request contract derived from shared memory definitions.
  - Archived-state prerequisite and thin adaptation to shared service/store deletion.
  - Independent default-off operator setting and immutable startup registration.
  - Per-call OpenCode approval ordering and restart/unsafe-auto-approval documentation.
  - Minimal `forgotten` result and bounded validation, disabled, active-state, not-found, revision, write, storage, uncertain-outcome, and internal failures.
  - No-tombstone, no-retained-body, unrelated-file, empty-directory, and second-call behavior.
  - Content-free terminal logging with a reviewed metadata allowlist.
  - Focused domain, store, schema, handler, registry, settings, import-boundary, route, logging, client-policy, and isolated direct MCP coverage.
  - Public documentation and architecture/glossary updates.
- Out of scope:
  - Legacy version-1 public deletion or automatic migration to version 2.
  - Direct deletion of active canonical memory.
  - Scope-wide, bulk, query-based, paginated, background, age-based, duplicate-based, or contradiction-based deletion.
  - Secure disk erasure, block wiping, filesystem-journal cleanup, snapshot deletion, backup management, MCP-client transcript deletion, or deletion of external copies.
  - Tombstones, audit databases, deletion manifests, retained record hashes, hidden history, event sourcing, or content-bearing indexes.
  - Empty-directory cleanup, namespace/collection cleanup, multi-process locking, or transactional filesystem redesign.
  - Revise, relocate, reclassify, recall changes, archive/restore changes beyond necessary compatibility, or other mutation Tools.
  - Caller-supplied paths, roots, filenames, content, tags, labels, timestamps, target state, or client/model confirmation fields.

Milestones
- [x] M1) Public eligibility, request/result, archived prerequisite, enablement, consent, irreversibility, uncertainty, errors, logs, registration, and validation decisions are complete and the Track is eligible for ACTIVE.
- [x] M2) Focused TDD exposes consent-gated archived canonical physical deletion while preserving shared-domain ownership, all existing mutation/read-only contracts, and no-tombstone semantics.
- [x] M3) Documentation, full validation, configured/direct checks, cleanup, and completion transition are recorded.

Risks / decisions
- Risk: Physical deletion is irreversible, so accepting active memory or stale identity would bypass the recoverable archive/restore safety flow.
- Risk: Supporting legacy deletion would lack a revision binding between inspection, approval, and deletion and could require ambiguous bounded discovery.
- Risk: Reusing archive/restore enablement would silently authorize a more destructive capability; another setting increases startup configuration complexity.
- Risk: A parent-directory sync failure can occur after unlink, so a normal storage error may conceal that deletion already happened.
- Risk: Filesystem snapshots, journals, backups, client history, logs outside Mnemosyne, and copied content can retain data despite source-file deletion.
- Risk: Empty directories can reveal organizational structure even after the only record is removed; deleting them safely is a separate policy problem.
- Decision (prior Track 006): Forgetting is physical source-file deletion with no tombstone, hidden history, or automatic directory cleanup.
- Decision (prior Track 011): Reversible archive/restore, canonical structured references, current expected revisions, independent operator gates, exact per-call approval, and content-minimized results/logs precede irreversible deletion.
- Decision (initial direction): Public forget is canonical-only and archived-only, returns only `forgotten` plus the versioned reference, and treats a repeat as `not_found` because no tombstone exists.
- Decision (initial direction): Use a separate default-off forget gate rather than widening remember or archive/restore enablement.

Open questions
- [x] Q1) Public `memory_forget` is strictly canonical version 2; legacy references fail validation before discovery and legacy deletion remains unexposed.
- [x] Q2) Every eligible record must be archived at its current revision. Revision is checked before state, so stale requests return `revision_conflict`; a current active record returns `not_archived`.
- [x] Q3) The request is exactly `{reference: <canonical version-2 reference>, expected_revision: <positive exact integer>}`. Unknown fields and boolean, float, string, null, zero, or negative revisions are invalid.
- [x] Q4) Success is exactly `{status: "forgotten", reference: <same canonical versioned reference>}` with no lifecycle, timestamp, deleted metadata, fingerprint, or storage wrapper.
- [x] Q5) A call beginning after deletion returns `not_found`; no outcome claims idempotent confirmation because no tombstone exists.
- [x] Q6) Stable mappings are: invalid/legacy reference -> `invalid_request`/`invalid_reference`; invalid revision -> `invalid_request`/`invalid_expected_revision`; disabled -> `policy_error`/`mutation_disabled`; active -> `conflict`/`not_archived`; absent -> `not_found`/`not_found`; stale -> `conflict`/`revision_conflict`; changed after selection -> `conflict`/`write_conflict`; unsafe or unavailable before unlink -> `storage_error`/`memory_source_unavailable`; failure after unlink before confirmed directory durability -> `uncertain`/`deletion_outcome_uncertain`; unexpected pre-unlink failure -> `internal_error`/`internal_error`. Messages remain bounded and content-free.
- [x] Q7) Independent enablement uses exact `MNEMOSYNE_MEMORY_FORGET_ENABLED`, otherwise strict `[memory].forget_enabled`, otherwise false. All supplied environment values are validated before file access; each overrides only its setting; unresolved settings share at most one strict file read; startup registration is immutable.
- [x] Q8) Shared errors distinguish `MemoryNotArchived` from `DeletionOutcomeUncertain`. Ordinary pre-unlink storage failures retain normal bounded errors; any ordinary failure after successful unlink and before parent-directory sync confirmation becomes uncertain.
- [x] Q9) On uncertainty, do not blindly retry: inspect the same reference. `not_found` means currently absent but is not tombstone-backed proof; a present record must be reviewed, remain archived, and use its current revision in a newly approved call; unavailable inspection leaves the outcome uncertain.
- [x] Q10) The store deletion point validates a canonical reference and exact positive revision, safely loads matching version-2 identity, checks revision then archived state, revalidates path/fingerprint immediately before unlink, unlinks only the selected path, syncs its parent, and returns no record body. A shared in-process store mutation lock serializes cooperating Mnemosyne writers; external/multi-process last-instruction races and secure erasure remain outside guarantees.
- [x] Q11) Logger `mcp.memory_forget` emits one terminal event per reached handler call. INFO is used for success, WARNING for bounded request/policy/conflict/storage/uncertain outcomes, and ERROR without traceback for unexpected failure. The allowlist is event, outcome, stable code/field, schema version, and validated scope only.
- [x] Q12) Forget reuses only the strict canonical request schema/parser and generic text-result mechanics from `_memory_lifecycle.py`; it has a deletion-specific executor/result projection and does not use lifecycle-state result semantics.
- [x] Q13) Add a three-file `memory_forget` Tool package, preserve shared-domain and thin-route import boundaries, and extend focused domain, schema, handler, registry, settings, startup, route, logging, and both OpenCode policy-source tests. Isolated direct checks prove default omission, independent enablement, active/stale/write/uncertain outcomes, approved physical deletion, second-call absence, no artifacts, and cleanup; configured-client checks separately prove `reject` no-call and `once` execution when available.

Decision log
- Decision (initial inspection): `MemoryService.forget()` and `FilesystemMemoryStore.delete()` already support physical canonical and legacy deletion behind mutation-disabled shared-domain policy, but no public Tool, independent gate, archived prerequisite, exact revision-type check, safe logs, or protocol result exists.
- Decision (initial inspection): Canonical store deletion checks persisted revision and fingerprint before unlink, retains empty directories, and creates no tombstone; existing tests cover basic canonical/legacy deletion and revision mismatch.
- Decision (initial inspection): The store currently unlinks before syncing the parent directory. A sync failure can therefore return `MemorySourceUnavailable` after the source file is absent, making deletion outcome uncertainty a blocking public-contract decision.
- Decision (initial inspection): Track 011 provides canonical reference/revision parsing and enabled mutation patterns, but its shared executor assumes persisted lifecycle results and idempotent states, so forget should reuse only narrow request mechanics unless a deletion-specific private adapter is justified.
- Decision (initial inspection): Current startup settings and OpenCode policy independently gate remember and archive/restore only; physical forget must not be enabled by either existing mutation setting.
- Decision (2026-07-19, Q1-Q5): Public forget is canonical-only, archived-only, revision-bound, non-idempotent after success, and projects only `forgotten` plus the same versioned reference.
- Decision (2026-07-19, Q6-Q10): The shared domain owns `not_archived` and post-unlink `deletion_outcome_uncertain`; revision precedes state; definitive state/revision/fingerprint checks occur at deletion; cooperating in-process writers share a store mutation lock; uncertainty requires inspect before any newly approved retry.
- Decision (2026-07-19, Q7): Forget has an independent exact environment/file/default startup gate resolved in the existing combined at-most-one-read settings snapshot.
- Decision (2026-07-19, Q11-Q13): Forget uses a content-free dedicated logger and deletion adapter, reuses only strict lifecycle request mechanics, keeps a three-file Tool package, and requires automated plus isolated direct/configured-client evidence.
- Decision (2026-07-19, client policy inspection): `.opencode/agents/mnemosyne.md` currently contains a broad `mnemosyne_*: allow` override that conflicts with exact mutation approval. The policy chunk must remove that bypass and test both policy sources before forget can be enabled.

Plan (execution steps)
- [x] S1) Resolve Q1-Q13 and record exact eligibility, request/result, archived-state, enablement, consent, irreversibility, no-tombstone, uncertainty/recovery, error/logging, registration, boundary, and isolated-validation contracts.
- [x] S2) Move Track 012 to ACTIVE (folder, filename, title, and current path status) and check this step before implementation begins.
- [x] S3) Execute one TDD chunk for shared service/store archived-only canonical deletion, exact revision validation, state/revision/fingerprint conflicts, pre-unlink failures, post-unlink uncertainty, no-tombstone/no-artifact behavior, and explicit legacy compatibility boundaries.
- [x] S4) Execute one TDD chunk for strict `memory_forget` definition, canonical reference/revision adaptation, disabled handler, minimal success/error projections, package exports/import boundaries, and fail-closed registry injection without startup exposure.
- [x] S5) Execute one TDD chunk for the independent strict forget setting, immutable startup selection, both discovery surfaces, dispatch/restart behavior, and OpenCode exact per-call approval ordering.
- [x] S6) Execute one TDD chunk for enabled shared-service forget adaptation, archived success, active/stale/missing/legacy/write/storage/uncertain/internal outcomes, physical absence, recall/inspect/restore behavior, and content-free terminal logs.
- [x] S7) Update `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md`; run focused and full automated validation plus `git diff --check`; perform isolated direct MCP/configured-client checks and cleanup; record evidence.
- [x] S8) Confirm acceptance and milestones, move Track 012 to COMPLETED with synchronized status, and record final outcomes.

Current inventory
- Baseline commit `0d9419c` (`Add consent-gated memory lifecycle tools`) is synchronized on `main` and `origin/main`; the working tree is clean before this planning-only Track is added.
- `MemoryService.forget()` returns `ForgetResult(status, reference)`, requires domain mutation enablement, accepts canonical or legacy references, accepts optional expected revision, and delegates directly to `FilesystemMemoryStore.delete()` without exact revision-type or archived-state validation.
- `FilesystemMemoryStore.delete()` resolves the selected record, compares canonical revision, compares the current fingerprint, unlinks the source, syncs the parent directory, returns the prior stored wrapper, leaves directories intact, and creates no tombstone.
- Because parent-directory sync occurs after unlink, a sync failure currently raises `MemorySourceUnavailable` even though the file may already be absent. No distinct uncertain-outcome domain error exists.
- Existing shared tests cover basic canonical physical deletion, canonical revision mismatch, retained directories, and legacy physical deletion. They do not cover active-versus-archived eligibility, exact revision types, repeat calls, fingerprint races during deletion, post-unlink uncertainty, broad no-artifact snapshots, or public adaptation.
- `_memory_lifecycle.py` already derives the strict canonical reference/expected-revision schema and parser used by archive/restore. Its executor and result validator are lifecycle-state-specific and do not directly fit tombstone-free deletion.
- `memory_archive` and `memory_restore` establish separate three-file Tool packages, validation-before-root-resolution, enabled shared-service construction, minimal projections, stable bounded errors, and content-free terminal logs.
- `MemoryToolSettings` currently contains independent `remember_enabled` and `archive_restore_enabled` booleans; both environment/file/default paths share one strict startup snapshot and at most one file read.
- The immutable registry always exposes list/recall/inspect, conditionally appends archive/restore together, then conditionally appends remember. No forget definition or handler exists.
- `opencode.json` denies broad Mnemosyne access, allows the three read-only Tools, and asks for remember, archive, and restore. It has no forget permission.
- `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` identify physical forget as unregistered, tombstone-free domain behavior and the next roadmap capability.
- Activation inspection found that store locks are instance-local while mutation handlers construct stores per call, so they do not serialize cooperating cross-call writers. S3 will introduce a shared in-process store mutation lock while retaining explicit multi-process/external-race limits.
- Activation inspection found `.opencode/agents/mnemosyne.md` broadly allows `mnemosyne_*`, potentially overriding exact mutation approval in `opencode.json`; S5 must remove this bypass and add coverage for both policy sources.
- S3 added shared-domain `MemoryNotArchived` and `DeletionOutcomeUncertain` errors. `MemoryService.forget()` and `FilesystemMemoryStore.delete()` now accept only canonical references with exact positive-integer revisions, check revision before archived state, and return no deleted storage wrapper.
- S3 deletion revalidates safe path components and a bounded fingerprint immediately before unlink, maps observed post-selection disappearance/change to `WriteConflict`, leaves directories and unrelated files intact, creates no deletion artifact, and distinguishes parent-directory sync failure after unlink as uncertain.
- `FilesystemMemoryStore` mutation locks are now shared by absolute memory-root key across in-process store instances, serializing cooperating create/replace/delete operations. Multi-process and adversarial external last-instruction races remain explicitly out of scope.
- Legacy records remain readable through existing inspection/store lookup but are rejected before public-oriented service/store deletion access; no legacy discovery, migration, or deletion is introduced.
- S4 added the three-file `memory_forget` Tool package and private `_memory_forget.py` MCP adapter. The Tool schema reuses the strict canonical reference/current-revision request mechanics, while the deletion adapter validates only `forgotten` plus the same reference and never projects lifecycle or deleted record data.
- The direct handler remains disabled by default and validates before root resolution. S4 intentionally maps only invalid, disabled, success, and inconsistent-operation behavior; enabled domain failure mappings and terminal-log coverage remain the declared S6 chunk.
- `build_tool_registry()` now accepts an injectable independent forget Tool/handler pair, omits it while disabled, and fails closed when enabled registration is incomplete. `build_startup_tool_registry()` and the immutable startup registry do not yet pass or expose forget; setting/startup integration remains S5.
- Import-boundary coverage requires exactly the three public Tool-package modules, keeps storage construction in the public handler rather than the private adapter, and prohibits archive/restore, route, and FastAPI coupling.
- S5 added independent startup-fixed `forget_enabled` resolution through exact `MNEMOSYNE_MEMORY_FORGET_ENABLED`, otherwise strict `[memory].forget_enabled`, otherwise false. All three mutation settings share the existing environment-first, at-most-one-file-read resolver and remain independent.
- Startup registration now appends the real forget definition/handler after archive, restore, and remember when enabled. Both MCP `tools/list` and the `list_tools` Tool use the same immutable selection; disabled dispatch remains unknown, invalid enabled dispatch validates before root creation, and configuration changes require restart.
- OpenCode policy now asks for exact `memory_forget` calls after the existing mutation rules. The scoped Mnemosyne agent no longer broadly allows `mnemosyne_*`; it denies the broad prefix, allows only the three read-only Tools, and asks for remember/archive/restore/forget in last-match order. Automated policy tests cover both configuration sources.
- S6 completed enabled Tool adaptation with stable bounded mappings for defensive validation, disabled mutation, active-state conflict, absence, stale revision, fingerprint/write conflict, pre-unlink storage failure, post-unlink uncertainty, and unexpected failure. The uncertainty message explicitly requires inspection of the same reference before any retry.
- Each reached forget handler call emits exactly one `mcp.memory_forget` terminal event. Logs contain only event, bounded outcome/code/field, schema version, and validated scope; tests exclude IDs, namespace/collection identity, paths, content-bearing details, exception text, and traceback information.
- Real enabled integration now proves an archived current-revision call physically removes exactly the source record, retains organizational directories, preserves an unrelated file, creates no deletion artifact, and returns only `forgotten` plus the same reference. Subsequent inspect, recall, restore, and forget calls report absence/no matches rather than fabricated idempotency.
- Real active/stale integration proves revision conflict precedes archived-state conflict and neither outcome changes record bytes or modification time. Public legacy rejection remains covered by strict request validation before enabled adaptation.
- S7 updated `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` with the exact forget request/result, independent gate, archived prerequisite, revision/state ordering, per-call consent, bounded outcomes, uncertainty recovery, logging, no-tombstone behavior, irreversibility, external-copy limits, startup/restart requirements, package ownership, and OpenCode `once`/`reject` rules.

Artifacts
- Shared domain/delete prerequisite: `.backlog/COMPLETED/2026/TRACK_006_COMPLETED_shared_memory_domain_architecture.md`.
- Consent and registration prerequisite: `.backlog/COMPLETED/2026/TRACK_007_COMPLETED_consent_gated_memory_remember.md`.
- Persistent settings prerequisite: `.backlog/COMPLETED/2026/TRACK_009_COMPLETED_local_settings_file.md`.
- Exact inspection/reference prerequisite: `.backlog/COMPLETED/2026/TRACK_010_COMPLETED_read_only_memory_inspection.md`.
- Reversible lifecycle prerequisite: `.backlog/COMPLETED/2026/TRACK_011_COMPLETED_consent_gated_memory_archive_restore.md`.
- Baseline implementation: commit `0d9419c` (`Add consent-gated memory lifecycle tools`).

Completion notes
- DRAFT created on 2026-07-19 after TRACK_011 was completed, committed, pushed, enabled locally, and used to archive one stale bug memory. Existing physical-delete primitives and their safety gaps were inspected, but no implementation or implementation-driving test was added.
- Moved to ACTIVE on 2026-07-19 after Q1-Q13 were resolved. The approved first implementation chunk is S3 only; no MCP Tool, startup setting, registry, documentation, commit, or push is included in that chunk.
- S3 TDD evidence (2026-07-19): the first focused run failed during collection because `DeletionOutcomeUncertain` and `MemoryNotArchived` did not exist. After the minimal domain implementation, the focused store/service run passed `58 passed in 0.35s`; the full suite passed `464 passed in 4.04s`; `git diff --check` passed with no output. No direct MCP check was applicable because S3 exposes no MCP Tool. The next unchecked step is S4.
- S4 TDD evidence (2026-07-19): the first focused run failed during collection with `ModuleNotFoundError: mnemosyne.mcp.tools.memory_forget`. After the minimal Tool, adapter, registry injection, and boundary implementation, focused MCP/registry/import tests passed `50 passed in 0.19s`; the full suite passed `487 passed in 3.96s`; `git diff --check` passed with no output. Default startup discovery and dispatch remain unexposed by automated assertion. No direct MCP check was needed because S4 deliberately leaves the startup registry unchanged. The next unchecked step is S5.
- S5 TDD evidence (2026-07-19): the first focused run failed during collection because `get_memory_forget_enabled` did not exist. After the minimal settings, registry, startup, route-matrix, and OpenCode policy implementation, one focused run exposed the intended three-setting precedence requirement in an existing invalid-file override test; supplying all three overrides made the test pass without file access. Final focused validation passed `130 passed in 4.76s`; the full suite passed `509 passed in 5.27s`; `git diff --check` passed with no output. Fresh-process tests cover file/environment enablement, both discovery surfaces, dispatch, independent ordering, invalid-value failure before file access, no root creation, and restart-fixed selection. The next unchecked step is S6.
- S6 TDD evidence (2026-07-19): the focused test run initially failed `12 failed, 17 passed` because enabled domain exceptions were intentionally still mapped to `internal_error`. After the minimal ordered error adaptation, focused forget tests passed `29 passed in 0.17s`; the full suite passed `523 passed in 5.26s`; `git diff --check` passed with no output. Automated integration used an isolated temporary memory root and pytest cleanup; no durable fixture or content-bearing log was created. The next unchecked step is S7.
- S7 validation evidence (2026-07-19): focused Track coverage passed `228 passed in 5.03s`; the full suite passed `523 passed in 5.25s`; final `git diff --check` passed with no output. An isolated server ran on `127.0.0.1:8765` with only forget enabled and a synthetic archived revision-2 fixture under the approved temporary directory. Direct JSON-RPC checks proved both discovery surfaces listed exactly `list_tools`, `memory_recall`, `memory_inspect`, and `memory_forget`; one exact forget returned minimal `forgotten`; the source file was absent; exact inspect and a second forget returned `not_found`; and two terminal forget events were bounded and content-free. The isolated server was stopped, port 8765 was confirmed closed, and its complete temporary directory was removed. The pre-existing port-8000 server was not changed; `opencode mcp list` remained connected to it. Interactive configured-client `once`/`reject` could not be safely exercised from this non-interactive API session, so automated policy assertions plus direct protocol evidence are recorded instead. The next unchecked step is S8.
- Completed on 2026-07-19. All acceptance criteria and milestones passed. Mnemosyne now exposes independently enabled, per-call-consent-oriented, canonical-only, archived-only physical forget with exact revision binding, minimal results, bounded content-free logs, no tombstone, explicit uncertain-outcome recovery, and documented irreversibility/external-copy limits. Final implementation evidence is `523 passed`, focused evidence is `228 passed`, direct isolated MCP deletion and cleanup passed, and whitespace validation passed. No commit or push was performed.

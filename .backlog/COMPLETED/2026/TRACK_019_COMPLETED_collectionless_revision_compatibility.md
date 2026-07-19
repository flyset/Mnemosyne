# TRACK 019 [COMPLETED]: Collectionless revision compatibility

Track
- ID: TRACK_019
- Repository: Mnemosyne
- Branch: main
- Current path: `.backlog/COMPLETED/2026/TRACK_019_COMPLETED_collectionless_revision_compatibility.md`

Problems (PORE)
- P1: As a Claude client user revising a collectionless memory, I cannot submit the required `collection_label: null`, because the client exposes an untyped field and its scalar interface cannot express bare JSON null.
- P2: As a caller correcting an invalid revision request, I receive a `collection_label` field paired with the message `revision field is invalid`, because revision validation collapses replacement-field errors into a contradictory generic message.
- P3: As an operator validating a reported fix, I cannot distinguish a stale Mnemosyne process through `list_tools`, because that Tool returns names without the server version.

Objective
- Make collectionless revision callable through flattened/stringifying clients, return field-consistent errors, and expose a version marker without weakening complete replacement or consent boundaries.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Never log raw revise arguments, memory content, labels, tags, IDs, paths, or submitted values.
- Do not mutate the reported production record during development or validation.
- Keep `collection_label` required for references whose `collection_id` is a string; permit omission only when the reference is collectionless.
- Preserve one-layer schema-aware normalization for stringified reference, tags, and expected revision values.
- Preserve startup-fixed mutation enablement and exact client approval requirements.

Acceptance criteria
- [x] A1) [P1] A revise request whose reference has `collection_id: null` may omit `collection_label`; the parsed replacement uses `None` and can revise a real isolated collectionless record.
- [x] A2) [P1] A revise request whose reference has a collection still requires `collection_label`; native null remains accepted as an explicit absent label, while the literal string `"null"` remains ordinary text.
- [x] A3) [P1] The published schema exposes nullable replacement text through direct client-visible types and durable descriptions, removes unconditional top-level `collection_label` requirement, and explains the conditional rule.
- [x] A4) [P1] Route/registry tests matching Claude's stringified reference, tags, and expected revision prove one-layer normalization preserves native nested null and reaches revise validation/dispatch without logging payload values.
- [x] A5) [P2] Missing and invalid replacement fields return `invalid_record` with the correct public field and a matching bounded field-specific message.
- [x] A6) [P3] `list_tools` includes the current Mnemosyne version, and the project/server patch version is bumped consistently so an old process is distinguishable.
- [x] A7) [P1, P2, P3] Applicable README, architecture, and glossary contracts are updated; focused/full tests and direct isolated MCP checks pass with no temporary artifacts.

Why now / impact
- Claude can now list and inspect the target but seven revise attempts produced no writes. The observed `invalid_collection` for literal `"null"` proves stringified reference/tags normalization reached the service; the remaining blocker is the required top-level null and misleading validation diagnostics.

Scope
- In scope:
  - Conditional collection-label omission for collectionless revise references.
  - Portable nullable replacement-field schemas and model-facing descriptions.
  - Field-specific revise validation errors.
  - Stringified transport and isolated physical collectionless revision coverage.
  - Version marker in `list_tools` and a patch version bump.
  - Applicable public documentation.
- Out of scope:
  - Logging raw Tool arguments or memory content.
  - Revising the user's real stakeholder record during development.
  - Changing immutable record identity, collection presence, or collection ID.
  - Patch semantics for namespace label, title, content, or tags.
  - Relaxing mutation enablement, revision checks, content policy, or client consent.

Milestones
- [x] M1) TDD the conditional request/schema/error contract.
- [x] M2) TDD stringified transport and physical collectionless MCP revision.
- [x] M3) TDD the operator-visible version marker.
- [x] M4) Reconcile documentation and complete automated/direct validation.

Risks / decisions
- Risk: Treating literal `"null"` globally as null would destroy a legitimate string value; do not add that coercion.
- Risk: Making `collection_label` broadly optional would turn complete replacement into an ambiguous patch; omission is accepted only when no collection exists structurally.
- Decision: Parse the reference before enforcing replacement completeness so collection presence can determine whether `collection_label` must be supplied.
- Decision: Use direct nullable scalar types plus prose rather than composition-only visibility for revised text fields.
- Decision: Prove the transport boundary through captured types and isolated fixtures rather than raw production-payload logging.
- Decision: Include the static server patch version in `list_tools`; public schema/contract changes must update the version consistently.

Open questions
- [x] Q1) Are Claude's stringified reference and tags decoded before revise validation?
- [x] Q2) Has collectionless revision succeeded anywhere?

Decision log
- Decision (Q1): Yes. The central normalizer and an existing startup-registry test decode one JSON layer for object/array/integer positions; the reported literal-`"null"` request reaching `invalid_collection` independently proves reference, nested null, and tags reached the service in typed form.
- Decision (Q2): Yes at parser/service level: nullable parsing and physical collectionless service revision tests pass. This Track adds the missing end-to-end MCP-handler success fixture.

Plan (execution steps)
- [x] S1) Move Track 019 to ACTIVE (folder, filename, and title status).
- [x] S2) TDD conditional request/schema/error behavior: first add focused failing tests for collectionless omission, collected omission refusal, direct nullable schema visibility/prose, and field-consistent messages; then implement minimally and validate.
- [x] S3) Add focused client-path regression coverage after S2: route/registry and real-handler tests use stringified reference/tags/revision plus omitted collection label to prove type preservation and isolated physical collectionless revision without production writes; no additional implementation is expected unless the tests expose a gap.
- [x] S4) TDD version visibility: first change focused `list_tools`/initialize/version expectations, then bump the patch version and expose it minimally through `list_tools`.
- [x] S5) Update README, architecture, and glossary; run focused/full/repository checks and isolated direct MCP validation; record evidence and move Track 019 to COMPLETED.

Current inventory
- `_memory_revise.py` now exposes nullable replacement text through direct string/null types and descriptions, conditionally defaults omitted collection label only for a collectionless parsed reference, retains collected-memory completeness, preserves literal `"null"`, and emits bounded field-specific validation messages.
- The central Tool argument normalizer decodes one stringified layer only when the declared position disallows strings; it correctly decodes revise reference, tags, and expected revision while preserving literal strings in nullable text fields.
- `MemoryService.revise()` already accepts `collection_label=None` for collectionless records and rejects non-null labels when no collection exists.
- Automated coverage now includes nullable/conditional parsing, stringified route and normalized registry boundaries, field-specific errors, physical collectionless revision through the real MCP handler, version consistency, and versioned list output.
- Route coverage now proves Claude-style string values reach central dispatch unchanged without entering logs; registry coverage proves one-layer normalization produces an object reference with native null, integer revision, and array tags before the selected handler; a real-handler temporary fixture proves physical collectionless revision with omitted collection label.
- MCP initialize and `/version` now expose `0.1.1`; `list_tools` prefixes its names with `Server: mnemosyne 0.1.1.` and a focused test enforces package/server version consistency.
- The working tree is clean at commit `45f2365` before this Track.

Artifacts
- Investigation (2026-07-19): raw running-server discovery showed `collection_label` as `anyOf` string/null and `expected_revision` as integer; initialize returned version `0.1.0`. The target inspected as collectionless, active, revision 1 and was not mutated. Focused existing revise/service tests passed 77 tests.
- Activated on 2026-07-19 after the user approved conditional collectionless omission, portable schemas, field-specific errors, stringified transport/physical MCP coverage, and a version marker.
- S2 TDD evidence (2026-07-19): `PYTHONPATH=. pytest -q tests/mcp/test_memory_revise.py` first produced 7 focused failures because collection label remained unconditionally required, nullable fields remained composition-only, missing namespace label still mapped to revision, and field messages were generic; 33 existing tests passed.
- S2 validation (2026-07-19): after the minimal shared revise-adapter/schema change, the focused revise file passed 40 tests and the broader revise/normalization/registry/record/service set passed 159 tests.
- S3 regression validation (2026-07-19): the new route, registry capture, and physical real-handler tests passed immediately after S2, confirming no additional production change was needed. The combined revise/registry/route set passed with 100 tests; all fixtures used temporary paths and the reported production record remained untouched.
- S4 TDD evidence (2026-07-19): the focused `list_tools` test first failed both the absent marker and old `0.1.0` assertions. After the minimal output and patch-version change, it passed; the first broader run then produced 14 expected exact-output failures in registry/startup tests, which were reconciled to the versioned contract.
- S4 validation (2026-07-19): list-tools, registry, startup-settings, MCP-route, and operational-route coverage passed with 85 tests at consistent version `0.1.1`.
- S5 documentation (2026-07-19): README, architecture, and glossary now document conditional collection-label omission, literal-string preservation, one-layer normalization, field-specific errors, content-free logging, and the static version marker.
- S5 automated validation (2026-07-19): the final focused revise/normalization/registry/startup/list-tools/route/record/service set passed with 204 tests; `PYTHONPATH=. pytest -q` passed with 705 tests; `git diff --check` passed.
- S5 direct discovery (2026-07-19): an isolated server at `127.0.0.1:8771` exposed initialize version `0.1.1`, `Server: mnemosyne 0.1.1.` in `list_tools`, collection label outside unconditional required fields, a direct string/null type, conditional omission prose, and integer expected revision.
- S5 direct mutation (2026-07-19): using only a synthetic temporary collectionless fixture, raw `tools/call` supplied Claude-style stringified reference/tags/revision and omitted collection label; it returned `revised` with native-null collection identity and revision 2. Exact inspection confirmed changed content, unchanged collection absence, and coherent lifecycle. Logs contained only bounded method/outcome/scope/lifecycle metadata. The isolated server stopped and its complete temporary directory was removed.
- Final review confirmed the reported production stakeholder record was inspected only during diagnosis and never mutated by implementation or validation.

Completion notes
- Completed on 2026-07-19. Collectionless revision now supports omitted collection label for clients unable to emit top-level null, while collected memories retain complete explicit replacement semantics and literal strings remain uncoerced.
- Validation errors now align field and message, and version `0.1.1` is visible through initialize, `/version`, and `list_tools` for stale-process detection.

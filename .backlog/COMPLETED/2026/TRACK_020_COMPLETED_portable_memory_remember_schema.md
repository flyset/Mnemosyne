# TRACK 020 [COMPLETED]: Portable memory remember schema

Track
- ID: TRACK_020
- Repository: Mnemosyne
- Branch: main
- Current path: `.backlog/COMPLETED/2026/TRACK_020_COMPLETED_portable_memory_remember_schema.md`

Problems (PORE)
- P1: As a model using an MCP client that projects only top-level object properties, I cannot construct a valid `memory_remember` call, because all nine declared fields exist only inside top-level `oneOf` branches and the client reduces the Tool to an empty parameter object.
- P2: As a Tool caller diagnosing the resulting failure, I cannot tell whether `origin` is caller-owned or forbidden, because the projected empty request reaches the handler's first field check and returns `invalid_origin` without exposing the schema-loss root cause.

Objective
- Publish all nine caller-owned remember fields in a portable top-level schema while preserving strict scope-specific validation, both public origin values, mutation consent, and runtime behavior.

Non-negotiables
- Implementation followed one declared coherent TDD chunk while ACTIVE.
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Preserve the exact nine required caller-owned fields and the six scope-specific namespace-kind and memory-kind combinations.
- Preserve `explicit_user_statement` and `user_approved_proposal` as the only public caller-supplied origins; `recorded_via` and other operational provenance remain server-owned.
- Keep mutation default-off and preserve exact per-call MCP-client approval, content policy, handler behavior, persistence, results, errors, logging, and HTTP transport.
- Preserve all unrelated existing working-tree changes.

Acceptance criteria
- [x] A1) [P1] `memory_remember.inputSchema` exposes all nine caller-owned fields in top-level `properties`, requires all nine, and rejects additional properties.
- [x] A2) [P1] The six strict scope branches continue to derive and enforce each scope's allowed namespace kinds and memory kinds.
- [x] A3) [P1] A regression test simulates a client retaining only top-level properties and required fields and proves a complete valid remember request survives unchanged.
- [x] A4) [P2] Focused tests prove both documented public origin values pass Tool-owned origin validation, while non-public values retain `invalid_origin`.
- [x] A5) [P1, P2] README, architecture, and glossary documentation state the portable schema layout and caller-owned origin semantics.
- [x] A6) [P1, P2] Focused tests, the full suite, and whitespace validation pass without changing mutation behavior or creating durable memory outside test temporary roots.

Why now / impact
- Claude directly reported an empty generated parameter schema for `memory_remember`. The same composition-only interoperability failure was previously corrected for `memory_list`, and the standing architecture rule now requires caller-visible fields at top level.
- The empty projection also explains the misleading origin investigation: the current handler checks absent or non-public origin before parsing the rest of the draft.

Scope
- In scope:
  - `memory_remember` Tool-schema layout.
  - Top-level field schemas derived from existing shared dimensions.
  - Focused flattened-client and public-origin regression coverage.
  - Applicable README, architecture, and glossary clarification.
- Out of scope:
  - Handler, domain, storage, policy, result, error, log, permission, settings, or HTTP changes.
  - New origin values or server inference of origin.
  - Client-specific adapters outside the MCP Tool schema.

Milestones
- [x] M1) TDD the portable remember schema and origin regressions.
- [x] M2) Reconcile documentation and complete validation.

Risks / decisions
- Risk: Duplicating schemas at top level and inside strict branches could drift; construct both from shared schema helpers and lock derivation with tests.
- Risk: Flattening could weaken scope-specific validation; retain the existing six full `oneOf` branches as strict refinements.
- Decision: Top-level `properties`, `required`, and `additionalProperties` are the portable caller-facing field bag; `oneOf` retains scope-specific constraints for complete JSON Schema clients.
- Decision: `origin` is caller-owned provenance context, not consent. Consent remains the MCP client's per-call approval, while `recorded_via` remains server-assigned.
- Decision: No handler change is planned because current code accepts both public values and rejects only absent, wrong-type, or non-public values.

Open questions
- [x] Q1) Is `origin` intended to be caller-supplied?
- [x] Q2) Does the current handler accept both documented public origins?
- [x] Q3) Is the server omitting the remember fields entirely?

Decision log
- Decision (Q1): Yes. README, architecture, glossary, completed Track 007, and `MemoryDraft` define origin as one of nine caller-owned remember fields.
- Decision (Q2): Yes. `memory_remember.handler.PUBLIC_ORIGINS` contains both values and the first validation check accepts either exact string before parsing the complete draft.
- Decision (Q3): Raw source defines all fields, but only inside top-level `oneOf` object branches. Clients that keep only top-level properties observe an empty object, so this is a schema portability defect rather than complete server omission.

Plan (execution steps)
- [x] S1) Move Track 020 to ACTIVE (folder, filename, title, and current path status) and check this step before implementation begins.
- [x] S2) Execute one TDD chunk: add focused failing top-level schema/projection coverage plus public-origin regression coverage, minimally publish the existing nine schemas at top level while retaining six strict branches, update public documentation, and run focused/full/whitespace validation.
- [x] S3) Confirm acceptance, record evidence, and move Track 020 to COMPLETED with synchronized status.

Current inventory
- `mnemosyne/mcp/tools/memory_remember/definition.py` now derives a complete top-level field bag plus broad scope, namespace-kind, memory-kind, and public-origin enums from the same shared definitions used by the six strict full-object branches.
- Top-level `properties`, `required`, and `additionalProperties: false` preserve all nine caller-owned fields for flat clients; the unchanged `oneOf` structure still narrows namespace kind and memory kind by scope for composition-aware clients.
- Top-level origin prose identifies both values as caller-supplied provenance context rather than consent. `memory_remember.handler.py` remains unchanged and continues accepting both exact values while rejecting absent or non-public values as `invalid_origin`.
- `tests/mcp/test_memory_remember.py` now locks the top-level contract, simulates top-level-only projection through the real disabled handler, explicitly accepts both public origins, and retains all branch-local, invalid-origin, persistence, policy, result, and logging coverage.
- `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` document the portable field bag, strict branch refinements, public-origin meaning, server-owned `recorded_via`, and separate client-consent boundary.
- The working tree's pre-existing unrelated Track 019 changes remain present and unmodified by this Track except where shared documentation files received additive Track 020 paragraphs.

Artifacts
- User approval on 2026-07-19 covers Track creation/activation, the declared TDD chunk, documentation, and focused/full/whitespace validation.
- Activated on 2026-07-19 with synchronized folder, filename, title, and current path before implementation began.
- S2 red evidence: `PYTHONPATH=. pytest -q tests/mcp/test_memory_remember.py` failed the two new portability assertions because root `properties`, `required`, and `additionalProperties` were absent; 46 existing tests passed.
- S2 minimal green evidence: after publishing the top-level field bag from shared helpers, the focused remember file passed 48 tests.
- S2 refactor evidence: after consolidating shared top-level/branch property construction and adding bounded field guidance, remember plus schema-aware argument normalization passed 64 tests.
- S2 focused validation: remember, argument normalization, registry, MCP route, and import-boundary coverage passed 139 tests.
- S2 full/repository validation: `PYTHONPATH=. pytest -q` passed 708 tests in 8.40 seconds and `git diff --check` passed.

Completion notes
- S1 completed on 2026-07-19. The next unchecked step is S2, one coherent TDD chunk for portable schema publication, public-origin regression coverage, documentation, and validation.
- S2 completed on 2026-07-19 through one focused TDD chunk. The public Tool schema is now callable through a top-level-only client projection without changing handler, domain, storage, consent, persistence, result, error, logging, settings, or transport behavior.
- S3 completed on 2026-07-19 after all acceptance criteria and milestones passed. Track 020 moved to COMPLETED with synchronized status; no direct MCP mutation or non-test memory was created.

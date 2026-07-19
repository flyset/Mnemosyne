# TRACK 018 [COMPLETED]: Portable memory scope schemas

Track
- ID: TRACK_018
- Repository: Mnemosyne
- Branch: main
- Current path: `.backlog/COMPLETED/2026/TRACK_018_COMPLETED_portable_memory_scope_schemas.md`

Problems (PORE)
- P1: As a model using an MCP client that projects only top-level object properties, I cannot supply `memory_list` arguments, because its declared fields exist only inside top-level `oneOf` object branches and the client reduces the Tool to an empty parameter object.
- P2: As a model discovering `memory_recall`, I cannot reliably see the allowed scope vocabulary in clients with limited JSON Schema composition support, because scope is expressed only as `oneOf` constants without an explicit string enum.

Objective
- Publish portable, top-level list parameters and explicit shared scope enums while preserving the four strict list request variants and all runtime behavior.

Non-negotiables
- All implementation follows TDD: focused failing tests, the smallest passing implementation, then refactoring and validation.
- Keep handlers, registry, storage, selectors, results, mutation policy, and HTTP transport unchanged.
- Preserve the exact six scope values and list request semantics, including omission-sensitive collection selection and page-size/cursor exclusivity.
- Preserve schema-aware argument normalization behavior.

Acceptance criteria
- [x] A1) [P1] `memory_list.inputSchema` exposes `scope`, `namespace_id`, `collection_id`, `page_size`, and `cursor` in top-level `properties`, requires `scope`, and rejects additional properties.
- [x] A2) [P1] Conditional schema constraints retain exactly the four valid scope-wide/namespace and initial/continuation request variants.
- [x] A3) [P1, P2] List and recall publish `scope` as `type: string` with an explicit enum of all six canonical scopes.
- [x] A4) [P1, P2] Focused schema, normalization, registry, and route tests plus the full suite pass; raw MCP discovery exposes the portable schema and direct list dispatch still accepts `scope: project`.
- [x] A5) [P1, P2] README and architecture documentation describe the portable schema surface without changing request semantics.
- [x] A6) [P1] Model-facing Tool/property prose that survives composition flattening explains all four valid list request variants and each field's combination constraints.
- [x] A7) [P1] A regression test simulates a client retaining only top-level properties and required fields, proves valid list arguments survive that projection, and reaches the handler with `scope: project` intact.

Why now / impact
- Claude reported `memory_list` as `properties: {}` and could not get `scope` through its generated Tool boundary, while direct OpenCode calls worked. Raw MCP inspection showed a valid but composition-heavy server schema, identifying an interoperability gap rather than a scope-vocabulary mismatch.

Scope
- In scope:
  - `memory_list` Tool-schema layout.
  - Explicit enum scope schemas for list and recall.
  - Focused automated compatibility coverage.
  - Applicable README and architecture updates.
- Out of scope:
  - Handler or domain validation changes.
  - Result, pagination, cursor, selector, or storage changes.
  - Changes to inspection or mutation Tool schemas.
  - Client-specific adapters or workarounds outside the MCP schema.

Milestones
- [x] M1) TDD the portable list and recall schema declarations.
- [x] M2) Reconcile documentation and complete automated/direct validation.
- [x] M3) Close the flattened-client guidance and regression-test gap found after initial completion.

Risks / decisions
- Risk: Flattening properties could weaken advertised conditional semantics; retain four mutually exclusive conditional branches over the top-level property declarations.
- Risk: Schema layout changes can affect central argument normalization; keep property types unchanged and rerun its focused tests.
- Decision: Use top-level `type`, `properties`, `required`, and `additionalProperties`, with `oneOf` limited to presence/exclusion constraints rather than hiding parameter declarations inside branches.
- Decision: Use `type: string` plus `enum` for scope portability; preserve model guidance in a bounded property description derived from the canonical scope registry.
- Decision: Treat top-level composition as validation detail, not the sole model-facing explanation; flat property descriptions must carry combination semantics for clients that discard `oneOf` / `anyOf` / conditional keywords.
- Decision: Establish a standing MCP architecture rule that variant-based Tool schemas keep a flat top-level property bag and remain meaningfully callable from that reduced view.

Open questions
- [x] Q1) Does `memory_list` use a different scope vocabulary from recall?
- [x] Q2) Is the server omitting the schema?

Decision log
- Decision (Q1): No. Both Tools use the same six canonical scopes.
- Decision (Q2): No. Raw MCP `tools/list` exposes all fields within four top-level `oneOf` branches; the reported client appears to ignore those nested object properties.

Plan (execution steps)
- [x] S1) Move Track 018 to ACTIVE (folder, filename, and title status).
- [x] S2) TDD schema portability: first change focused list and recall expectations to require top-level properties and explicit scope enums, run them to observe failure, then minimally refactor both definitions and rerun focused schema/normalization tests.
- [x] S3) Update README and architecture documentation, run focused/full/repository validation, perform raw MCP discovery and direct dispatch checks, record evidence, and move Track 018 to COMPLETED.
- [x] S4) Correct the post-completion flattened-client gap: first add failing tests for durable four-variant prose and top-level-only argument projection reaching the handler, then minimally update Tool/property descriptions and the standing architecture rule, rerun focused/full/direct validation, and return Track 018 to COMPLETED.

Current inventory
- `memory_list.inputSchema` now exposes all five fields at top level, requires scope, rejects unknown fields, and uses four mutually exclusive presence/exclusion branches for the unchanged request variants.
- `memory_recall.inputSchema` now publishes its canonical scope vocabulary as an explicit string enum in its existing top-level property.
- `memory_list` handler and direct calls already accept the same literal scope values as recall.
- Central schema-aware normalization traverses top-level properties and `oneOf` / `anyOf`; top-level list declarations can preserve current page-size decoding and string/null selector behavior.
- `tests/mcp/test_memory_list.py`, `tests/mcp/test_memory_recall.py`, and `tests/memory/test_scopes.py` enforce top-level visibility, canonical enum derivation, model guidance, and the four list variants; existing handler tests continue to enforce exact runtime validation.
- `tests/mcp/test_memory_list.py` also projects only top-level properties/required fields, proves all four representative request shapes retain every argument, and dispatches the projected scope-wide request through the real handler adapter.
- `README.md` documents the compatibility layout and unchanged request semantics; `docs/ARCHITECTURE.md` now requires future variant-based Tools to remain callable and understandable through a flat top-level projection. No glossary terminology changed.
- Tracks 016 and 017 plus the list implementation remain uncommitted existing work and must be preserved.

Artifacts
- Pre-change raw MCP evidence (2026-07-19): `tools/list` returned `memory_list.inputSchema` with top-level `type: object` and four nested object branches containing scope and other fields; it did not return top-level properties. Direct connected list calls with `scope: project` succeeded.
- Activated on 2026-07-19 after the user approved the portable top-level list schema, explicit list/recall scope enums, focused tests, and documentation updates.
- S2 TDD evidence (2026-07-19): `PYTHONPATH=. pytest -q tests/mcp/test_memory_list.py tests/mcp/test_memory_recall.py` first failed the two changed schema tests because list had no top-level properties and recall still used scope `oneOf` constants; 61 existing tests passed.
- S2 focused validation (2026-07-19): after the minimal definition-only refactor, `PYTHONPATH=. pytest -q tests/mcp/test_memory_list.py tests/mcp/test_memory_recall.py tests/mcp/test_tool_arguments.py` passed with 79 tests, including unchanged list page-size and selector normalization behavior.
- S3 focused validation (2026-07-19): the initial 136-test schema/normalization/registry/route set passed. The first full run then found one legacy `tests/memory/test_scopes.py` expectation for recall's former `oneOf`; updating that canonical-derivation assertion to the approved enum contract produced 148 passing focused tests.
- S3 full/repository validation (2026-07-19): final `PYTHONPATH=. pytest -q` passed with 696 tests and `git diff --check` passed.
- S3 raw MCP discovery (2026-07-19): after the user restarted the server, `tools/list` exposed list's five top-level properties, required scope, additional-property refusal, four conditional variants, and explicit six-value string enum; recall exposed the same explicit scope enum in its top-level scope property.
- S3 direct dispatch/client validation (2026-07-19): raw `tools/call` with `{"scope":"project","page_size":1}` returned `status: ok`, one item, and coherent 16-record pagination metadata; `opencode mcp list` reported Mnemosyne connected with the revised schema.
- Post-completion client review (2026-07-19): Claude confirmed the corrected root cause but identified that a top-level-only projection also discards conditional constraints, leaving a flat field bag without enough prose to choose legal combinations. It also requested a regression test of the lossy projection rather than only structural schema assertions. The user approved reopening for this corrective chunk; A6, A7, and M3 remain open.
- User client validation (2026-07-19): before S4 implementation, the user confirmed Claude successfully discovered and called the corrected Tool after reconnecting, proving the core top-level schema fix resolved the reported failure.
- S4 TDD evidence (2026-07-19): `PYTHONPATH=. pytest -q tests/mcp/test_memory_list.py` first failed the new durable-prose assertion while the new top-level-only projection/dispatch regression and 31 existing tests passed. Minimal Tool/property descriptions then made the final focused file pass with 33 tests.
- S4 focused/full validation (2026-07-19): the final schema/recall/normalization/registry/route/scope set passed with 150 tests; `PYTHONPATH=. pytest -q` passed with 698 tests; `git diff --check` passed.
- S4 direct validation (2026-07-19): an isolated server at `127.0.0.1:8769` exposed all four variants in Tool/scope prose plus combination-specific descriptions for namespace, collection, page size, and cursor. Direct `tools/call` with `scope: project` and page size 1 returned `status: ok` with coherent 16-record pagination. The isolated server stopped normally and its temporary log was removed.

Completion notes
- Initial completion on 2026-07-19 published client-portable list parameters and explicit list/recall scope enums without changing handlers, selectors, pagination, results, storage, permissions, or transport.
- Reopened on 2026-07-19 for S4 after client review found that flattened discovery still lacked durable combination guidance and an explicit projection regression test.
- Re-completed on 2026-07-19 after adding durable flat-view prose, an explicit lossy-projection dispatch regression, the standing schema architecture rule, and focused/full/direct validation. Handler, domain, storage, result, permission, and transport behavior remain unchanged.

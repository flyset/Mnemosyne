# TRACK 016 [COMPLETED]: Complete memory discovery

Track
- ID: TRACK_016
- Repository: Mnemosyne
- Branch: main
- Current path: `.backlog/COMPLETED/2026/TRACK_016_COMPLETED_complete_memory_discovery.md`

Problems (PORE)
- P1: As a user asking what Mnemosyne knows within a memory scope, I receive a relevance-ranked sample rather than a complete inventory, because `memory_recall` requires matching query signals, excludes non-positive matches, and returns at most five records without total-count or truncation metadata.
- P2: As an MCP caller trying to inspect an existing memory, I cannot discover its exact reference unless recall happens to return it, because `memory_inspect` requires an already-known reference and there is no bounded enumeration primitive.
- P3: As a user governing archived memory, I cannot enumerate archived canonical records through MCP, because normal recall intentionally excludes them even though exact inspection supports them.

Objective
- Add a bounded, read-only memory discovery capability that completely and deterministically enumerates valid records in one selected scope or canonical container without relevance ranking or bulk content disclosure.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Keep the capability separate from `memory_recall`; search and complete inventory have different intent, ordering, result, and least-privilege contracts.
- Require exactly one allowlisted memory scope and never accept a filesystem path, root, filename, arbitrary traversal selector, or cross-scope request.
- Keep HTTP transport thin and put MCP semantics under `mnemosyne/mcp/`; shared listing, selection, ordering, and storage meaning belong under `mnemosyne/memory/`.
- Return compact user-visible inventory metadata and inspect-compatible references, not record content, paths, fingerprints, retrieval scores, or match evidence.
- Preserve filesystem records as the source of truth; do not add a required manifest, persistent index, hidden history, or background rewrite.
- Fail closed rather than returning an apparently complete partial inventory when the source is unsafe, unavailable, over its candidate bound, or changes incompatibly during pagination.
- Keep listing read-only: it must not create the memory root, rewrite records, or change lifecycle state.
- Preserve single-user, local-first, explicit-tool, and least-privilege boundaries.

Acceptance criteria
- [x] A1) [P1] A distinct read-only MCP Tool can list all valid compatible records in exactly one required scope without a query, relevance ranking, or five-result recall cap.
- [x] A2) [P1] The Tool can optionally narrow canonical records by namespace and collection using explicit, documented selector semantics; it never searches another scope or accepts a path.
- [x] A3) [P1] Results use one deterministic server-defined order and expose a page number, returned-item count, total matching count, total page count, whether more selected records remain, and a next cursor when they do.
- [x] A4) [P1] Traversing unchanged pages returns every selected valid record exactly once; a changed or selector-mismatched continuation fails with a bounded error rather than silently skipping or duplicating records.
- [x] A5) [P2] Every canonical and uniquely identified legacy item contains an exactly inspectable versioned reference and compact metadata sufficient for selection; duplicate legacy sources preserve their valid but ambiguous shared reference and are marked `inspectability: ambiguous`, while content and internal storage details remain absent.
- [x] A6) [P2] An empty valid container returns an explicit successful empty inventory, distinct from recall's relevance-based `no_matches` outcome.
- [x] A7) [P3] Canonical active and archived records are discoverable with visible lifecycle state; scope-wide legacy records remain discoverable without invented canonical metadata.
- [x] A8) [P1, P2, P3] Invalid arguments, malformed or stale cursors, candidate overflow, unavailable sources, and unexpected failures produce stable bounded protocol or Tool errors without partial results or sensitive details.
- [x] A9) [P1, P2, P3] Tool discovery, dispatch, schema-aware argument normalization, terminal content-free logging, client permission policy, and direct MCP behavior are covered by automated tests.
- [x] A10) [P1, P2, P3] `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` document the final public contract and its distinction from recall and inspection.
- [x] A11) [P1, P2, P3] Focused tests and the full automated suite pass, supplemented by direct MCP protocol checks that demonstrate complete traversal without source mutation or content/path leakage.

Why now / impact
- Retrieval is currently Mnemosyne's weakest capability: it works when the caller can name relevant concepts but cannot prove complete discovery for questions such as "what projects do I have?"
- A complete inventory primitive makes existing memory inspectable and governable without weakening recall's bounded relevance semantics.
- The current store already performs bounded deterministic scope discovery, so this capability can reuse the file-truth architecture without introducing a database or persistent index.

Scope
- In scope:
  - A distinct read-only Tool named `memory_list`.
  - One required scope plus optional canonical namespace and collection selectors.
  - Explicit collection selector semantics, including the distinction between all collections, collectionless records, and one exact collection.
  - Valid version-1 and version-2 record discovery with no invented legacy metadata.
  - Active and archived canonical record visibility.
  - Compact result projection with inspect-compatible references.
  - Deterministic ordering, bounded pages, complete counts, truncation state, and opaque continuation cursors.
  - Cursor validation against the selected container and an unchanged ordered record set.
  - Stable errors and content-free terminal logging.
  - Registry, dispatch, client permission, documentation, automated-test, and direct MCP coverage.
- Out of scope:
  - Changing `memory_recall`, its ranking, five-result cap, or match evidence.
  - Returning complete record content from listing.
  - Cross-scope enumeration or unrestricted filesystem access.
  - Arbitrary query, tag, sort, path, filename, timestamp, or provenance filters.
  - Mutation, lifecycle changes, migration, record repair, or automatic cleanup.
  - A persistent manifest, database, vector index, snapshot store, or background indexing process.
  - Resolving legacy duplicate identity by exposing a path or inventing canonical identity.
  - General awareness tooling beyond memory inventory.

Milestones
- [x] M1) Resolve the public Tool name, selector, eligibility, ordering, pagination, count, cursor, legacy-ambiguity, and client-permission contracts.
- [x] M2) Add shared-domain listing selection, deterministic ordering, and pagination behavior with focused tests.
- [x] M3) Add the MCP Tool definition and handler with strict validation, compact projections, bounded errors, and content-free logs.
- [x] M4) Register discovery and dispatch, update client permissions, and prove end-to-end protocol behavior.
- [x] M5) Update durable documentation and complete focused, full-suite, and direct MCP validation.

Risks / decisions
- Decision: Use a distinct Tool rather than an empty-query or mode branch of `memory_recall`; this preserves stable recall semantics and an independent least-privilege permission boundary.
- Decision: Require exactly one high-level scope; cross-scope listing is outside the initial contract.
- Decision: Keep listing compact and compose it with `memory_inspect` for complete record retrieval.
- Decision: Define completeness over valid, compatible records in the selected bounded source; invalid or unsafe JSON candidates are not represented as memories, while candidate overflow fails the call rather than truncating silently.
- Decision: Include archived canonical records so the Tool closes the current governance and rediscovery gap.
- Decision: Register the read-only Tool unconditionally at startup between `memory_recall` and `memory_inspect`; it has no operator enablement setting, while bundled clients require approval because complete inventory metadata is broader than relevance-selected recall.
- Decision: Promise complete traversal only while the selected valid-record snapshot remains unchanged between bounded rescans; the filesystem is not an atomic multi-page snapshot and no persistent snapshot store will be introduced.
- Decision: Cursors are process-instance-bound and become stale after server restart. They contain no path, content, fingerprint, secret, or reversible storage identity.
- Decision: Empty selection is a successful page with page number 1, returned count 0, total count 0, total pages 0, `truncated: false`, and no next cursor.
- Risk: Files may change between pages, causing offset-only pagination to skip or duplicate records; continuation must detect an incompatible changed selection and require a fresh traversal.
- Risk: Snapshot verification may require a bounded rescan for every page because there is intentionally no persistent index.
- Risk: Duplicate legacy IDs can produce multiple entries with the same public legacy reference while exact inspection remains ambiguous.
- Risk: Scope-wide discovery may make a narrow canonical selector fail because unrelated candidates consume the existing scope bound; selector-aware store discovery may be needed without weakening path safety.
- Risk: Titles and tags can make even compact pages large; the page-size bound must reflect existing field limits.
- Risk: Broad inventory access reveals more metadata than query-selected recall, so bundled client permissions must make that capability explicit.

Open questions
- [x] Q1) Is the final Tool name `memory_list`, `memory_enumerate`, or another canonical term?
- [x] Q2) What exact request shape represents namespace-wide, all-collections, collectionless, and exact-collection selection without ambiguity?
- [x] Q3) What fixed ordering key supports canonical and legacy records without exposing internal paths?
- [x] Q4) What opaque cursor format binds continuation to its selector and ordered record snapshot without carrying reversible paths, content, or secrets?
- [x] Q5) Which source changes make a cursor stale, and what stable status/code should report that condition?
- [x] Q6) Should scope-wide listing return duplicate legacy references as separate ambiguous entries, mark them as ambiguous, or adopt another bounded representation?
- [x] Q7) Should namespace and collection selection narrow filesystem discovery before applying the candidate bound, and how are legacy records handled in that path?
- [x] Q8) What compact fields beyond the reference are necessary for selection: title, tags, kind, and lifecycle, or a smaller set?
- [x] Q9) What default and maximum page sizes keep responses bounded while avoiding excessive repeated scans?
- [x] Q10) Should bundled OpenCode policy initially `allow` this read-only Tool or require `ask` because it exposes a complete bounded inventory?

Decision log
- Decision (initial): The preferred direction is a separate, scope-required, compact listing Tool with optional canonical-container narrowing, deterministic pagination, explicit completeness metadata, and list-then-inspect composition.
- Decision (Q1): Name the Tool `memory_list` to distinguish complete discovery from relevance-ranked `memory_recall` and exact `memory_inspect` while matching the existing verb-oriented Tool names.
- Decision (Q2): The request always requires `scope`. Omitting `namespace_id` selects every valid compatible record in that scope and requires `collection_id` to be absent. Supplying `namespace_id` selects canonical records in that namespace and excludes legacy records; an absent `collection_id` selects collectionless records and all collections, explicit `collection_id: null` selects only collectionless records, and a string selects one exact collection. Continuations repeat the same selector and add `cursor`.
- Decision (Q3): Sort ascending by schema version and then public identity: legacy by record ID; canonical by namespace ID, collection-presence marker, collection ID, and record ID. Use normalized scope-relative path only as an unexposed final tie-breaker for duplicate legacy IDs.
- Decision (Q4): Use a bounded, versioned, URL-safe opaque cursor containing a process-instance identifier, selector digest, selected-snapshot digest, next offset, and fixed page size, authenticated with an in-memory process key. It contains no path, content, record fingerprint, secret source value, or reversible storage identity and is never persisted.
- Decision (Q5): Return `status: invalid_request`, code `invalid_cursor` for malformed, tampered, selector-mismatched, or request-incompatible cursors. Return `status: conflict`, code `stale_cursor` when the process instance or selected valid-record snapshot changed. Addition, removal, relocation, byte change, lifecycle change, or valid/invalid transition in the selected container invalidates continuation; changes outside a selector-aware container do not.
- Decision (Q6): Return every valid legacy source so counts remain source-record counts and traversal remains complete. Mark duplicate legacy entries `inspectability: ambiguous`; mark unique legacy and canonical entries `inspectability: exact`. Exact inspection retains its existing `ambiguous_reference` behavior.
- Decision (Q7): Narrow canonical namespace and collection discovery to the deterministic safe container before applying the 1,000-candidate bound. Scope-wide discovery retains the full-scope bound and includes legacy records. Canonical selectors exclude legacy records and must not fail because of candidates outside the selected container.
- Decision (Q8): Each item contains a versioned reference, nullable title, and inspectability. Canonical items additionally contain kind and lifecycle state. Omit content, tags, labels, language, provenance, timestamps, lifecycle revision, paths, fingerprints, retrieval scores, and match evidence.
- Decision (Q9): Initial requests accept optional `page_size` from 1 through 100, defaulting to 50. Continuations use the cursor-bound size and reject `page_size`. Successful results use `status: ok`, a `memories` array, and a `page` object containing `number`, `count`, `total_count`, `total_pages`, `truncated`, and nullable `next_cursor`; `truncated` means more selected records remain, never that the source was partially scanned.
- Decision (Q10): Bundled OpenCode policy requires `ask` for `mnemosyne_memory_list` at both policy levels. The exact rule follows broad denial and precedes mutation approval rules. Server registration remains unconditional and independent of mutation gates.
- Decision (result/log contract): Registry order begins `list_tools`, `memory_recall`, `memory_list`, `memory_inspect`, followed by conditionally enabled mutation Tools in their existing relative order. The handler emits one terminal content-free event containing only outcome, bounded code/field where applicable, scope, selector-presence booleans, returned count, total count, page number, and truncation state; it omits IDs, selector values, titles, content, paths, cursors, fingerprints, and exception details.
- Decision (cursor authentication qualification): Cursor structure is validated before process binding. A structurally valid cursor carrying a foreign process marker returns `stale_cursor` before HMAC verification because the current process cannot authenticate an intentionally non-persisted prior-process key; malformed cursors and current-process authentication failures return `invalid_cursor`. Consequently, tampering only the process marker is conservatively classified as stale, but no unauthenticated cursor is ever accepted.
- Decision (snapshot boundary): Cursor snapshots cover every ordered selected valid record using keyed digests over schema/public identity plus internal relative path and raw-file fingerprint. Selected additions, removals, relocations, byte rewrites, lifecycle changes, and valid/invalid transitions stale continuation. Changes that remain invalid or occur outside the selector-aware discovery container do not.
- Decision (cursor lifetime): Cursors are reusable stateless continuations within one process and selected snapshot; they are not one-time tokens. The process-shared codec supports separately constructed services in the current single-process local server, while multi-worker cursor affinity remains outside the v0 deployment model.
- Decision (MCP request branches): The `memory_list` schema uses four mutually exclusive strict object branches for scope-wide initial, namespace initial, scope-wide continuation, and namespace continuation requests. Initial requests may include `page_size`; continuations repeat the selector and include `cursor` but reject any `page_size` key, including null.
- Decision (MCP omission semantics): An omitted `collection_id` under a namespace means collectionless plus all collections, native JSON null means collectionless only, and a string means one exact collection. Because collection IDs legitimately permit strings, the string `"null"` remains the exact collection ID `null`; collectionless selection requires native null.
- Decision (MCP compact lifecycle): Canonical list items expose `lifecycle: {"state": <active|archived>}` and omit revision. Legacy items expose no invented kind or lifecycle metadata.
- Decision (MCP structural errors): Public `tools/call.params.arguments`, when present, must be an object; a non-object is rejected before Tool dispatch as JSON-RPC `-32602 Invalid params` with the request ID preserved. At the direct handler boundary, a non-object request or an object with unknown top-level fields returns `status: invalid_request`, code `invalid_request`, field `request`. Scope, namespace, collection, page-size, and cursor validation use their dedicated stable codes and fields.

Plan (execution steps)
- [x] S1) Move Track 016 to ACTIVE (folder, filename, and title status) after resolving the blocking public-contract questions.
- [x] S2) TDD shared-domain selector and eligibility semantics: first add focused failing tests for scope isolation, canonical namespace/collection selection, legacy inclusion, and active/archived visibility; then implement the smallest listing model/service behavior and validate.
- [x] S3) TDD selector-aware storage discovery, deterministic ordering, and pagination: first add focused failing tests for safe narrowed roots, missing containers, symlinks, unrelated scope/container overflow, legacy exclusion under canonical selectors, complete unchanged traversal, counts, page boundaries, selector-bound and process-bound cursors, stale continuation, invalid records, selected-container candidate overflow, and duplicate legacy IDs; then implement minimally and validate.
- [x] S4) TDD the `memory_list` MCP package: first add focused failing schema, validation, projection, error, logging, no-initialization, and argument-normalization tests; then implement the three-file Tool package and validate.
- [x] S5) TDD registry, dispatch, and client permission integration: first add focused failing discovery, real-handler, route, and policy-order tests; then register the Tool and update the explicit client rule minimally.
- [x] S6) Update `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` for the final public contract and architecture.
- [x] S7) Run focused tests, the full automated suite, and direct MCP checks for empty, canonical, legacy, archived, multi-page, stale-cursor, overflow, logging, and no-mutation behavior; record exact evidence.
- [x] S7a) Correct public non-object Tool-argument handling found during completion review: first add failing method/route tests, then reject non-object `tools/call.params.arguments` as JSON-RPC invalid params, update durable protocol terminology, rerun focused/full/direct validation, and restore affected acceptance evidence.
- [x] S9) Correct OpenCode Tool-schema compatibility found after completion: first add a failing schema test requiring top-level object type, add the minimal declaration, run focused/full validation, prove `opencode mcp list` succeeds, and restore affected acceptance evidence.
- [x] S8) Confirm all acceptance criteria, capture completion notes, and move Track 016 to COMPLETED (folder, filename, title, and this step).

Current inventory
- `mnemosyne/memory/listing.py`: owns immutable scope/namespace/collection selectors, eligibility, the schema/public-identity ordering key, whole-snapshot legacy ambiguity marking, page/result models, 1–100 page-size policy with default 50, keyed selector/snapshot digests, and strict bounded HMAC cursor encoding/decoding. Its store import is type-checking-only to preserve runtime dependency direction.
- `mnemosyne/memory/service.py`: `MemoryService.list_memories()` validates initial or continuation inputs before discovery, uses selector-aware storage, orders and fingerprints the complete selected valid snapshot, verifies continuation staleness before slicing, and returns coherent page metadata. A module-process codec is shared across service instances; `recall()` and `inspect()` remain unchanged.
- `mnemosyne/memory/store.py`: `discover_for_list()` validates the selected root without creating it, rejects selected symlink/non-directory sources, narrows scope/namespace/collection discovery before candidate counting, scans only canonical path levels for collectionless/exact selectors, and applies eligibility defense-in-depth. Existing `discover()` behavior remains unchanged for recall and duplicate discovery.
- `mnemosyne/memory/paths.py`: validates and projects deterministic namespace and collection directories from fixed scope names and normalized IDs.
- `mnemosyne/memory/errors.py`: defines domain `invalid_cursor` and `stale_cursor` conditions for later bounded MCP adaptation.
- `mnemosyne/memory/__init__.py`: exports stable selector, inspectability, page/result, and page-size contracts without exporting the process cursor codec or key.
- `mnemosyne/mcp/tools/memory_list/definition.py`: defines four strict omission-sensitive initial/continuation schema branches derived from shared scopes, identifier rules, and listing bounds; it accepts no path, query, tags, sort, filter, content, or mutation field.
- `mnemosyne/mcp/tools/memory_list/handler.py`: independently validates the advisory schema before root resolution, adapts omission-sensitive selectors to the shared domain, invokes read-only listing without an enablement gate, projects compact inspect-compatible legacy/canonical items and page metadata, maps bounded errors, and emits one content-free terminal event.
- `mnemosyne/mcp/tools/memory_list/__init__.py`: re-exports only the Tool definition and handler.
- `mnemosyne/memory/retrieval.py`: excludes archived canonical records, requires positive relevance, orders by score, and returns at most five matches.
- `mnemosyne/memory/records.py`: owns versioned records and inspect-compatible references; legacy identity lacks namespace, collection, lifecycle, and other canonical dimensions.
- `mnemosyne/mcp/tools/memory_recall/`: owns query-ranked retrieval schema, validation, projection, errors, and logs; its contract has no list mode or completeness metadata.
- `mnemosyne/mcp/tools/memory_inspect/`: retrieves one exact active or archived canonical record or one exact legacy record, but cannot discover unknown references.
- `mnemosyne/mcp/tools/registry.py`: couples the `memory_list` definition and real handler, registers it unconditionally between recall and inspection, derives its normalization schema from the selected Tool, and preserves independent mutation gates and ordering.
- `opencode.json`: requires exact `ask` approval for `mnemosyne_memory_list` at top level and after the agent's broad denial/read-only allows but before mutation approvals; the remote MCP declaration is unchanged.
- `.opencode/agents/mnemosyne.md`: mirrors the broad-deny, explicit read-only allow, exact list `ask`, and mutation `ask` ordering so the file agent cannot weaken complete-inventory approval.
- `tests/memory/test_store.py`: covers existing discovery plus narrowed namespace, exact-collection, and collectionless roots; unrelated and selected-container candidate bounds; missing-root non-initialization; selected symlink/non-directory refusal; invalid-record skipping; and canonical-selector legacy exclusion.
- `tests/memory/test_listing.py`: covers scope/container eligibility, mixed schema ordering, private legacy tie-breaking, whole-snapshot ambiguity, empty/default/maximum/exact-boundary pages, complete multi-service traversal, no five-item cap, invalid page sizes and cursors, selector/process binding, current-process tamper refusal, selected-snapshot staleness, unrelated-scope stability, and absence of writes.
- `tests/memory/test_import_boundaries.py`: verifies listing has no top-level runtime store import, enforces the three-file `memory_list` package, and preserves shared-domain/MCP/HTTP dependency direction.
- `tests/mcp/test_memory_list.py`: covers the four schema branches, package exports, all selector modes, initial/continuation adaptation, strict invalid requests, compact legacy/canonical projection, bounded domain and unexpected errors, terminal content-free logs, validation-before-root behavior, missing-root non-initialization, and source preservation.
- `tests/mcp/test_tool_arguments.py`: covers one-layer `memory_list` page-size decoding, native-null collection preservation, string-`"null"` exact-collection preservation, cursor text preservation, caller-argument immutability, and normalized-handler compatibility.
- `tests/mcp/test_registry.py`: covers paired list registration, fail-closed partial wiring, immutable order, centralized normalization, global real-handler dispatch, no-initialization behavior, and all mutation-setting combinations.
- `tests/mcp/test_startup_settings.py`: proves list discovery and dispatch remain always available and read-only across file/environment mutation settings and startup-fixed registry selection.
- `tests/routes/test_mcp.py`: proves HTTP `tools/list` ordering and real `tools/call` compact listing through the unchanged thin route.
- `tests/test_opencode_config.py`: enforces exact ordered list approval in project, inline agent, and file-agent policy.
- `tests/memory/test_retrieval.py`: continues to cover relevance ranking and the independent five-result recall limit.
- `tests/mcp/test_memory_recall.py`, `tests/mcp/test_memory_inspect.py`, `tests/mcp/test_registry.py`, `tests/mcp/test_list_tools.py`, `tests/routes/test_mcp.py`, and `tests/test_opencode_config.py`: are the primary public-contract and integration test surfaces likely affected.
- `README.md`: documents the registered Tool, recall/list/inspect composition, omission-sensitive selectors, page and cursor contracts, compact projections, ordering/ambiguity, errors, read-only behavior, filesystem bounds, schema-aware normalization, and exact OpenCode approval policy.
- `docs/ARCHITECTURE.md`: documents `memory/listing.py`, the three-file MCP package, shared-domain/store/handler ownership, keyed cursor and pagination architecture, fixed registry order, and selector-aware filesystem discovery.
- `docs/GLOSSARY.md`: defines canonical listing, selector, request, item, inspectability, page, cursor, empty-inventory, and cursor/error terminology and updates shared scope/domain language.

Artifacts
- User-approved project memory: `Idea: add a list/enumerate primitive for blind discovery`, recorded 2026-07-19 under the Mnemosyne `ideas` collection.
- S2 TDD evidence (2026-07-19): `PYTHONPATH=. pytest -q tests/memory/test_listing.py` first failed during collection because `mnemosyne.memory.listing` did not exist; after the minimal implementation it passed with 5 tests.
- S2 validation (2026-07-19): `PYTHONPATH=. pytest -q tests/memory/test_listing.py tests/memory/test_import_boundaries.py tests/memory/test_service.py tests/memory/test_retrieval.py` passed with 68 tests.
- Environment note (2026-07-19): the initial bare `pytest -q tests/memory/test_listing.py` could not import the local `mnemosyne` package in this shell, so repository-local validation used explicit `PYTHONPATH=.` without installing dependencies or changing the environment.
- S3 TDD evidence (2026-07-19): `PYTHONPATH=. pytest -q tests/memory/test_store.py tests/memory/test_listing.py tests/memory/test_import_boundaries.py` first failed during collection because `InvalidMemoryListCursor` and the remaining S3 contracts did not exist; after minimal implementation and refactoring, the focused set passed with 62 tests.
- S3 validation (2026-07-19): `PYTHONPATH=. pytest -q tests/memory/test_listing.py tests/memory/test_store.py tests/memory/test_service.py tests/memory/test_import_boundaries.py tests/memory/test_retrieval.py tests/mcp/test_memory_recall.py tests/mcp/test_memory_inspect.py` passed with 175 tests; chained `git diff --check` also passed.
- S4 TDD evidence (2026-07-19): `PYTHONPATH=. pytest -q tests/mcp/test_memory_list.py tests/mcp/test_tool_arguments.py tests/memory/test_import_boundaries.py` first failed during collection because `mnemosyne.mcp.tools.memory_list` did not exist; after the minimal three-file implementation, the focused set passed with 63 tests.
- S4 validation (2026-07-19): `PYTHONPATH=. pytest -q tests/mcp/test_memory_list.py tests/mcp/test_tool_arguments.py tests/memory/test_listing.py tests/memory/test_store.py tests/memory/test_import_boundaries.py tests/mcp/test_memory_recall.py tests/mcp/test_memory_inspect.py` passed with 174 tests; chained `git diff --check` also passed.
- S5 TDD evidence (2026-07-19): `PYTHONPATH=. pytest -q tests/mcp/test_registry.py tests/routes/test_mcp.py tests/test_opencode_config.py` first produced 8 focused failures because listing was not registered and its exact client approval rules were absent; after minimal integration those surfaces passed, and startup integration passed with 80 tests across the focused files.
- S5 validation (2026-07-19): `PYTHONPATH=. pytest -q tests/mcp/test_registry.py tests/mcp/test_list_tools.py tests/mcp/test_tool_arguments.py tests/mcp/test_memory_list.py tests/mcp/test_methods.py tests/mcp/test_startup_settings.py tests/routes/test_mcp.py tests/test_opencode_config.py` passed with 130 tests; chained `git diff --check` also passed.
- S6 validation (2026-07-19): reviewed `memory_list` coverage across `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md`; `PYTHONPATH=. pytest -q tests/mcp/test_memory_list.py tests/mcp/test_registry.py tests/test_opencode_config.py` passed with 74 tests, and `git diff --check` passed.
- S7 focused validation (2026-07-19): `PYTHONPATH=. pytest -q tests/memory/test_listing.py tests/memory/test_store.py tests/memory/test_import_boundaries.py tests/mcp/test_memory_list.py tests/mcp/test_tool_arguments.py tests/mcp/test_registry.py tests/mcp/test_startup_settings.py tests/routes/test_mcp.py tests/test_opencode_config.py` passed with 191 tests.
- S7 full-suite validation (2026-07-19): `PYTHONPATH=. pytest -q` passed with 694 tests.
- S7 direct discovery (2026-07-19): the available connected `mnemosyne_list_tools` call and isolated HTTP `tools/list` request both exposed `memory_list` between `memory_recall` and `memory_inspect`; the isolated registry contained all nine currently enabled Tools.
- S7 direct inventory (2026-07-19): an isolated server at `127.0.0.1:8765` used only `/var/folders/40/fp1hb78x6td05pslff7dn5pc0000gn/T/opencode/track016-direct/root`. `knowledge` returned the explicit zero-count empty page; scope-wide `preference` returned one compact legacy item with no content; exact `project`/`mnemosyne`/`decisions` traversal with page size 1 returned active then archived canonical items exactly once across two pages with coherent counts and no content, path, fingerprint, or revision.
- S7 direct errors (2026-07-19): adding one valid record to the selected temporary collection made the previously returned continuation produce `status: conflict`, code `stale_cursor`; 1,001 temporary JSON candidates under `knowledge` produced `status: storage_error`, code `candidate_limit_exceeded`, with no partial page.
- S7 direct logging/no-mutation (2026-07-19): isolated `mcp.memory_list` terminal events contained only outcome, stable code where applicable, scope, selector-presence booleans, counts, page number, and truncation. SHA-256 values for the original legacy, active canonical, and archived canonical fixtures were identical before and after all read-only calls. The isolated server stopped normally and the complete temporary validation directory was removed.
- S7 repository checks (2026-07-19): `git diff --check` passed; final status contained only the intended Track 016 repository changes and no temporary validation artifacts.
- S8 completion review blocker (2026-07-19): final read-only review found that `handle_tools_call()` coerced non-object `params.arguments` to `{}` before dispatch. Public `memory_list` therefore returned `invalid_scope` for `arguments: []` instead of rejecting the malformed Tool call at the MCP parameter boundary. A8, A9, A11, and M5 were reopened pending corrective S7a TDD and revalidation; no completion transition occurred.
- S7a TDD evidence (2026-07-19): `PYTHONPATH=. pytest -q tests/mcp/test_methods.py tests/routes/test_mcp.py` first produced 2 focused failures because `arguments: []` was coerced and dispatched; `handle_tools_call()` now returns JSON-RPC `-32602 Invalid params` before Tool selection/dispatch, preserving the request ID.
- S7a focused validation (2026-07-19): `PYTHONPATH=. pytest -q tests/mcp/test_methods.py tests/routes/test_mcp.py tests/mcp/test_memory_list.py` passed with 50 tests.
- S7a full-suite validation (2026-07-19): `PYTHONPATH=. pytest -q` passed with 696 tests.
- S7a direct protocol validation (2026-07-19): a direct HTTP `tools/call` to the connected server with `name: memory_list` and `arguments: []` returned `{"jsonrpc":"2.0","id":"non-object-arguments","error":{"code":-32602,"message":"Invalid params"}}` with no Tool result; the method/route tests verify rejection occurs before handler dispatch.
- S7a documentation/review validation (2026-07-19): README and glossary distinguish pre-dispatch non-object argument rejection from object-shaped Tool validation; final follow-up review confirmed the implementation blocker was resolved. `git diff --check` passed and status contained only intended Track 016 repository changes.

Completion notes
- Activated on 2026-07-19 after resolving the public Tool, selector, ordering, pagination, cursor, legacy ambiguity, bounded discovery, projection, page-size, registration, logging, and client-permission contracts.
- S2 completed on 2026-07-19: added shared selector and eligibility semantics plus a read-only service entrypoint without changing recall, storage discovery, MCP registration, or public Tool behavior.
- S3 completed on 2026-07-19: added strict selector-aware discovery, deterministic mixed-schema ordering, duplicate-legacy inspectability, complete bounded page metadata, and process/selector/snapshot-bound cursor continuation without changing MCP discovery or dispatch.
- S4 completed on 2026-07-19: added the strict three-file `memory_list` MCP package with compact projections, bounded errors, content-free logging, argument-normalization compatibility, and no-initialization behavior.
- S5 completed on 2026-07-19: registered list discovery and dispatch unconditionally in the fixed startup registry, proved real HTTP Tool behavior and centralized normalization, and added exact bundled-client approval ordering without changing mutation enablement or HTTP routes.
- S6 completed on 2026-07-19: documented the complete public request/result/error/cursor contract, architecture and filesystem ownership, canonical terminology, recall/list/inspect distinctions, and bundled-client approval boundary.
- S7 completed on 2026-07-19: focused and full automated validation passed, isolated direct protocol checks proved discovery, empty/legacy/canonical/archived/multi-page behavior, stale and overflow errors, bounded logs, unchanged source fixtures, and temporary cleanup. Final completion review subsequently found the non-object public Tool-argument blocker recorded above.
- S7a completed on 2026-07-19: public non-object Tool arguments now fail at the MCP parameter boundary, focused/full/direct validation passed, durable terminology was reconciled, and reopened acceptance evidence was restored.
- S8 completed on 2026-07-19: final review confirmed all eleven acceptance criteria, five milestones, public-contract documentation, least-privilege client policy, focused/full/direct validation, and the corrective public argument boundary. Track 016 moved to `COMPLETED`; Mnemosyne now exposes bounded complete memory discovery through the read-only `memory_list` Tool without changing recall semantics, filesystem source-of-truth ownership, or mutation gates.
- Post-completion compatibility failure (2026-07-19): the server remained healthy and direct JSON-RPC `tools/list` returned all nine Tools, but OpenCode 1.17.11 reported `memory_list` MCP discovery as `failed` with `Failed to get tools`. Inspection showed `memory_list.inputSchema` had object-typed `oneOf` branches but no top-level `type: object`, unlike every previously accepted Mnemosyne Tool schema. Track 016 was reopened to ACTIVE for S9 corrective TDD; A9, A11, M4, M5, and S8 were reopened pending real-client validation.
- S9 TDD evidence (2026-07-19): `PYTHONPATH=. pytest -q tests/mcp/test_memory_list.py` first produced 1 focused failure with 30 passing tests because the new compatibility assertion found no top-level schema type. `memory_list.inputSchema` now declares `type: object` while retaining the four strict `oneOf` branches.
- S9 focused validation (2026-07-19): `PYTHONPATH=. pytest -q tests/mcp/test_memory_list.py tests/mcp/test_tool_arguments.py tests/mcp/test_registry.py tests/routes/test_mcp.py tests/test_opencode_config.py` passed with 106 tests.
- S9 real-client validation (2026-07-19): `opencode mcp list` on OpenCode 1.17.11 changed from `mnemosyne failed — Failed to get tools` to `mnemosyne connected` at `http://127.0.0.1:8000/mcp` after the schema correction.
- S9 full-suite/repository validation (2026-07-19): `PYTHONPATH=. pytest -q` passed with 696 tests and `git diff --check` passed.
- S9 completed on 2026-07-19: OpenCode now accepts Tool discovery, the server contract and normalization behavior remain unchanged, and A9, A11, M4, and M5 were restored.
- S8 re-completed on 2026-07-19 after S9: final review confirmed all acceptance criteria and milestones, 696 passing tests, direct protocol behavior, and successful OpenCode 1.17.11 MCP discovery. Track 016 returned to `COMPLETED` with the real-client schema compatibility issue resolved.

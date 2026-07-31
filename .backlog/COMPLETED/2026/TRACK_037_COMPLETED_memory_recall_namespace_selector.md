# TRACK 037 [COMPLETED]: memory_recall namespace selector

Track
- ID: TRACK_037
- Repository: MyMCP
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_037_COMPLETED_memory_recall_namespace_selector.md

Problems (PORE)
- P1: As a caller of memory_recall, I cannot narrow ranked recall to one exact
  namespace within a scope, because memory_recall accepts only scope/query/tags
  while memory_list already accepts namespace_id; I must either accept scope-wide
  ranked results that mix unrelated namespaces or fall back to memory_list plus
  memory_inspect, which bypasses retrieval ranking and inflates call count.
- P2: As a maintainer, I need namespace-selected recall to reuse Mnemosyne's
  canonical identifier validation and filesystem boundaries, because a second
  selector contract would create avoidable differences in accepted identifiers,
  path safety, and missing-container behavior.

Objective
- Add an optional namespace_id selector to memory_recall that, when supplied and
  valid, restricts ranked candidate discovery to that exact namespace within the
  selected scope, preserves current scope-wide recall when omitted, and returns a
  successful empty result for an unknown namespace, while preserving all existing
  accepted requests, required fields, and result shapes.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing
  implementation, then refactoring and validation.
- scope and query remain required; the published memory_recall result shapes,
  error payloads, retrieval cap (5 results), and no-path/no-score guarantees are
  unchanged.
- Omitting namespace_id must preserve the exact current scope-wide recall
  behavior and three-argument recall-operation invocation; the handler passes a
  fourth argument only when the selector is present.
- Reuse the anchored identifier contract: normalize_identifier with
  IDENTIFIER_PATTERN fullmatch and the anchored ^...$ schema pattern (TRACK_036
  Ollama compatibility); never introduce an unanchored pattern.
- Unknown but valid namespace_id returns a successful no_matches result; an
  invalid namespace_id (non-string, including explicit JSON null, "", path
  traversal, uppercase, over-length) returns invalid_request with code
  invalid_namespace. The public schema rejects non-strings through its type; the
  handler independently rejects them through normalize_identifier.
- The change is confined to mymcp/plugins/mnemosyne/ (definition, handler, seam,
  plugin wiring, MemoryService, store discovery) plus its tests and public
  documentation; no host-owned file changes.
- Namespace presence may be logged; the namespace value must not be logged.
- Automated tests are required; direct MCP protocol checks supplement and do not
  replace them.

Acceptance criteria
- [x] A1) [P1] memory_recall(scope, query, namespace_id=<valid>) returns only
  active records of that exact namespace within the selected scope, ranked by the
  existing ranker.
- [x] A2) [P1] memory_recall with a valid but unknown namespace_id returns status
  no_matches with memories [] (successful, non-error result).
- [x] A3) Omitting namespace_id returns exactly the current scope-wide ranked
  results.
- [x] A4) Invalid namespace_id values are rejected with status invalid_request,
  code invalid_namespace.
- [x] A5) A selected namespace path that is a symlink is skipped safely and a
  selected namespace path that exists but is not a directory returns the existing
  memory_source_unavailable error; neither case escapes the configured root.
- [x] A6) The advertised memory_recall inputSchema publishes namespace_id with the
  anchored pattern and keeps required == ["query", "scope"]; the exact TOOL
  equality test is updated.
- [x] A7) Every existing three-argument recall seam call site and test fake
  continues to work when namespace_id is omitted; selector-present calls forward
  the exact normalized namespace as a fourth argument.
- [x] A8) The complete automated suite passes and a direct configured-client
  recall check confirms the narrowed selector end to end.

Why now / impact
- memory_list already publishes the canonical namespace selector; memory_recall is
  the only read-only Tool without it, forcing callers to either pollute ranking
  with unrelated namespaces or bypass ranking via list+inspect. The change is
  small, additive, and reuses proven store/path helpers and the memory_list
  validation precedent.

Scope
- In scope:
  - memory_recall inputSchema gains an optional namespace_id property reusing
    memory_list's IDENTIFIER_SCHEMA/NAMESPACE_SCHEMA contract.
  - memory_recall handler validates namespace_id and forwards it through the
    recall seam.
  - RecallOperation seam, plugin _recall wiring, and MemoryService.recall accept
    the optional selector.
  - FilesystemMemoryStore.discover gains a trailing namespace_id=None parameter
    and narrows its discovery root to namespace_directory only when the selector
    is present; discover(scope) retains its current meaning and behavior.
  - Focused tests for schema, handler, seam, domain, and store behavior,
    including the exact TOOL equality update.
  - Public documentation updates (README.md, docs/ARCHITECTURE.md,
    docs/GLOSSARY.md, docs/MANUAL.md, docs/GETTING_STARTED.md) and a
    version/public-contract decision before activation.
- Out of scope:
  - collection_id selection on memory_recall (deferred; not needed to solve the
    stated problem).
  - Changes to rank_memories scoring, MAX_RESULTS, pagination, or cursor
    behavior.
  - Legacy version-1 records under a namespace selection (they have no canonical
    namespace identity; discovery-root narrowing therefore excludes them,
    matching memory_list).
  - Changes to any other memory_* Tool, the host, routes, bootstrap, registry,
    argument normalization, or opencode.json permissions.
  - Automatic migration or rewriting of existing stored data.

Milestones
- [x] M1) Domain: MemoryService.recall and store discovery narrow ranked
  candidates to one namespace.
- [x] M2) MCP: memory_recall schema, handler validation, seam, and plugin wiring
  support the optional selector.
- [x] M3) Validation: focused, integration, and complete suites pass; direct MCP
  check confirms narrowing and empty-unknown behavior.
- [x] M4) Documentation and version decision: public recall contract documented
  and the version marker decision recorded.

Risks / decisions
- Risk: Extending the recall seam signature can break 3-argument fakes in tests
  (test_memory_recall.py _recall_operation and the adapt test, plus bound
  read_service.recall in archive/restore/forget tests). Mitigation: the handler
  preserves the exact three-argument operation call when namespace_id is omitted
  and passes a fourth positional argument only when it is present;
  MemoryService.recall and _recall accept a trailing namespace_id=None.
- Risk: The exact TOOL equality test pins the current schema. Mitigation: update
  it in the schema/handler chunk and add a recursive anchored-pattern check
  (TRACK_036 precedent).
- Risk: An unanchored pattern regression would break Ollama/llama.cpp constrained
  decoding. Mitigation: reuse the anchored ^IDENTIFIER_PATTERN$ form already
  proven in memory_list.
- Decision: Unknown namespace -> successful no_matches. namespace_directory is
  deterministic and FilesystemMemoryStore.discover already returns [] for a
  missing scope directory (store.py lines 316-317); a missing namespace directory
  behaves identically.
- Decision: Invalid namespace_id, including explicit JSON null, ->
  invalid_request with code invalid_namespace, mirroring memory_list's handling.
  JSON Schema rejects null through type=string, not through pattern; direct
  handler invocation rejects it through normalize_identifier.
- Decision: Narrow at the store discovery boundary via namespace_directory so
  rank_memories and serialization are untouched; legacy v1 files never enter a
  namespace-rooted discovery.
- Decision: Do not add collection_id to memory_recall in this Track; collection
  selection remains a memory_list concern.
- Decision: Log only namespace_selector_present, not the namespace value,
  matching memory_list's logging contract.

Open questions
- [x] Q1) Seam parameter style: preserve the three-argument operation call when
  namespace_id is omitted; call with a fourth positional argument only when it is
  present; MemoryService.recall's trailing parameter is positional-or-keyword
  with default None.
- [x] Q2) Keep the SERVER_VERSION/`0.2.1` marker. This is an additive optional
  schema property, and advancing the marker would require host-owned version
  changes outside this Track's scope (TRACK_036 A5 precedent).
- [x] Q3) Validate query, then scope, then namespace_id, then tags, mirroring
  memory_list's scope-then-namespace order.
- [x] Q4) Do not distinguish "namespace empty" from "scope empty"; both return
  status no_matches with memories [] exactly as today.

Decision log
- Decision (Q1): Preserve exact three-argument operation invocation for omitted
  namespace_id; selector-present calls use a fourth positional argument. The
  service and plugin seam accept a trailing namespace_id=None.
- Decision (Q2): Keep SERVER_VERSION and the package marker at `0.2.1`; the
  additive optional selector does not require a compatibility-build increment,
  and this Track makes no host-owned changes.
- Decision (Q3): Validate query, scope, namespace_id, then tags.
- Decision (Q4): A valid empty or unknown selected namespace returns the same
  successful no_matches result as an empty selected scope.
- Decision: namespace_id narrows store discovery to namespace_directory within
  the selected scope; omitted preserves scope-wide recall.
- Decision: invalid namespace_id -> invalid_request/invalid_namespace; unknown
  valid namespace -> successful no_matches.
- Decision: no collection_id, no pagination, no ranker change, and no host-owned
  change.

Plan (execution steps)
- [x] S1) Resolve Q2 and record the public version decision, then move Track 037
  to ACTIVE (folder, filename, title status) after user review of the proposed
  decisions; no implementation before this step is checked.
- [x] S2) TDD domain chunk: add a focused failing test for
  MemoryService.recall(namespace_id=...) narrowing to one exact namespace
  (present-valid returns only that namespace, present-unknown returns [], omitted
  returns scope-wide, legacy v1 excluded under selection), plus focused store
  tests for a missing, symlinked, and non-directory namespace root; implement the
  store discovery-root narrowing and the service keyword-default parameter;
  refactor; run focused tests; update this Track.
- [x] S3) TDD MCP-schema/handler chunk: add focused failing tests for the
  definition (namespace_id property, anchored pattern, required unchanged), for
  handler validation (invalid values -> invalid_namespace, valid unknown ->
  no_matches, omitted -> scope-wide through an exact three-argument operation
  call, present -> operation receives a fourth selector argument, logging logs
  presence only), and update the exact TOOL equality test; make the smallest
  definition/handler/seam/plugin change; refactor; run focused tests; update this
  Track.
- [x] S4) TDD compatibility chunk: run the recall, retrieval, integration,
  production-compatibility, tool-arguments, and complete suites; verify seam and
  schema-boundary tests; run a direct configured-client recall check with and
  without the selector; update this Track.
- [x] S5) Documentation and version decision: update README.md,
  docs/ARCHITECTURE.md, docs/GLOSSARY.md, docs/MANUAL.md, and
  docs/GETTING_STARTED.md for the optional selector; apply the Q2 version
  decision already required by S1; run whitespace/link validation; update this
  Track.
- [x] S6) Validate and complete: review all acceptance criteria, record evidence,
  and move the Track to COMPLETED according to the backlog workflow.

Current inventory
- mymcp/plugins/mnemosyne/mcp/tools/memory_recall/definition.py (TOOL schema;
  optional anchored namespace_id selector; required remains query/scope)
- mymcp/plugins/mnemosyne/mcp/tools/memory_recall/handler.py (overloaded narrow
  RecallOperation protocol; query/scope/namespace/tags validation; omission-aware
  three/four-argument dispatch; selector-presence-only logging)
- mymcp/plugins/mnemosyne/plugin.py (_recall accepts and conditionally forwards a
  trailing namespace_id; wiring remains unchanged)
- mymcp/plugins/mnemosyne/memory/service.py (recall lines 121-127)
- mymcp/plugins/mnemosyne/memory/store.py (discover lines 314-328;
  `_validate_discovery_root`; optional namespace-rooted discovery; canonical-only
  selected results; _discover_candidates; MAX_CANDIDATES; MAX_DIRECTORY_DEPTH)
- mymcp/plugins/mnemosyne/memory/paths.py (namespace_directory lines 16-29)
- mymcp/plugins/mnemosyne/memory/normalization.py (IDENTIFIER_PATTERN line 7;
  normalize_identifier lines 46-50)
- mymcp/plugins/mnemosyne/memory/retrieval.py (rank_memories; MAX_RESULTS = 5)
- mymcp/plugins/mnemosyne/mcp/tools/memory_list/definition.py
  (IDENTIFIER_SCHEMA/NAMESPACE_SCHEMA precedent, lines 36-47)
- mymcp/plugins/mnemosyne/mcp/tools/memory_list/handler.py (invalid_namespace
  precedent, lines 113-129)
- tests/mcp/test_memory_recall.py (exact TOOL equality, anchored selector schema,
  invalid-selector precedence, exact three/four-argument adaptation, unknown
  namespace, and presence-only logging coverage)
- tests/memory/test_retrieval.py (service.recall call site, lines 203-237)
- tests/memory/test_store.py (discovery-root, missing-root, symlink, non-directory,
  path-safety, candidate-loading behavior, and focused namespace discovery cases)
- tests/mcp/test_memory_archive.py line 361, test_memory_restore.py line 206,
  test_memory_forget.py line 506 (bound read_service.recall seams)
- tests/mcp/test_mnemosyne_integration.py (operation-seam requirements lines
  273-292; read-service fake line 369)
- README.md, docs/ARCHITECTURE.md (recall sections and namespace-discovery
  boundaries), docs/GLOSSARY.md, docs/MANUAL.md, docs/GETTING_STARTED.md (public
  recall contract, canonical namespace selector, selected-root behavior, version
  decision, and usage guidance)

Artifacts
- Precedent Tracks: TRACK_004 (memory_recall scope contract), TRACK_005
  (filesystem retrieval), TRACK_016 (complete memory discovery), TRACK_017
  (read-only listing namespace selector), TRACK_036 (anchored schema patterns /
  Ollama compatibility).
- Living roadmap: `project/mymcp/roadmaps`, `MyMCP host and gateway roadmap`,
  active revision 7 (Phase 3A native installation NEXT). This Track is not
  roadmap-derived (new additive capability, not phase work); the roadmap remains
  current and needs no revision for this outcome.
- S2 red evidence: `pytest tests/memory/test_retrieval.py
  tests/memory/test_store.py` collected 35 tests with 4 expected failures because
  MemoryService.recall and FilesystemMemoryStore.discover did not yet accept
  namespace_id; 31 passed.
- S2 green evidence: the same focused command passed 35 tests after the minimal
  service/store implementation and compatibility-preserving refactor;
  `git diff --check` passed. Independent test review also ran the complete
  `tests/memory` suite with 312 passing tests and no file modifications.
- S3 red evidence: `pytest tests/mcp/test_memory_recall.py` collected 42 tests
  with 10 expected failures before the MCP implementation (schema, forwarding,
  logging, validation, and precedence); 32 passed. One initially incorrect
  boundary fixture was corrected from 64 characters (valid) to 65 (over-length).
- S3 green evidence: `pytest tests/mcp/test_memory_recall.py
  tests/mcp/test_mnemosyne_integration.py` passed 67 tests and
  `git diff --check` passed. Independent test review ran the combined recall,
  retrieval, store, and Mnemosyne integration set with 102 passing tests and no
  file modifications.
- S4 automated evidence: the declared recall, retrieval, store, Mnemosyne
  integration, production-compatibility, and Tool-argument suite passed 119
  tests. The complete repository suite passed 1,154 tests, and
  `git diff --check` passed.
- S4 configured-client evidence: the initial connected process was stale and
  required the recorded server restart/reconnect. After restart, direct
  `tools/list` on the configured `http://127.0.0.1:8000/mcp` endpoint advertised
  namespace_id with the exact anchored pattern and kept required equal to
  query/scope. A selector-present project/mnemosyne recall returned five ranked
  records, all with namespace_id `mnemosyne`; the same request with the selector
  omitted succeeded through scope-wide recall; a valid unknown namespace returned
  exactly `status: no_matches` with `memories: []`. No mutation Tool was called.
- S5 documentation evidence: README.md, docs/ARCHITECTURE.md,
  docs/GLOSSARY.md, docs/MANUAL.md, and docs/GETTING_STARTED.md document the
  optional selector, omission and canonical-only selection behavior, no-match and
  invalid-selector outcomes, no collection selector, selected-root safety,
  selector-presence-only logging, unchanged result/ranking bounds, and retained
  `0.2.1` marker. `pytest tests/mcp/test_memory_recall.py` passed 42 tests;
  relative Markdown-link validation and `git diff --check` passed. Independent
  documentation review found and resolved one stale scope-wide candidate-bound
  phrase and reported no remaining defect.

Completion notes
- S2 completed: MemoryService.recall accepts a trailing optional namespace_id and
  preserves the prior store call when omitted. FilesystemMemoryStore.discover
  validates the deterministic scope and selected namespace roots, narrows before
  candidate discovery, returns empty for missing or symlinked selected roots,
  rejects non-directory roots, and excludes legacy records from canonical
  namespace-selected results. Scope-wide discovery remains unchanged.
- S3 completed: memory_recall advertises the optional anchored namespace_id,
  validates it before tags, preserves exact three-argument operation calls when
  omitted, forwards a normalized fourth argument when present, and logs only
  selector presence. The plugin seam conditionally forwards the selector into
  the domain service without changing registration or host-owned code.
- S4 completed: 119 focused and 1,154 full-suite tests passed, whitespace
  validation passed, and post-restart configured-endpoint discovery plus
  selector-present, selector-omitted, and unknown-selector read-only calls passed.
- S5 completed: all five declared public documents now describe the implemented
  namespace-aware recall contract and approved unchanged version marker; focused
  schema tests, relative links, and whitespace validation pass.
- S6 completed: final validation passed all 1,154 automated tests, repository-wide
  relative Markdown-link validation, and `git diff --check`. Independent test and
  repository reviews found no implementation, acceptance, scope, secret,
  generated-artifact, or completion blocker. All acceptance criteria and
  milestones pass, and Track 037 moved to COMPLETED with synchronized title,
  filename, path, and status.
- Roadmap reconciliation: this additive capability was not roadmap-derived and
  does not change the delivered baseline, current phase, sequencing,
  dependencies, intended outcomes, or next major step. The living MyMCP host and
  gateway roadmap remains current at revision 7; no memory revision is needed.
- No commit, push, release, or durable memory mutation was performed.

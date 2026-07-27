# TRACK 036 [COMPLETED]: Ollama schema pattern compatibility

Track
- ID: TRACK_036
- Repository: MyMCP
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_036_COMPLETED_ollama_schema_pattern_compatibility.md

Problems (PORE)
- P1: As a MyMCP user with an Ollama/llama.cpp-backed MCP client, I cannot use
  the advertised Tool surface because llama.cpp rejects unanchored JSON Schema
  `pattern` values while compiling constrained Tool-call grammars.
- P2: As a caller storing legitimate multiline text, I need the compatibility
  fix to preserve the existing "contains at least one non-whitespace character"
  meaning rather than accidentally requiring dot-matched single-line text or
  entirely non-whitespace text.

Objective
- Make every serialized Mnemosyne Tool-schema pattern fully anchored and
  compatible with llama.cpp/Ollama constrained decoding without narrowing the
  intended nonblank-string contract.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing
  implementation, then refactoring and validation.
- Preserve the public `memory_*` Tool names, field shapes, bounds, mutation
  gates, consent requirements, and memory-domain validation semantics.
- Do not use `^\S+$`, which would reject legitimate spaces within labels,
  titles, and content.
- Do not adopt `^.*\S.*$` without resolving its failure to span line terminators
  under normal JSON Schema regular-expression semantics.
- Validate the selected anchored expression against the actual
  llama.cpp/Ollama JSON-Schema-to-GBNF compatibility boundary.
- Automated tests are required; a direct Ollama/llama.cpp check supplements and
  does not replace them.

Acceptance criteria
- [x] A1) [P1] With every Mnemosyne mutation gate enabled, recursive inspection
  of every advertised `inputSchema` reports no `pattern` value that lacks both a
  leading `^` and trailing `$`.
- [x] A2) [P2] Automated tests prove that removing converter-incompatible
  nonblank schema patterns leaves server validation accepting multi-word and
  multiline strings containing a non-whitespace character while rejecting
  whitespace-only strings.
- [x] A3) [P1] The complete advertised Tool surface is accepted by the available
  llama.cpp/Ollama constrained Tool-schema conversion path without the
  unanchored-pattern error.
- [x] A4) Existing focused Tool-schema tests and the complete automated suite
  pass.
- [x] A5) The public-contract/version consequence is resolved explicitly: either
  MyMCP advances consistently to patch version `0.2.1` with applicable
  documentation updates, or the Track records an approved reason not to change
  the released `0.2.0` marker.

Why now / impact
- One incompatible pattern in an advertised Tool can prevent common
  Ollama/llama.cpp clients from generating any constrained Tool call when they
  submit the complete Tool set. The current enabled surface can serialize 41
  unanchored occurrences across three Tools, making this a high-impact client
  interoperability defect.

Scope
- In scope:
  - The seven unanchored source patterns in `memory_recall`, `memory_remember`,
    and the private `memory_revise` adapter.
  - Recursive regression coverage over the complete gate-enabled advertised
    Mnemosyne Tool surface.
  - Semantic coverage for nonblank multi-word, multiline, and whitespace-only
    values.
  - Existing exact Tool-schema assertions affected by the replacement.
  - Direct validation against an available llama.cpp/Ollama schema-conversion
    path.
  - The patch-version and applicable public documentation decision required by
    the serialized Tool-schema change.
- Out of scope:
  - Tool names, request fields, result shapes, domain validation policy, storage,
    mutation enablement, or consent behavior.
  - General JSON Schema rewriting or adding a host-wide schema transformation
    layer.
  - Ollama installation, model acquisition, or unrelated client configuration.
  - Publishing a release unless separately and explicitly approved.

Milestones
- [x] M1) Confirm converter-compatible schema treatment that preserves
  semantically faithful server validation against the target llama.cpp/Ollama
  converter.
- [x] M2) Complete the focused schema compatibility TDD chunk.
- [x] M3) Resolve version/documentation treatment and pass final validation.

Risks / decisions
- Risk: `^.*\S.*$` is not equivalent to substring `\S` for strings containing
  line terminators because `.` is not dot-all by default.
- Risk: A semantically correct JSON Schema expression such as
  `^\s*\S[\s\S]*$` still requires empirical converter validation before it can
  be treated as llama.cpp-compatible.
- Observed risk: The installed Ollama/llama.cpp converter rejects anchored
  patterns containing `\s` or `\S` with a grammar-parse failure, including both
  `^.*\S.*$` and `^\s*\S[\s\S]*$`. Anchoring alone is therefore insufficient
  for this target runtime.
- Risk: Exact serialized-pattern counts are useful inventory evidence but are
  brittle as a permanent invariant when future Tools legitimately add patterns.
- Decision: Assert the durable anchoring invariant recursively; use current
  counts as Track evidence rather than the sole regression contract.
- Decision: Keep the fix in plugin-owned Tool definitions rather than adding
  transport, registry, or runtime schema rewriting.

Open questions
- [x] Q1) Which fully anchored expression preserves multiline nonblank semantics
  and is accepted by the target llama.cpp/Ollama converter?
- [x] Q2) Does this serialized public Tool-schema correction advance the
  endpoint/package marker to `0.2.1`?
- [x] Q3) Which existing public documents need a concise compatibility note if
  the patch version advances?

Decision log
- Decision (Q1, initial evidence): The initial candidate was
  `^\s*\S[\s\S]*$`; `^.*\S.*$` is not accepted as semantically equivalent
  without contrary evidence. Direct evidence now rejects both candidates. An
  in-memory check that removed only the seven nonblank-pattern sources allowed
  the complete nine-Tool surface to compile and generate a valid
  `memory_recall` call. Replacing the patterns with a narrower ASCII expression
  would change Unicode/multiline semantics, so removal with unchanged server
  validation was proposed and then approved as recorded below.
- Decision (Q1, resolved): The user approved removing the seven redundant
  nonblank schema patterns. Direct Ollama evidence rejects the semantically
  faithful shorthand-class expressions, while in-memory removal compiles the
  complete Tool surface. Existing server validation remains authoritative for
  nonblank values; no narrower ASCII-only schema expression will be introduced.
- Decision (Q2): Yes. The user approved treating the serialized public
  Tool-schema correction as a `0.2.1` patch. Host and package version markers
  must advance consistently; release publication remains separately approval
  gated and out of scope unless explicitly added.
- Decision (Q3): `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md`
  describe the current `0.2.1` compatibility build while preserving the
  historical released `0.2.0` cutover. Root, MCP, and route scoped guidance now
  identifies the active build accurately. Historical release notes, links,
  tags, artifacts, and completed Tracks remain unchanged.

Plan (execution steps)
- [x] S1) Move Track 036 to ACTIVE (folder, filename, title, and current path)
  after the user approves this plan and resolves or explicitly scopes Q2.
- [x] S2) TDD chunk: add a focused failing recursive anchoring invariant and
  nonblank-pattern semantic tests; confirm failure on the current schemas; make
  the smallest seven source-pattern changes; update affected exact-schema test
  expectations; run focused validation; and record evidence immediately.
- [x] S2a) Correct the converter-disproved S2 implementation under TDD: make the
  complete-surface invariant reject shorthand whitespace classes, replace regex
  semantic coverage with server-validation coverage, confirm focused failure,
  remove the seven redundant patterns, update exact schema expectations, and
  rerun focused validation.
- [x] S3) Run the complete automated suite and a direct available
  llama.cpp/Ollama constrained-schema compatibility check; record exact evidence.
- [x] S4) Apply the approved patch-version and applicable documentation outcome,
  validate consistency, and record evidence.
- [x] S5) Move Track 036 to COMPLETED after all acceptance criteria pass and
  capture final inventory and outcomes.

Current inventory
- `mymcp/plugins/mnemosyne/mcp/tools/memory_recall/definition.py` no longer
  publishes the redundant converter-incompatible nonblank pattern for recall
  tag items.
- `mymcp/plugins/mnemosyne/mcp/tools/memory_remember/definition.py` no longer
  publishes that pattern from its nullable-text helper, content, or tag items;
  the top-level and six-branch field shape and all length bounds remain.
- `mymcp/plugins/mnemosyne/mcp/tools/_memory_revise.py` no longer publishes that
  pattern from its nullable-text helper, content, or tag items.
- Recursive gate-enabled registry coverage now enforces that every remaining
  serialized pattern begins with `^`, ends with `$`, and contains neither
  converter-incompatible `\s` nor `\S` shorthand classes. The original failing
  TDD run exposed 41 unanchored occurrences; the revised failing run exposed the
  same 41 anchored but converter-incompatible serialized occurrences.
- Updated exact schema expectations remain in
  `tests/mcp/test_memory_recall.py`, `tests/mcp/test_memory_remember.py`, and
  `tests/mcp/test_memory_revise.py`.
- `tests/mcp/test_mnemosyne_integration.py` now owns the complete-surface
  Ollama-compatibility invariant and verifies through server validation that
  multi-word and multiline values remain accepted while whitespace-only content
  remains rejected.
- No ACTIVE Track existed when this DRAFT was created. The working tree was clean
  on `main` before this planning edit.
- `pyproject.toml` and `mymcp/settings.py` now agree on `0.2.1`; initialize,
  `/version`, and `list_tools` derive the updated marker while the Mnemosyne
  plugin version remains `0.1.0`.
- Current-version documentation distinguishes the unpublished `0.2.1` source
  build from the historical released `0.2.0` public-host cutover. The approved
  commit and push finalize this Track; no tag, wheel, or GitHub release is part
  of it.

Artifacts
- User-supplied defect analysis: unanchored `\S` patterns cause llama.cpp's JSON
  Schema-to-GBNF conversion to report that patterns must start with `^` and end
  with `$`.
- Project memory recall found no prior durable record for this specific defect.
- S2 failing evidence: `.venv/bin/python -m pytest
  tests/mcp/test_mnemosyne_integration.py -q` produced 1 failed and 24 passed;
  the invariant listed 41 unanchored serialized occurrences.
- S2 passing evidence: `.venv/bin/python -m pytest
  tests/mcp/test_mnemosyne_integration.py tests/mcp/test_memory_recall.py
  tests/mcp/test_memory_remember.py tests/mcp/test_memory_revise.py -q` produced
  172 passed.
- Independent S2 test review reran the same four focused modules with 172 passed
  in 0.15 seconds and `git diff --check` passed. It found the recursive anchoring
  and representative semantic coverage adequate; full-suite and target-converter
  validation remain pending S3.
- S3 automated evidence: `.venv/bin/python -m pytest -q` produced 1,141 passed
  in 4.61 seconds.
- S3 environment evidence: Ollama is installed at `/opt/homebrew/bin/ollama` and
  model `qwen3.6-27b:latest` is installed. No installation or model pull was
  performed.
- S3 converter evidence: the complete current nine-Tool surface returned HTTP
  400 `Failed to initialize samplers: failed to parse grammar`. Per-Tool checks
  isolated the failure to `memory_recall`, `memory_remember`, and
  `memory_revise`; the other six Tools returned HTTP 200.
- Candidate probes showed HTTP 400 for `^.*\S.*$`,
  `^\s*\S(?:\s|\S)*$`, `^(?:\s|\S)*\S(?:\s|\S)*$`,
  `^\s*\S(.|\n)*$`, `^\s*\S(?:.|\n)*$`,
  `^\s*\S[\s\S]*$`, and shorthand-class variants. Some explicit ASCII
  whitespace-class expressions compiled but do not preserve the existing
  Unicode and multiline nonblank semantics.
- An in-memory direct check removed only the seven new nonblank patterns while
  retaining every other schema pattern. Ollama accepted all nine Tools with
  HTTP 200 and generated a valid `memory_recall` call containing query and scope.
  No repository file was changed by that check. S3 remains incomplete until the
  approved production schema passes the same direct check.
- S2a failing evidence: `.venv/bin/python -m pytest
  tests/mcp/test_mnemosyne_integration.py -q` produced 1 failed and 24 passed;
  the revised invariant listed 41 shorthand-class pattern occurrences.
- S2a focused passing evidence: the four schema/integration modules produced
  172 passed in 0.25 seconds after removing the seven source patterns and
  updating exact expectations.
- Final S3 automated evidence: `.venv/bin/python -m pytest -q` produced 1,141
  passed in 5.18 seconds.
- Final S3 direct evidence: Ollama with `qwen3.6-27b:latest` accepted the complete
  production nine-Tool surface with HTTP 200 and generated a valid
  `memory_recall` call containing `query` and `scope` arguments.
- Independent S2a review found no issues, reran 172 focused tests and all 1,141
  tests successfully, and reported a clean `git diff --check`.
- S4 failing evidence: the six focused version/production modules produced 14
  failures and 65 passes after assertions advanced to `0.2.1` while package and
  server constants still reported `0.2.0`.
- S4 focused passing evidence: the same six modules produced 79 passed after
  `pyproject.toml`, `SERVER_VERSION`, and affected expectations advanced
  consistently.
- S4 complete validation produced 1,141 passed in 4.85 seconds, no remaining
  `0.2.0` test assertions, and a clean `git diff --check`. Independent test
  verification repeated 27 focused passes and all 1,141 suite passes, including
  wheel metadata coverage.
- Independent documentation review confirmed accurate current `0.2.1`,
  historical released `0.2.0`, Ollama compatibility, and unchanged roadmap
  sequencing after one route-guidance sentence was clarified to state that
  `0.2.1` is not published.
- Roadmap reconciliation: the living `MyMCP host and gateway roadmap` was
  inspected at revision 7. TRACK_036 is a maintenance compatibility build and
  does not change the delivered architecture, phase dependencies, or NEXT Phase
  3A native-installation work. The roadmap remains current; a future separately
  approved `0.2.1` release may warrant updating only its released baseline.

Completion notes
- TRACK_036 completed the unpublished MyMCP `0.2.1` compatibility build. Seven
  redundant nonblank patterns were removed from `memory_recall`,
  `memory_remember`, and `memory_revise` schemas after direct evidence showed
  that the installed Ollama/llama.cpp converter rejects `\s`/`\S` constructs
  even when anchored. Existing server validation preserves nonblank,
  multi-word, multiline, Unicode, mutation, consent, and storage behavior.
- Final evidence includes 172 focused passes, 1,141 complete-suite passes,
  independent test/documentation/repository reviews, clean whitespace checks,
  and an HTTP 200 Ollama generation over all nine production Tools with a valid
  `memory_recall` call. Package, server, initialize, `/version`, and `list_tools`
  markers agree on `0.2.1`; the Mnemosyne plugin remains `0.1.0`.
- Finalization includes the approved Track commit and push only. No tag, wheel,
  GitHub release, dependency installation, model pull, storage mutation, or
  roadmap mutation is part of this outcome. The living roadmap remains current
  with Phase 3A native installation next; only a future approved `0.2.1` release
  may require its released-baseline text to change.
- On 2026-07-27, the user independently tested the completed Tool surface with
  their Ollama model and confirmed that it works.

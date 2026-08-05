# TRACK 050 [COMPLETED]: llama.cpp grammar-safe Mnemosyne Tool schemas

Track
- ID: TRACK_050
- Repository: MyMCP
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_050_COMPLETED_llama_cpp_grammar_safe_tool_schemas.md

Problems (PORE)
- P1: As a MyMCP user with a llama.cpp-backed MCP client serving gpt-oss-20b, I
  cannot prompt at all when the Mnemosyne Tool surface is attached, because the
  client converts the advertised tool schemas into a constrained-call grammar and
  llama.cpp rejects it with `parse: error parsing grammar: number of repetitions
  exceeds sane defaults` / `Failed to initialize samplers: failed to parse
  grammar`. Direct probes against the running gpt-oss-20b server (TRACK_050
  Artifacts) reproduce the failure from `content` `maxLength: 4000` and the
  `occurred_at` `\d` pattern, each independently.
- P2: As a caller of `memory_list` through the same grammar path, I receive no
  usable constraint at all: the published top-level `oneOf` presence/absence
  combinator branches cannot be converted, so the client silently produces an
  unconstrained grammar (probe returned HTTP 200 for a schema containing the
  otherwise-crashing `cursor` `maxLength: 4096`, proving the branch logic was
  dropped).
- P3: As a MyMCP developer, I need the published schemas to stay safely below the
  llama.cpp repetition cap across converter versions so that no future grammar
  path (this model or another) can regenerate the failure.

Objective
- Make every advertised Mnemosyne `inputSchema` convertible by the llama.cpp
  JSON-Schema-to-GBNF path: remove the converter-hostile large `maxLength`
  values and the `\d` pattern from the published schemas, keep authoritative
  server-side enforcement, and pin recursive invariants so the failure cannot
  regress.

Non-negotiables
- This Track began as DRAFT and was moved to ACTIVE before implementation; its
  Move-to-ACTIVE plan step is checked.
- All implementation follows TDD: a focused failing test, the smallest passing
  implementation, then refactoring and validation, then Track update.
- Preserve the public `memory_*` Tool names, field shapes, result shapes,
  mutation gates, consent requirements, and memory-domain validation semantics.
  Server validation remains authoritative for length bounds; the schemas merely
  stop publishing bounds llama.cpp cannot convert.
- Do not add a host-wide schema-transformation layer (TRACK_036 precedent:
  plugin-owned definitions change; transport/registry/runtime rewrite is out of
  scope).
- Do not narrow semantic meaning: `[0-9]` replaces `\d` only for the UTC-second
  timestamp pattern, which is ASCII-digit-only under both ECMA-262 and the
  server's `%Y-%m-%dT%H:%M:%SZ` `strptime` parser.
- Automated tests are required; the direct llama.cpp probe supplements and does
  not replace them.

Acceptance criteria
- [x] A1) [P1] With every Mnemosyne mutation gate enabled, recursive inspection
  of every advertised `inputSchema` reports no `maxLength` greater than the
  documented safe bound (1000) and no `pattern` containing any backslash letter
  shorthand class (`\d`, `\w`, `\s`, `\S`, and case variants).
- [x] A2) [P1] Direct probe: the actual production schemas for
  `memory_remember`, `memory_revise`, and `memory_list` (the `TOOL` dicts, not
  synthetic stand-ins) are accepted by the running gpt-oss-20b llama.cpp server
  with HTTP 200, where the pre-fix schemas returned HTTP 400.
- [x] A3) [P2] `memory_list` no longer publishes the top-level `oneOf`
  combinator; its published schema is flat `properties`/`required`, and the
  direct probe shows it converts (HTTP 200) without a silent no-rule result.
- [x] A4) Server validation still enforces the removed bounds: content length
  `> 4000` and cursor/query length limits remain rejected exactly as before
  through the memory-domain parsers (`MemoryDraft.from_dict`,
  `MemoryRevision.from_dict`, `_parse_v1`, `_parse_v2`, list cursor decode).
- [x] A5) Existing focused Tool-schema tests and the complete automated suite
  pass; the capability-contract ledger carries new `1.2.0` entries for
  `memory_remember`, `memory_revise`, and `memory_list` while preserving all
  historical entries.
- [x] A6) The public-contract/version consequence is resolved explicitly: the
  version-impact decision below records every relevant dimension with an
  approved reason for each layer left unchanged.

Why now / impact
- The failure blocks all prompting for the user's primary local model while the
  Mnemosyne tool set is attached, and it will block any future model that uses
  grammar-enforced tool calling. Direct evidence shows two independent crash
  sources in the current surface (`content` 4000 and the `\d` pattern) plus one
  silent unconstraint (`memory_list`). The repair is small, follows the
  established TRACK_036 pattern, and is fully covered by the empirical boundary
  already measured (≤1900 safe, ≥2000 rejected on the target build).

Scope
- In scope:
  - `memory_remember`: remove `maxLength: 4_000` from `content`; replace the
    `\d` timestamp pattern with the equivalent `[0-9]` expression.
  - `memory_revise`: remove `maxLength: 4_000` from `content`.
  - `memory_list`: remove the published top-level `oneOf` presence/absence
    combinator; remove `maxLength: 4096` from `cursor` (its minLength and the
    server-side `MAX_MEMORY_LIST_CURSOR_LENGTH` enforcement remain).
  - Recursive regression invariants over the complete gate-enabled advertised
    surface for shorthand-class patterns and oversized `maxLength`.
  - Exact-schema test updates in `test_memory_remember.py`,
    `test_memory_revise.py`, and `test_memory_list.py`.
  - Capability-contract version advancement to `1.2.0` for the three changed
    Tools in `plugin.py`, `manifest.json`, and the test-owned ledger (historical
    entries preserved).
  - The host-version and documentation decision required by the serialized
    Tool-schema change (decision below).
  - Direct validation against the running gpt-oss-20b llama.cpp server with the
    production schemas.
- Out of scope:
  - `memory_recall` `query` `maxLength: 1000` (measured safe at 200 on the
    target build; unchanged so its `1.2.0` contract and ledger entry do not
    churn).
  - The four lifecycle/inspect Tools (no offending constructs; unchanged).
  - Tool names, request fields, result shapes, domain validation policy,
    storage, mutation enablement, or consent behavior.
  - General JSON Schema rewriting or a host-wide schema transformation layer.
  - The client-side per-model tool-calling configuration (grammar vs template);
    the fix makes any grammar path safe, it does not change client behavior.
  - Publishing a release unless separately and explicitly approved.

Milestones
- [x] M1) Confirm the failure and the safe boundary empirically on the target
  llama.cpp server (done in the Artifacts below; re-confirm production schemas
  after the fix).
- [x] M2) Complete the focused schema-compatibility TDD chunks for the three
  Tools.
- [x] M3) Advance capability contracts to `1.2.0` with ledger parity.
- [x] M4) Resolve the version/documentation treatment and pass final validation
  including the direct production-schema probe.

Risks / decisions
- Risk: The measured repetition cap (~1900–2000 on this build) is
  llama.cpp-version dependent. Mitigation: publish no `maxLength` above 1000
  (nearly 2x margin) and pin that invariant recursively.
- Risk: Removing `maxLength` from the schema could suggest unbounded input to
  clients. Mitigation: server enforcement is unchanged and authoritative; the
  tool descriptions continue to state bounded behavior where relevant.
- Risk: `\d` → `[0-9]` could be seen as narrowing. It is not: ECMA-262 `\d` is
  ASCII `[0-9]`, and the server parser accepts only `%Y-%m-%dT%H:%M:%SZ`.
- Risk: Dropping the `memory_list` `oneOf` could relax strict clients. The
  handler never enforced through that combinator (top-level-only projection is
  fully callable; a test proves it), and the published property descriptions
  continue to document the four valid argument combinations.
- Decision: Follow TRACK_036 precedent: fix in plugin-owned Tool definitions,
  keep server validation authoritative, no transport/registry/runtime schema
  rewriting.
- Version impact: Public MCP contract change — record the decision for every
  relevant dimension in the canonical identity/version model and the approved
  reason each unchanged layer remains unchanged (see Decision log Q1).

Open questions
- [x] Q1) Version-impact decision (see Decision log): host/package/endpoint
  marker `0.10.0` → `0.10.1` patch, plugin stays `0.3.0`, capability contracts
  for the three changed Tools advance to `1.2.0`, all other dimensions
  unchanged. Is the marker advance approved, or should the marker stay `0.10.0`
  with documentation noting the schema correction?
  RESOLVED: approved to advance to `0.10.1`.
- [x] Q2) Does the root `AGENTS.md` "Current Scope" paragraph (currently citing
  `0.8.0`) get corrected to the active build as part of this Track, per the
  TRACK_036 documentation precedent?
  RESOLVED: approved; correct the paragraph as part of S6.

Decision log
- Decision (Q1): APPROVED (user, 2026-08-05). Advance the
  MyMCP distribution/package/endpoint marker from `0.10.0` to `0.10.1` as a
  patch for the serialized Tool-schema correction (TRACK_036 advanced
  `0.2.0` → `0.2.1` for the same class of change), update `pyproject.toml`,
  `mymcp/settings.py` `SERVER_VERSION`, and version-pinning tests; keep the
  MCP protocol (`2025-11-25`), host plugin API (`1`), manifest schema (`1`),
  Authentication contract (`1`), host configuration schemas (`1`–`7`), plugin
  identity (`mnemosyne`), plugin version (`0.3.0`), configuration schema (`1`),
  plugin-data schema (`1`), memory record schema (`1`,`2`), runtime-generation
  semantics, and endpoint-visible Tool names unchanged — each unchanged layer
  because this Track alters only serialized Tool-schema shape, not any host,
  plugin, protocol, storage, or record contract; capability-contract versions
  (`memory_remember`, `memory_revise`, `memory_list` → `1.2.0`) are the single
  deliberately advanced capability dimension.
- Decision (Q2): APPROVED (user, 2026-08-05). Correct the root `AGENTS.md`
  "Current Scope" paragraph from the stale `0.8.0` citation to the active
  build as part of S6, per the TRACK_036 documentation precedent.

Plan (execution steps)
- [x] S1) Move Track 050 to ACTIVE (folder, filename, title, and current path)
  after the user approves this plan and resolves Q1/Q2.
- [x] S2) TDD chunk 1 (`memory_remember`): extend the complete-surface
  compatibility invariants in `tests/mcp/test_mnemosyne_integration.py` to
  reject backslash-letter shorthand classes in every published `pattern` and any
  published `maxLength` above 1000; update the exact-schema assertions in
  `tests/mcp/test_memory_remember.py` (`content` loses `maxLength: 4000`;
  `occurred_at` uses the `[0-9]` expression); confirm focused failure; make the
  smallest changes in `memory_remember/definition.py`; run focused validation;
  record evidence.
  DONE (2026-08-05). RED: both exact-schema assertions and the new shorthand
  invariant failed against the pre-fix surface. Implementation: removed
  `maxLength: 4_000` from `content` and replaced `\d` with `[0-9]` in
  `occurred_at` in `memory_remember/definition.py`; extended
  `test_mnemosyne_integration.py` with `_schema_max_lengths` and
  shorthand/maxLength invariants. Validation:
  `tests/mcp/test_memory_remember.py` 65 passed;
  `tests/mcp/test_mnemosyne_integration.py::test_every_advertised_mnemosyne_schema_pattern_is_ollama_compatible`
  fails only on the not-yet-implemented `memory_list` (4096) and
  `memory_revise` (4000) oversized `maxLength` values, which are S3/S4 scope;
  `memory_remember` no longer appears in any violation list. `compileall` OK.
- [x] S3) TDD chunk 2 (`memory_revise`): pin the `content` property schema in
  `tests/mcp/test_memory_revise.py` without `maxLength`; confirm failure;
  remove `maxLength: 4_000` from the `content` schema in
  `_memory_revise.py`; run focused validation; record evidence.
  DONE (2026-08-05). RED: new exact `content` assertion failed against the
  maxLength-bearing schema. Implementation: removed `maxLength: 4_000` from
  `content` in `_memory_revise.py::revise_input_schema` and pinned
  `{"type": "string", "minLength": 1}` in `test_memory_revise.py`. Validation:
  `tests/mcp/test_memory_revise.py` 49 passed; the integration invariant now
  fails only on `memory_list` (4096), the S4 target. `compileall` OK.
- [x] S4) TDD chunk 3 (`memory_list`): update `tests/mcp/test_memory_list.py`
  so the published schema is flat (no `oneOf`) and `cursor` carries no
  `maxLength`; confirm failure; remove the `oneOf` block and the cursor
  `maxLength` in `memory_list/definition.py`; run focused validation; record
  evidence.
  DONE (2026-08-05). RED: top-level key-set assertion flagged the extra
  `oneOf`; the integration invariant flagged `memory_list` cursor 4096.
  Implementation: removed the top-level `oneOf` block and the
  `maxLength: MAX_MEMORY_LIST_CURSOR_LENGTH` entry from `CURSOR_SCHEMA` in
  `memory_list/definition.py`, removed the now-unused import, and updated
  `test_memory_list.py` to pin the flat schema. Validation:
  `tests/mcp/test_memory_list.py` + `tests/mcp/test_mnemosyne_integration.py`
  58 passed; the complete-surface invariant is green for the first time;
  `test_memory_remember.py`, `test_memory_revise.py` also green (172 total
  focused passes across the four files). Server-side
  `MAX_MEMORY_LIST_CURSOR_LENGTH` enforcement in `memory/listing.py` and the
  4097-char cursor rejection test remain unchanged and passing. `compileall`
  OK.
- [x] S5) Capability-contract chunk: advance `memory_remember`,
  `memory_revise`, and `memory_list` to `1.2.0` in
  `mymcp/plugins/mnemosyne/plugin.py` and `manifest.json`; add the three
  `1.2.0` entries to `tests/plugin/capability_contract_ledger.json` with
  recomputed digests, preserving every historical entry; run the ledger,
  manifest-parity, and plugin-version validation; record evidence.
  DONE (2026-08-05). RED: ledger guard failed with "missing
  memory_list@1.2.0 ledger entry" before the additions. Implementation: advanced
  the three capability declarations in `plugin.py` and `manifest.json` to
  `1.2.0`; added the three ledger `1.2.0` entries
  (memory_list e412b346…, memory_remember e5bfecc4…, memory_revise 305340b5…,
  digests independently recomputed by the primary agent and matching);
  updated the version maps in `tests/mcp/test_mnemosyne_integration.py` and
  `tests/plugin/test_mnemosyne_manifest.py`. Historical ledger entries are
  byte-identical (verified against HEAD). Validation: full `tests/plugin/` plus
  `tests/mcp/test_mnemosyne_integration.py` 328 passed; the three focused tool
  suites 147 passed. `compileall` OK.
- [x] S6) Version/docs chunk (per approved Q1/Q2): advance the host marker to
  `0.10.1` in `pyproject.toml` and `mymcp/settings.py` and update
  version-pinning tests; update the compatibility notes in `README.md`,
  `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md`; correct the root `AGENTS.md`
  current-scope paragraph if approved; validate consistency; record evidence.
  DONE (2026-08-05). Q1/Q2 both APPROVED and recorded in the Decision log.
  Advanced `pyproject.toml` and `mymcp/settings.py` `SERVER_VERSION` to
  `0.10.1`; updated every hard-coded version pin in
  `test_oauth_dormancy.py`, `test_packaging.py`, `test_bootstrap.py`,
  `test_project_identity.py`, `test_mnemosyne_integration.py`,
  `test_startup_settings.py`, `test_list_tools.py`, and
  `test_production_compatibility.py` (renamed the stale
  `..._0_9_0` test function to `..._0_10_1`); added the `0.10.1`
  llama.cpp grammar-safety compatibility note to `README.md` and updated the
  current-version statements and the capability-count statement in `README.md`,
  `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md`; corrected the root
  `AGENTS.md` Current Scope paragraph (version lineage through `0.10.1`,
  four `1.2.0` capabilities, schemas 1-7). No stale `0.10.0` remains in code,
  tests, or the updated docs.
- [x] S7) Validation: run the complete automated suite; run the direct probe of
  the production `memory_remember`, `memory_revise`, and `memory_list` schemas
  against the running gpt-oss-20b server expecting HTTP 200; record exact
  evidence.
  DONE (2026-08-05). Full suite: `2067 passed, 3 skipped` (13.00s), including
  the complete-surface compatibility invariants in `test_mnemosyne_integration.py`
  and 5 new A4-focused content-bound tests in `tests/memory/test_records.py`
  (delegated to @test, diff reviewed by the primary agent). Direct probe of the
  production `TOOL` dicts for all three Tools → HTTP 200; a reconstructed
  pre-fix `memory_remember` schema (content `maxLength` 4000 plus `\d` pattern)
  → HTTP 400, confirming the probe remains sensitive. Plain-curl HTTP 400
  carries no error body; the OpenAI-format payload with `max_tokens: 8` is the
  verification path.
- [x] S8) Completion: review, update the Track inventory/completion notes, and
  move to COMPLETED after acceptance; per user approval, record the durable
  issue and resolution in project memory (`project/mymcp/issues`).
  DONE (2026-08-05). Acceptance criteria A1-A6 and milestones M1-M4 all met;
  inventory and completion notes updated below; Track moved to
  `.backlog/COMPLETED/2026/TRACK_050_COMPLETED_llama_cpp_grammar_safe_tool_schemas.md`;
  durable issue/resolution recorded in `project/mymcp/issues` per user approval.

Current inventory
- `mymcp/plugins/mnemosyne/mcp/tools/memory_remember/definition.py`:
  `content` schema no longer carries `maxLength` (removed in S2);
  `occurred_at` pattern at line 211 is now
  `^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$` (the only `\d`
  occurrence in the tools tree was removed in S2).
- `mymcp/plugins/mnemosyne/mcp/tools/_memory_revise.py`: `content` schema at
  lines 99-103 no longer carries `maxLength` (removed in S3).
- `mymcp/plugins/mnemosyne/mcp/tools/memory_list/definition.py`: the
  top-level `oneOf` presence/absence combinator and the cursor
  `maxLength: MAX_MEMORY_LIST_CURSOR_LENGTH` were removed in S4; the published
  schema is flat `properties`/`required` and `cursor` keeps `minLength: 1`;
  the unused `MAX_MEMORY_LIST_CURSOR_LENGTH` import was removed.
- Server-side enforcement (unchanged, authoritative):
  `memory/records.py` lines 498, 562, 663, 745 enforce `content <= 4000`;
  `memory/listing.py` enforces `MAX_MEMORY_LIST_CURSOR_LENGTH`; the server
  parses timestamps only via `%Y-%m-%dT%H:%M:%SZ` (`records.py` line 277).
- Exact-schema assertions: `tests/mcp/test_memory_remember.py` lines 243-247
  and 252-259; `tests/mcp/test_memory_list.py` lines 189-197 and 201-230;
  `tests/mcp/test_memory_revise.py` pins the property set but not `content`'s
  exact dict (line 132).
- Complete-surface invariants: `tests/mcp/test_mnemosyne_integration.py`
  lines 111-132 reject unanchored patterns and `\s`/`\S` only; no `\d` or
  `maxLength` guard exists.
- Capability contracts: `plugin.py` declares `1.2.0` for `memory_list`,
  `memory_remember`, `memory_revise` (and `memory_recall`), `1.1.0` for the
  other four; mirrored in `manifest.json`; ledger
  `tests/plugin/capability_contract_ledger.json` holds `1.0.0`/`1.1.0`/`1.2.0`
  entries for the three changed Tools and preserves every historical entry.
- Host markers: `pyproject.toml` and `mymcp/settings.py` `SERVER_VERSION` both
  `0.10.1`; the version-pinning tests in eight test modules reference
  `0.10.1` (remaining `0.10.0` strings are historical attributions, unchanged).

Artifacts
- Direct probes against the running gpt-oss-20b server
  (`llama serve --alias unsloth/gpt-oss-20b-GGUF:F16`, localhost:8080):
  - `content` with no `maxLength` → HTTP 200.
  - `content` `maxLength` 100–1900 → HTTP 200 (tested 100, 1000, 1001, 1100,
    1500, 1600, 1800, 1900).
  - `content` `maxLength` 2000, 3000, 4000, 4096 → HTTP 400
    `Failed to initialize samplers: failed to parse grammar`.
  - `occurred_at` pattern with `\d` → HTTP 400 (same grammar failure);
    with `[0-9]` → HTTP 200.
  - `memory_list`-shaped schema (oneOf `not`/`anyOf` presence branches plus
    `cursor` `maxLength: 4096`) → HTTP 200, i.e. the combinator silently
    suppresses the otherwise-crashing bound.
- User defect report: gpt-oss-20b prompts fail with
  `parse: error parsing grammar: number of repetitions exceeds sane defaults`;
  qwen3.6-27b on the same `llama serve` binary and schema set succeeds,
  consistent with a per-model grammar vs template tool-calling path.
- Final acceptance probe (S7, 2026-08-05): the production `TOOL` dicts for
  `memory_remember`, `memory_revise`, and `memory_list` submitted through the
  OpenAI-format `max_tokens: 8` payload against the running gpt-oss-20b server
  each return HTTP 200; a reconstructed pre-fix `memory_remember` schema
  (content `maxLength` 4000, `\d` pattern) returns HTTP 400 — the probe is
  still sensitive to the removed constructs. Temp probe files were cleaned up.
- A4 automated evidence (S7, 2026-08-05): `tests/memory/test_records.py` gains
  five focused tests proving 4001-character content is rejected with a
  `MemoryValidationError` (`.field == "content"`) through `MemoryDraft.from_dict`,
  `MemoryRevision.from_dict`, and `parse_memory_record` v1/v2, plus the
  exactly-4000 boundary case accepted. Cursor > 4096 and query > 1000 rejection
  were already covered by existing tests.
- TRACK_036 precedent: identical defect class fixed by removing
  converter-incompatible constructs from plugin-owned schemas while keeping
  server validation authoritative and validating directly against the installed
  converter.

Completion notes
- Completed 2026-08-05. Defect (TRACK_036-class): the advertised Mnemosyne Tool
  schemas contained constructs the llama.cpp JSON-Schema-to-GBNF converter
  rejects (`content` `maxLength: 4000`, the `\d` shorthand pattern) plus a
  silently-unconstraining `memory_list` `oneOf` combinator; gpt-oss-20b prompts
  failed while attached to the Mnemosyne tool set. Fixed in the plugin-owned
  Tool definitions (`memory_remember`, `memory_revise`, `memory_list`) while
  keeping server-side validation authoritative; added recursive complete-surface
  compatibility invariants; advanced the three capability contracts to `1.2.0`
  with ledger parity; advanced the host marker to `0.10.1` with full docs.
  Acceptance criteria A1-A6 all met. Final validation: 2067 passed, 3 skipped;
  production schemas probe HTTP 200 against the target server; A4 content/cursor/
  query server-enforcement bounds proven by automated tests. No release published;
  no commits/pushes made without separate approval. Durable issue and resolution
  recorded in `project/mymcp/issues`.

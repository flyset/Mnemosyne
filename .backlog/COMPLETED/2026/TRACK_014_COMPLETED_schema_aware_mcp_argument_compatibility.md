# TRACK 014 [COMPLETED]: schema-aware MCP argument compatibility

Track
- ID: TRACK_014
- Repository: Mnemosyne
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_014_COMPLETED_schema_aware_mcp_argument_compatibility.md

Problems (PORE)
- P1: As a user of an MCP client that stringifies structured Tool arguments, I receive validation errors for schema-valid calls, because Mnemosyne dispatches JSON strings where Tool schemas require objects or arrays.
- P2: As a maintainer, I risk adding inconsistent per-Tool decoding workarounds, because MCP dispatch has no shared schema-aware compatibility boundary.

Objective
- Normalize exactly one stringified JSON layer for schema-declared non-string Tool argument fields at central MCP Tool dispatch while preserving native requests, strict Tool validation, and least privilege.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Decode only when the applicable Tool input schema permits a non-string type and does not permit a string at that argument position.
- Decode at most one layer; never recursively decode and never infer types from string appearance alone.
- Preserve each Tool's existing validation and bounded error behavior after normalization.
- Do not change canonical memory record schemas or persistence behavior.
- Remove the temporary complete `memory_remember` payload log and restore content-free mutation logging.

Acceptance criteria
- [x] A1) [P1] A captured Claude-style `memory_remember` request with stringified `namespace`, `collection`, and `tags` reaches the existing handler as native object/object/array values and succeeds under an enabled isolated registry.
- [x] A2) [P1] Equivalent correctly typed arguments remain unchanged and existing native Tool behavior passes.
- [x] A3) [P1, P2] The shared normalizer follows the selected Tool's schema through object properties and composition keywords needed by current Tool definitions, decodes only one layer when the decoded JSON type is schema-allowed and string is not, and leaves malformed or wrong-type strings for ordinary Tool validation.
- [x] A4) [P1, P2] Schema positions that permit strings are never decoded, including memory title/content/labels and recall query/tag items.
- [x] A5) [P2] Unknown Tools and Tools without matching argument properties preserve existing dispatch behavior.
- [x] A6) [P1] The complete temporary payload log is absent, mutation logs are content-free again, and no submitted memory text appears in automated log assertions.
- [x] A7) [P1, P2] Focused and full automated tests, whitespace validation, and a direct/native plus configured-client compatibility check pass.

Why now / impact
- Live evidence showed Claude Desktop sent `memory_remember.namespace`, `collection`, and `tags` as JSON text strings while another MCP client sent their native JSON types. The current validator correctly rejects the former, blocking otherwise valid use through an unmodifiable client.

Scope
- In scope:
  - A shared schema-aware Tool-argument compatibility normalizer under `mnemosyne/mcp/`.
  - Central application through `ToolRegistry.call_tool()` before handler dispatch.
  - Current JSON Schema shapes used by Mnemosyne: `type`, object `properties`, `oneOf`, `anyOf`, and `const`-discriminated branches.
  - Tests for native, stringified, malformed, wrong-type, string-permitted, unknown-Tool, and real remember behavior.
  - Public architecture/behavior documentation and removal of temporary payload logging.
- Out of scope:
  - Recursively parsing arbitrary JSON-looking strings.
  - Accepting client-supplied paths or broadening Tool capabilities.
  - Modifying Claude Desktop or requiring a proxy.
  - General JSON Schema validation by the registry.

Milestones
- [x] M1) Shared normalizer contract passes focused TDD.
- [x] M2) Central registry integration passes real remember and regression tests.
- [x] M3) Documentation, full validation, and configured-client evidence complete.

Risks / decisions
- Risk: Broad string decoding could mutate legitimate text or weaken validation.
- Decision: Normalize only schema-declared argument positions where string is disallowed but the one-layer decoded JSON type is allowed.
- Risk: Composition branches can describe different types or scope-specific object shapes.
- Decision: Resolve schema allowance across applicable `oneOf`/`anyOf` branches and normalize only when the result is unambiguous for the received field; normal Tool validation remains authoritative.
- Risk: A malformed string could produce a new registry-owned error contract.
- Decision: Leave malformed and wrong-type strings unchanged so existing Tool handlers return their established bounded validation errors.

Open questions
- [x] Q1) Is the client discrepancy observable at the handler boundary?
- [x] Q2) Should compatibility be Tool-local or central?

Decision log
- Decision (Q1, 2026-07-19): Temporary local logging showed Claude sent `namespace` and `collection` as JSON object text and `tags` as JSON array text; a native client sent object/object/array values.
- Decision (Q1, 2026-07-19): Direct native remember succeeded and its synthetic record was archived and permanently forgotten; no test record remains.
- Decision (Q2, 2026-07-19): The user selected central schema-aware normalization rather than a remember-only workaround.
- Decision (2026-07-19): The public Tool schema remains canonical and advertises proper JSON types; compatibility is an inbound dispatch adaptation for non-conforming clients.

Plan (execution steps)
- [x] S1) Move Track 014 to ACTIVE (folder, filename, title, and current path status).
- [x] S2) Execute one TDD chunk for a pure schema-aware, one-layer argument normalizer covering current schema composition and string-safety rules.
- [x] S3) Execute one TDD chunk integrating normalization into `ToolRegistry.call_tool()` with captured Claude-style remember, native regression, and unknown-Tool coverage; remove the temporary payload log.
- [x] S4) Refactor, update `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md`, run focused/full automated validation and `git diff --check`, and record evidence.
- [x] S5) Restart/reload the local server and verify native direct MCP plus one Claude Desktop retry; record content-free evidence.
- [x] S6) Confirm acceptance, move Track 014 to COMPLETED, and record final outcomes.

Current inventory
- `mnemosyne/mcp/tool_arguments.py` now owns a pure, non-mutating, one-layer schema-aware normalizer. It resolves current `properties`, `oneOf`, `anyOf`, and `const`-discriminated shapes; decodes only when string is disallowed and the decoded JSON type is allowed; and leaves malformed, wrong-type, twice-stringified, or string-permitted values unchanged.
- `tests/mcp/test_tool_arguments.py` covers the captured remember wire shape, native non-mutation, title/content/tag-item string preservation, malformed/wrong/twice-stringified values, nullable composition, non-string scalars, and schemas that permit strings.
- `ToolRegistry` now retains an immutable Tool-name-to-input-schema mapping derived from the same selected definitions used for discovery. Known Tool dispatch non-mutatingly normalizes arguments against that exact schema before invoking the paired handler; unknown Tools still return `None` before normalization.
- Registry tests cover synthetic handler-boundary normalization, the captured Claude-style real remember request, native real remember behavior, stringified inspect references, stringified lifecycle references/revisions, disabled/unknown dispatch, and unchanged string content.
- The temporary full-argument logger has been removed from `memory_remember`; its existing content-free terminal logging remains unchanged.
- Before this Track, `ToolRegistry.call_tool()` passed arguments unchanged and retained no Tool-name-to-schema mapping; S3 replaced that behavior with selected-schema normalization.
- Current Tool schemas use root objects, nested `properties`, and `oneOf`/`anyOf` composition. Remember uses root scope-discriminated `oneOf` branches; collection and nullable text use `anyOf`.
- `mnemosyne/mcp/tools/memory_remember/handler.py` delegates strict draft validation to `MemoryDraft.from_dict()`; it should remain unaware of client-specific serialization after central normalization.
- `tests/mcp/test_registry.py` covers conditional discovery/dispatch and real enabled remember persistence. `tests/mcp/test_memory_remember.py` covers handler validation, persistence, and content-free logs.
- The working tree began with one user-added temporary complete-arguments logger in the remember handler; S3 removed it and focused logging tests pass.
- Baseline focused remember/record validation passed 67 tests. A live policy-refused native call proved the current server accepts proper namespace objects without writing.
- `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` now document central selected-schema normalization, its one-layer/string-safety boundary, unchanged Tool schemas, and continued handler validation.
- Review-driven regressions cover oversized JSON numbers, decoder recursion failure, no descent into newly decoded values, unconstrained/string-permitted branches, JSON number/integer semantics, and strict boolean-versus-number const discrimination.

Artifacts
- Captured local log evidence was reviewed in-session and is intentionally not copied into durable Track content because it includes submitted memory text.
- Remember contract prerequisite: `.backlog/COMPLETED/2026/TRACK_007_COMPLETED_consent_gated_memory_remember.md`.

Completion notes
- Planning and ACTIVE transition were explicitly approved on 2026-07-19. The next unchecked step is S2.
- S2 TDD evidence: focused collection first failed because `mnemosyne.mcp.tool_arguments` did not exist. The minimal pure normalizer then passed all 7 focused tests. Registry dispatch remains unchanged. The next unchecked step is S3.
- S3 TDD evidence: the two new registry tests first failed because synthetic dispatch received unchanged strings and the captured real remember request returned `invalid_record` at `namespace`; the failure log also confirmed the temporary payload logger remained active. The minimal registry schema mapping/normalization and logger removal made the focused normalizer/registry/remember slice pass 79 tests. Additional real inspect and lifecycle compatibility regressions brought the focused passing total to 81. The next unchecked step is S4.
- S4 review and validation evidence: initial focused/documentation validation passed 106 tests, the full suite passed 533 tests, and `git diff --check` passed. Independent read-only review then found oversized-integer parsing, recursive descent after decode, unconstrained composition, JSON numeric, and bool/numeric const edge cases. Focused regressions failed on the applicable cases; a conservative value-type refactor fixed them. Re-review confirmed all five findings resolved and identified decoder recursion as the remaining bounded-failure edge; its focused regression failed before `RecursionError` was added to the unchanged-value fallback. Final S4 validation passed 112 focused tests and 539 full-suite tests in 5.33 seconds; `git diff --check` passed. The next unchecked step is S5.
- S5 direct evidence: the reloaded port-8000 server returned the same bounded `disallowed_content` result for native and stringified synthetic remember requests, proving both paths reached content policy without a write.
- S5 configured-client evidence: Claude Desktop retried a previously rejected request with stringified structured fields; it returned `remembered` at active revision 1 and created a new `prometheus` namespace and `overview` collection. This proves compatibility is not restricted to pre-existing namespace paths. The created record is user-intended memory and was not removed.
- Track 014 completed on 2026-07-19. Central selected-schema normalization supports native and one-layer stringified structured arguments without changing advertised Tool schemas, canonical memory models, or content-free mutation logging.

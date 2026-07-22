# TRACK 024 [COMPLETED]: Mnemosyne integration boundary

Track
- ID: TRACK_024
- Repository: MyMCP (hosting the Mnemosyne memory domain in-process)
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_024_COMPLETED_mnemosyne_integration_boundary.md

Problems (PORE)
- P1: As a maintainer evolving MyMCP into a reusable host, I cannot identify a generic Tool-registry boundary, because `mymcp/mcp/tools/registry.py` combines immutable registry mechanics with hard-coded Mnemosyne Tool imports, enablement gates, and handler binding.
- P2: As a maintainer preparing a future Mnemosyne extraction, I must change multiple memory Tool handlers to alter service construction, because each handler independently constructs a `MemoryService` over a `FilesystemMemoryStore` from Mnemosyne settings.
- P3: As an existing Mnemosyne user, I risk an observable behavior regression during internal separation, because discovery, dispatch, tool ordering, schema normalization, mutation gates, and service composition presently meet at one startup registry.

Objective
- Establish a generic MyMCP registry/dispatch boundary and an explicit in-process Mnemosyne integration composition layer while preserving every current public Mnemosyne contract.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Preserve local-first, single-user, least-privilege, explicit-tool, and per-call consent boundaries.
- Preserve all current MCP Tool names, schemas, ordering, results, errors, HTTP endpoints, logging constraints, argument normalization, and startup-fixed enablement behavior.
- Preserve `SERVER_NAME = "mnemosyne"`, `MNEMOSYNE_*` settings, `~/.mnemosyne` paths, memory namespace data, and memory-list HMAC domains.
- Keep HTTP transport thin and MCP semantics under `mymcp/mcp/`.
- Do not claim or implement plugin discovery, installation, manifests, isolation, tool renaming/namespacing, generic storage, or generic approval services.

Acceptance criteria
- [x] A1) [P1] Generic registry and dispatch code import no Mnemosyne memory Tool packages or Mnemosyne settings and accept only explicit Tool/handler registrations.
- [x] A2) [P1, P3] The composed startup registry exposes and dispatches exactly the same default and independently enabled Mnemosyne Tools in the same order as before.
- [x] A3) [P1, P3] `tools/list`, `list_tools`, and `tools/call` use one immutable composed registry and retain schema-aware one-layer argument normalization.
- [x] A4) [P2, P3] Mnemosyne integration owns memory Tool registration, gate selection, and service/store composition; individual memory handlers no longer resolve the root or construct a service directly.
- [x] A5) [P3] Existing Mnemosyne server identity, settings, storage compatibility, Tool contracts, bounded errors, and logging guarantees remain unchanged.
- [x] A6) [P1, P2, P3] Package-boundary documentation accurately describes the in-process integration seam without claiming plugin extraction or public namespacing.
- [x] A7) [P1, P2, P3] Focused, full, and direct MCP validation pass.

Why now / impact
- Track 023 established MyMCP as the host package name. This Track establishes the smallest internal composition seam required before evaluating actual plugin contracts or client-visible namespacing, without prematurely building either.

Scope
- In scope:
  - Extract generic immutable registry/dispatch mechanics from `mymcp/mcp/tools/registry.py` into a host-owned MCP boundary.
  - Define an explicit Tool/handler registration contract with strict pairing, unique-name, immutable-discovery, and schema-normalization behavior.
  - Add an in-process Mnemosyne integration composition layer that owns current memory Tool registration, ordering, enablement selection, and handler binding.
  - Route one startup-composed registry through MCP discovery and dispatch.
  - Move memory service/store construction behind integration-supplied operations or factories so Tool handlers no longer resolve `get_memory_root()` or construct `MemoryService` directly.
  - Add focused generic-registry, integration-composition, handler-boundary, startup-registry, and direct MCP coverage.
  - Update affected architecture and glossary documentation.
- Out of scope:
  - Extracting Mnemosyne as an independently packaged or installed plugin.
  - Plugin discovery, manifests, installation, isolation, lifecycle, configuration UI, or aggregation.
  - Public Tool renaming, plugin-origin metadata, client configuration renaming, or Tool namespacing.
  - Generalizing memory scopes, kinds, retrieval, storage record semantics, lifecycle, consent policy, or content policy.
  - Renaming Mnemosyne server, settings, environment variables, paths, HMAC domains, or existing data.
  - Adding shell execution, unrestricted filesystem access, network services, or multi-user behavior.

Milestones
- [x] M1) Generic registry contract is independent of Mnemosyne imports and settings.
- [x] M2) Mnemosyne integration composes the unchanged public memory Tool surface.
- [x] M3) Tool handlers no longer own root/service/store construction.
- [x] M4) Documentation and full validation establish the transitional boundary.

Risks / decisions
- Risk: Moving composition can change startup-time settings reads, Tool ordering, or mutation enablement.
- Mitigation: Preserve one startup-fixed composition point; add explicit ordering/gate tests before moving behavior.
- Risk: Broad handler refactoring can weaken Tool-specific validation, bounded errors, or content-free logging.
- Mitigation: Keep request parsing, result projection, error mapping, and logs in Tool adapters; inject only narrowly typed operations/factories.
- Risk: A generic registry abstraction may become a premature plugin framework.
- Mitigation: Limit it to explicit in-process registrations; no dynamic loading, plugin metadata, or public namespacing.
- Decision: MyMCP owns generic registration and protocol mechanics; Mnemosyne integration owns memory Tool selection and composition.
- Decision: Public Tool names remain unchanged until a later compatibility Track designs multi-plugin naming.

Open questions
- [x] Q1) Should a generic Tool registration be represented as a frozen dataclass or a validated tuple/mapping?
- [x] Q2) Should the Mnemosyne integration supply individual typed service operations or one narrowly scoped service factory to Tool handlers?
- [x] Q3) Where should the host composition entrypoint live while `mymcp/settings.py` still contains retained Mnemosyne configuration?

Decision log
- Decision (Q1): Use a frozen `ToolRegistration` dataclass containing one Tool definition and its handler. `ToolRegistry` accepts only explicit complete registrations, snapshots ordered definitions, rejects duplicate names, and owns schema-aware dispatch. This makes pairing structural while keeping the boundary smaller than a plugin contract.
- Decision (Q3): Use `mymcp/mcp/startup.py` as the host composition root. It resolves retained `MemoryToolSettings` exactly once and delegates Mnemosyne Tool selection and binding to `mymcp/mcp/integrations/mnemosyne.py`; MCP methods consume the resulting generic registry. This keeps startup fixed without putting memory Tool imports or selection policy in generic registry/dispatch code.
- Decision (Q2): Supply individual narrowly typed operations to handlers. The Mnemosyne integration centralizes one private lazy construction path for `MemoryService(FilesystemMemoryStore(get_memory_root()))`, binds explicit recall/list/inspect/remember/archive/restore/revise/forget operations, and selects mutation-disabled or enabled services by operation. This preserves least privilege, validation-before-root resolution, fresh-service behavior, and handler-level default-off mutation gates while avoiding handler/integration circular imports.

Plan (execution steps)
- [x] S1) Move TRACK_024 to ACTIVE (folder, filename, title, and current path) and check this step before implementation.
- [x] S2) Execute the generic-registry TDD chunk: add focused failing tests for explicit complete registrations, unique names, immutable discovery, unknown Tools, and schema-aware normalization without Mnemosyne imports; make the smallest generic registry pass; refactor current registry tests; run focused validation; update this Track.
- [x] S3) Execute the Mnemosyne-integration TDD chunk: add focused failing tests for the unchanged ordered default/enabled Tool surface from a single integration composition; move hard-coded memory imports, gates, and handler bindings into the integration layer; make tests pass; run focused registry/startup validation; update this Track.
- [x] S4) Execute the handler-composition TDD chunk: add focused boundary tests proving memory handlers receive integration-supplied operations/factories and no longer resolve the root or construct services directly; make the smallest behavior-preserving migration; run focused Tool and import-boundary validation; update this Track.
- [x] S5) Update package-boundary documentation, run the complete automated suite and whitespace validation, perform direct MCP discovery/call checks, review all acceptance criteria, and record evidence.
- [x] S6) Move TRACK_024 to COMPLETED (folder, filename, title, and current path), check this transition, and record completion outcomes.

Current inventory
- `mymcp/mcp/tool_registry.py` now owns the generic frozen `ToolRegistration` and `ToolRegistry` contracts, defensive immutable discovery snapshots, unique-name validation, unknown-Tool handling, and schema-aware dispatch. It imports no Mnemosyne Tool package, memory domain, or settings.
- `mymcp/mcp/integrations/mnemosyne.py` now owns all current Mnemosyne Tool imports, fixed ordering, independent mutation-gate selection, real handler binding, and `list_tools` binding over the selected surface. The former mixed `mymcp/mcp/tools/registry.py` no longer exists.
- `mymcp/mcp/startup.py` is the single startup composition root: it resolves retained memory Tool settings once and stores one composed generic registry.
- `mymcp/mcp/methods.py` uses that one registry for `tools/list` and `tools/call`; its narrow `call_tool` wrapper remains monkeypatchable for protocol tests without owning registration policy.
- `mymcp/mcp/tools/` now contains Tool definitions and adapters only. Its host-level `list_tools` Tool remains unchanged and receives the selected surface from the Mnemosyne integration.
- `mymcp/settings.py` contains retained Mnemosyne public server/configuration identity and memory mutation gate resolution; it must remain behaviorally unchanged in this Track.
- `mymcp/mcp/integrations/mnemosyne.py` now owns one private lazy service-construction path and eight explicit typed operation adapters. Every validated operation call resolves a fresh root/store/service; recall/list/inspect use mutation-disabled services and remember/archive/restore/revise/forget use enabled services.
- The eight public memory Tool handlers require their corresponding narrow operation and no longer import `get_memory_root` or `FilesystemMemoryStore`, or import/construct concrete `MemoryService`. Request parsing, result projection, bounded errors, content-free logging, and mutation gates remain handler-owned; `_memory_lifecycle.py`, `_memory_revise.py`, and `_memory_forget.py` are unchanged.
- `mymcp/memory/` remains a tool-independent but semantically Mnemosyne-specific domain boundary and imports no MCP, FastAPI, or routes.
- `tests/mcp/test_mnemosyne_integration.py` protects default and independently enabled ordering, mutation handler availability, selected-surface `list_tools`, startup/method registry identity, required operation seams, lazy/fresh service composition, validation-before-construction, all eight real operation bindings, and read/mutation service modes. `tests/memory/test_import_boundaries.py` proves construction ownership moved out of handlers. The eight handler suites inject explicit stub or test-owned real service operations; recall and remember include direct operation-adaptation tests. `tests/mcp/test_tool_registry.py`, `tests/mcp/test_registry.py`, startup-setting tests, method tests, and route tests continue to protect existing dispatch and public behavior.
- `README.md` now concisely explains the generic immutable Tool registry, one startup composition root, explicit in-process Mnemosyne integration, preserved public contracts, and the absence of plugin extraction, discovery, or namespacing beside the shared memory-domain/Tool-gate architecture.
- `docs/ARCHITECTURE.md` now inventories `tool_registry.py`, `startup.py`, and the `integrations/` package; defines their separate responsibilities; identifies handlers as narrow typed operation adapters; and documents lazy fresh service composition with mutation-disabled reads and mutation-enabled operations only after handler gates.
- `docs/GLOSSARY.md` now defines Tool registration, startup registry, and the Mnemosyne integration layer, and distinguishes the in-process host seam from an extracted plugin system.
- Track 023 completed in commit `c76b31e`; the pre-MyMCP package state is preserved by tag `mnemosyne-v0.1.3-pre-mymcp` at `6099588`.

Artifacts
- Project-memory idea: `Idea: incremental host separation within Mnemosyne`.
- Project-memory ideation: `MyMCP — self-hostable MCP plugin host (project ideation)`.
- Pre-MyMCP rollback tag: `mnemosyne-v0.1.3-pre-mymcp`.
- S2 TDD evidence: focused test collection initially failed with `ModuleNotFoundError: No module named 'mymcp.mcp.tool_registry'`; after the smallest implementation and refactor, 65 focused registry/route tests passed and `git diff --check` passed on 2026-07-22.
- S3 TDD evidence: focused test collection initially failed with `ModuleNotFoundError: No module named 'mymcp.mcp.integrations'`; after moving composition and wiring the startup registry, 99 focused integration/registry/startup/method/route tests passed and `git diff --check` passed on 2026-07-22.
- S4 red evidence: `python -m pytest tests/memory/test_import_boundaries.py tests/mcp/test_mnemosyne_integration.py` collected 37 tests and produced 19 failed, 18 passed before production changes; failures covered all eight handler-owned constructors, all eight non-required operation seams, and absent integration construction.
- S4 focused green evidence: `python -m pytest tests/memory/test_import_boundaries.py tests/mcp/test_mnemosyne_integration.py tests/mcp/test_memory_recall.py::test_memory_recall_adapts_valid_arguments_to_the_supplied_operation tests/mcp/test_memory_remember.py::test_memory_remember_adapts_a_valid_draft_to_the_supplied_operation` passed 39 tests on 2026-07-22.
- S4 handler green evidence: `python -m pytest tests/mcp/test_memory_recall.py tests/mcp/test_memory_list.py tests/mcp/test_memory_inspect.py tests/mcp/test_memory_remember.py tests/mcp/test_memory_archive.py tests/mcp/test_memory_restore.py tests/mcp/test_memory_revise.py tests/mcp/test_memory_forget.py` passed 271 tests on 2026-07-22.
- S4 broad green evidence: `python -m pytest tests/mcp tests/memory tests/routes/test_mcp.py` passed 682 tests on 2026-07-22; `git diff --check` passed with no output.
- S5 documentation inventory: updated `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` for the generic registry, single startup root, and explicit in-process Mnemosyne integration boundary; no other durable public documentation was changed.
- S5 automated evidence: `python -m pytest` collected 778 tests and passed all 778 in 7.45 seconds on 2026-07-22; `git diff --check` passed with no output. Compatibility version remains `0.1.3` because public Mnemosyne behavior is unchanged.
- S5 direct MCP evidence: configured-client `list_tools` reported server `mnemosyne 0.1.3` and the expected ordered nine-Tool enabled surface; bounded `memory_list` for project namespace `mnemosyne` returned `status: ok`, five items, and 28 total without content; bounded `memory_recall` for integration-boundary architecture returned `status: ok` with the existing incremental host-separation context. No mutation Tool was called.

Completion notes
- 2026-07-22: Track moved to ACTIVE before implementation, with S2 selected as the first TDD chunk.
- 2026-07-22: Completed S2. The generic registry boundary now accepts only explicit Tool/handler registrations and preserves schema-aware dispatch without importing Mnemosyne Tools or settings. S3 is next.
- 2026-07-22: Completed S3. Mnemosyne integration now owns Tool selection and binding, while one host startup registry drives discovery and dispatch. S4 and Q2 are next.
- 2026-07-22: Completed S4 and resolved Q2 in favor of individual typed operations. Mnemosyne integration now owns lazy root/store/service composition, handlers retain narrow validation and policy boundaries without construction capability, and S5 documentation remains next.
- 2026-07-22: Completed the documentation and automated-validation portion of S5. A1-A6 and M4 are established by boundary tests, the 778-test full suite, and updated public architecture documentation. Compatibility remains `0.1.3`; direct MCP checks, A7, and S5 remain pending.
- 2026-07-22: Completed S5 after read-only direct MCP discovery, listing, and recall checks. All acceptance criteria now pass; S6 is the only remaining Track step.
- 2026-07-22: Completed TRACK_024. MyMCP now has a generic immutable Tool registry, one startup composition root, and an explicit in-process Mnemosyne integration that owns Tool selection, binding, and lazy service/store composition. Memory handlers receive only narrow typed operations, while every existing public Mnemosyne contract remains unchanged. Final evidence: 778 automated tests passed, whitespace validation passed, and configured-client discovery, bounded listing, and recall checks succeeded on compatibility version `0.1.3`.

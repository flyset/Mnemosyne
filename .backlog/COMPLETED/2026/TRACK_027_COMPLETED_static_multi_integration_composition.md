# TRACK 027 [COMPLETED]: Static multi-integration composition

Track
- ID: TRACK_027
- Repository: MyMCP (hosting the Mnemosyne memory domain in-process)
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_027_COMPLETED_static_multi_integration_composition.md

Problems (PORE)
- P1: As a maintainer evolving MyMCP into a reusable host, I cannot compose more than one in-process domain integration at startup, because the startup root asks Mnemosyne to build the complete Tool registry rather than aggregating host-independent integration contributions.
- P2: As a maintainer preserving host ownership of generic MCP behavior, I cannot treat `list_tools` as host-owned final-surface reporting, because Mnemosyne currently selects, registers, and binds it to the Mnemosyne-only surface.
- P3: As a maintainer adding a future second integration, I cannot verify ordering and collision safety across integration boundaries, because current tests prove duplicate rejection only inside one generic registry input and prove composition only for Mnemosyne.

Objective
- Establish explicit, ordered, static multi-integration Tool composition owned by MyMCP while preserving Mnemosyne's complete public Tool surface and deferring dynamic plugin architecture.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Preserve local-first, single-user, least-privilege, explicit-tool, and per-call consent boundaries.
- Preserve all current public Mnemosyne Tool names, schemas, ordering, gates, results, errors, server identity, configuration, storage compatibility, and argument normalization.
- MyMCP owns final Tool aggregation and `list_tools`; integrations contribute only explicit ordered Tool registrations.
- Keep startup composition fixed for the process lifetime and fail safely before serving if Tool names collide.
- Keep HTTP transport thin and MCP semantics under `mymcp/mcp/`.
- Do not implement dynamic discovery, imports from configured paths, installation, manifests, package loading, lifecycle management, isolation, origin metadata, namespacing, or third-party plugin support.

Acceptance criteria
- [x] A1) [P1] An integration contribution contract supplies an ordered finite sequence of complete `ToolRegistration` values without constructing or mutating the final `ToolRegistry`.
- [x] A2) [P1] The MyMCP startup composition root aggregates a fixed explicitly declared sequence of integration contributions in declaration order and constructs one immutable registry used by discovery and dispatch.
- [x] A3) [P2] MyMCP, not Mnemosyne, registers and binds `list_tools` to the complete final selected Tool surface while preserving `list_tools` as the first public Tool.
- [x] A4) [P1, P3] A test-only second integration proves ordered discovery, `list_tools` visibility, and dispatch through the same composed registry without adding a production Tool.
- [x] A5) [P3] Duplicate Tool names within or across integrations, including an integration attempt to claim `list_tools`, fail deterministically during composition without overwriting a handler or exposing a partial registry.
- [x] A6) [P1, P2] Mnemosyne contributes its currently enabled Tool registrations in the existing order, resolves immutable mutation settings once at startup, and retains lazy per-operation root/service/store construction.
- [x] A7) [P1, P2, P3] Generic composition and registry modules import no Mnemosyne Tool, memory-domain, or configuration package; Mnemosyne-specific selection remains inside its integration boundary.
- [x] A8) [P1, P2, P3] README, architecture, and glossary documentation describe static composition accurately without claiming plugin extraction or changing the public compatibility version solely for this internal work.
- [x] A9) [P1, P2, P3] Focused, full, whitespace, and direct read-only MCP validation pass with unchanged public Mnemosyne behavior.

Why now / impact
- Tracks 023 through 025 established MyMCP host identity, a generic immutable Tool registry, an explicit Mnemosyne integration boundary, and Mnemosyne-owned configuration. The roadmap's next phase is to prove that the host can combine more than one integration before defining Tool identity metadata, packaging, dynamic discovery, or plugin lifecycle behavior.

Scope
- In scope:
  - Define the smallest explicit in-process integration contribution contract over existing `ToolRegistration` values.
  - Add host-owned static aggregation that invokes a fixed declared integration sequence once, preserves contribution order, and constructs one immutable `ToolRegistry`.
  - Move `list_tools` selection and final-surface binding from the Mnemosyne integration to host composition while preserving its public position and output.
  - Change Mnemosyne startup composition from returning a complete registry to returning ordered registrations selected from its startup-fixed settings.
  - Prove composition with a small test-only second integration and no added production Tool.
  - Prove deterministic duplicate rejection across integration boundaries and for the host-reserved `list_tools` name.
  - Preserve the existing registry's schema-aware argument normalization and immutable defensive discovery behavior.
  - Update focused startup, integration, registry, import-boundary, and documentation coverage.
- Out of scope:
  - Dynamic module, filesystem, package, entry-point, manifest, or network discovery.
  - Plugin install, enable, disable, update, removal, health, failure isolation, permissions, resource limits, or secrets/configuration UI.
  - Integration identity or version metadata, compatibility negotiation, public Tool namespaces, aliases, or collision resolution beyond rejecting duplicates.
  - Extracting or separately packaging Mnemosyne.
  - Generalizing approval, audit, storage, memory taxonomy, retrieval, lifecycle, provenance, or content policy.
  - Adding a real second production integration or changing HTTP endpoints.
  - Renaming the public Mnemosyne server, Tools, settings, environment variables, storage paths, or existing data.

Milestones
- [x] M1) Host-owned static aggregation and cross-integration safety are established with synthetic integration tests.
- [x] M2) Mnemosyne contributes ordered registrations and startup uses the generic host composition path without public behavior changes.
- [x] M3) Documentation and complete validation establish the static composition boundary.

Risks / decisions
- Risk: Moving `list_tools` can change its public position, reported surface, server/version text, or relationship to MCP `tools/list`.
- Mitigation: Characterize both discovery paths first and require them to use the same final immutable registry with the existing order and text.
- Risk: Flattening contributions can silently overwrite duplicate handlers or report only part of a surface.
- Mitigation: Reuse `ToolRegistry` duplicate validation at final construction and add focused cross-integration and reserved-name tests.
- Risk: An abstraction intended for static composition can become a premature plugin framework.
- Mitigation: Accept only explicit in-process contributors declared in code; add no metadata, import mechanism, configuration, or lifecycle API.
- Risk: Refactoring Mnemosyne composition can alter settings-read count, mutation gates, or lazy storage behavior.
- Mitigation: Retain and adapt the existing focused settings, gate-order, validation-before-construction, and fresh-operation tests.
- Decision: Existing public Tool names remain unchanged; naming and integration-origin metadata belong to the roadmap's later Tool identity and aggregation-contract phase.
- Decision: A second integration exists only in tests; a real second consumer is still required before generalizing storage or governance services.

Open questions
- [x] Q1) Should the static contribution contract be a zero-argument callable returning a tuple of `ToolRegistration` values, a small immutable protocol object, or a direct iterable declared by startup?
- [x] Q2) Should host composition prepend `list_tools` before invoking integration contributors or bind it after collecting their definitions and prepend only during final registry construction?
- [x] Q3) Should duplicate failures continue using the current `ValueError("duplicate tool registration: <name>")` contract, or should composition introduce a host-specific bounded startup exception before origin metadata exists?
- [x] Q4) Which lower-level Mnemosyne registry-builder helpers remain justified for tests after production composition changes to registration contribution?

Decision log
- Decision (Q1): Use the smallest explicit contract: `ToolIntegration` is a zero-argument callable returning an ordered finite tuple of complete `ToolRegistration` values. Static startup will declare the callables directly; there is no identity object, metadata model, loader, or lifecycle API.
- Decision (Q2): Invoke each declared contributor once in declaration order, collect and snapshot the selected Tool definitions, then prepend and bind host-owned `list_tools` only during final registry construction. This gives `list_tools` the complete final surface without making it part of any integration contribution.
- Decision (Q3): Preserve the existing deterministic `ValueError("duplicate tool registration: <name>")` from final `ToolRegistry` construction. Without origin metadata there is no justified richer collision error, and construction returns no partial registry.
- Decision (Q4): Retain exactly one deterministic lower-level helper, `build_mnemosyne_registrations(...)`, which accepts explicit mutation-gate booleans and returns real ordered Mnemosyne registrations for focused tests. Remove `build_tool_registry()`, `build_startup_tool_registry()`, and their broad synthetic Tool/handler injection seam because they duplicate generic registry coverage and encode obsolete Mnemosyne ownership of final aggregation.

Plan (execution steps)
- [x] S1) Move TRACK_027 to ACTIVE (folder, filename, title, and current path) and check this step before implementation.
- [x] S2) Execute the host-composition TDD chunk: resolve Q1 through Q3; add focused failing tests using two synthetic explicit integrations for ordered aggregation, complete `list_tools` reporting, dispatch, cross-integration duplicates, and the reserved `list_tools` collision; implement the smallest generic static composition boundary; run focused registry/list-tools validation; update this Track.
- [x] S3) Execute the Mnemosyne-contribution TDD chunk: resolve Q4; add focused failing tests requiring Mnemosyne to return ordered registrations without host `list_tools`; migrate startup to the fixed host-owned integration sequence; preserve gate selection, one-time settings resolution, lazy root/service/store construction, discovery, and dispatch; run focused integration/startup/import-boundary validation; update this Track.
- [x] S4) Update README, architecture, and glossary documentation; run the complete automated suite and whitespace validation; perform direct read-only MCP discovery, listing, and recall checks; review all acceptance criteria; record evidence.
- [x] S5) Move TRACK_027 to COMPLETED (folder, filename, title, and current path), check this transition, and record completion outcomes.

Current inventory
- `mymcp/mcp/tool_registry.py` defines frozen `ToolRegistration` and immutable `ToolRegistry`. The registry preserves registration order, snapshots Tool definitions, rejects duplicate names with `ValueError`, and owns schema-aware dispatch without importing Mnemosyne packages.
- `mymcp/mcp/composition.py` now defines the minimal zero-argument `ToolIntegration` callable contract and `compose_tool_registry()`. It invokes explicit contributors once in order, snapshots the complete selected surface, prepends host-owned `list_tools`, and delegates immutable construction and duplicate rejection to `ToolRegistry` without importing Mnemosyne packages.
- `mymcp/mcp/startup.py` now declares the fixed production sequence `(mnemosyne_integration,)` and passes it to host-owned `compose_tool_registry()` once. It imports no Mnemosyne configuration, memory domain, or Tool package and exposes the same one immutable `REGISTRY` to methods.
- `mymcp/mcp/integrations/mnemosyne.py` now exposes `mnemosyne_integration()` as the zero-argument production contributor and `build_mnemosyne_registrations(...)` as the one deterministic lower-level gate-selection helper. It contributes real ordered memory registrations without `list_tools` or `ToolRegistry`, resolves mutation settings once per production contribution, and retains all narrow handlers plus lazy per-operation root/store/service construction.
- `mymcp/mcp/tools/list_tools/__init__.py` remains host-generic and unchanged; final selection and complete-surface binding now occur only in host composition.
- `mymcp/mcp/methods.py` uses the one startup `REGISTRY` for MCP `tools/list` and `tools/call`; this should remain unchanged unless focused evidence requires a smaller adaptation.
- `tests/mcp/test_tool_registry.py` already proves order, defensive discovery, duplicate rejection within one input sequence, unknown-Tool handling, and argument normalization.
- `tests/mcp/test_mnemosyne_integration.py` now proves raw Mnemosyne contributions are complete ordered `ToolRegistration` tuples without `list_tools`, production settings resolve once, host composition preserves every gate/order combination and complete-surface `list_tools`, startup/methods share one registry, and lazy/fresh service operation behavior remains unchanged.
- `tests/mcp/test_registry.py` now builds real gate-selected Mnemosyne contributions through host composition for dispatch and compatibility coverage. Obsolete synthetic Mnemosyne registry-builder and incomplete-injection tests were removed; the one remaining synthetic revise-schema normalization test constructs generic `ToolRegistry`/`ToolRegistration` directly at its actual ownership boundary.
- `tests/mcp/test_startup_settings.py` protects startup-fixed Tool availability, independent mutation gates, one settings-file read, restart behavior, no read-path initialization, and public discovery/dispatch through isolated subprocesses.
- `tests/mcp/test_list_tools.py` protects supplied-name formatting and compatibility version `0.1.3`.
- `tests/mcp/test_integration_composition.py` uses two synthetic zero-argument integrations to prove contribution call order, final Tool order, dispatch, complete `list_tools` reporting, cross-integration duplicate rejection, and rejection of an integration attempting to claim host-owned `list_tools`. It adds no production Tool.
- `README.md` now explains fixed ordered in-process integrations, host-owned final aggregation and `list_tools`, duplicate rejection, Mnemosyne-only production composition, and the test-only second integration without claiming dynamic plugins.
- `docs/ARCHITECTURE.md` now inventories and defines `composition.py`, separates static aggregation from immutable registry mechanics and startup declaration, and documents Mnemosyne registration contribution without final-registry ownership.
- `docs/GLOSSARY.md` now defines Tool integration and static integration composition and aligns startup-registry and Mnemosyne-integration terms with current ownership.
- No production second integration, integration metadata model, plugin package contract, dynamic loader, or Tool namespace exists.
- TRACK_026 remains a separate DRAFT for compact-token false-positive correction and is not part of this work.
- The worktree already contains a separate modified `MEMORY.md` and untracked TRACK_026; this Track must not overwrite or absorb those changes.

Artifacts
- Project-memory roadmap: `Overall roadmap for MyMCP and Mnemosyne`, Phase 1 — Static multi-integration composition.
- Prerequisite Track: `.backlog/COMPLETED/2026/TRACK_023_COMPLETED_mymcp_project_identity.md`.
- Prerequisite Track: `.backlog/COMPLETED/2026/TRACK_024_COMPLETED_mnemosyne_integration_boundary.md`.
- Prerequisite Track: `.backlog/COMPLETED/2026/TRACK_025_COMPLETED_mnemosyne_configuration_ownership.md`.
- S2 red evidence: `python -m pytest tests/mcp/test_integration_composition.py` collected no tests and failed during collection with `ModuleNotFoundError: No module named 'mymcp.mcp.composition'` before production implementation.
- S2 focused green evidence: the same command passed all 3 composition tests after the minimal implementation.
- S2 regression evidence: `python -m pytest tests/mcp/test_integration_composition.py tests/mcp/test_tool_registry.py tests/mcp/test_list_tools.py` passed all 11 tests; `git diff --check` passed with no output.
- S3 red evidence: the three focused contribution/startup tests collected successfully and all 3 failed before production changes: the two registration-contribution symbols were absent and startup did not import host composition.
- S3 focused green evidence: the same three tests passed after the minimal Mnemosyne-contribution and startup-composition migration.
- S3 primary regression evidence: `python -m pytest tests/mcp/test_mnemosyne_integration.py tests/mcp/test_registry.py tests/mcp/test_integration_composition.py tests/memory/test_import_boundaries.py` passed all 60 tests.
- S3 startup regression evidence: `python -m pytest tests/mcp/test_startup_settings.py tests/mcp/test_tool_registry.py tests/mcp/test_list_tools.py tests/mcp/test_methods.py tests/routes/test_mcp.py` passed all 51 tests.
- S3 broad MCP evidence: `python -m pytest tests/mcp tests/routes/test_mcp.py tests/memory/test_import_boundaries.py` passed all 402 tests; `git diff --check` passed with no output.
- S4 complete automated evidence: `python -m pytest` collected and passed all 761 tests in 7.50 seconds.
- S4 whitespace evidence: `git diff --check` passed with no output after documentation updates.
- S4 direct MCP discovery evidence: configured-client `list_tools` reported `mnemosyne 0.1.3` with the expected ordered nine-Tool enabled surface from `list_tools` through `memory_forget`.
- S4 direct MCP listing evidence: bounded project-namespace listing returned `status: ok`, 5 items of 31 total, an authenticated continuation cursor, and compact metadata without record content.
- S4 direct MCP recall evidence: bounded roadmap/architecture recall returned the living roadmap as the leading result with Phase 1 static composition and Phase 2 Tool identity sequencing intact.
- S4 acceptance review: A1-A9 and M1-M3 pass. Public Mnemosyne Tool names, ordering, schemas, gates, results, errors, server identity, configuration, storage, and compatibility version `0.1.3` remain unchanged; no dynamic discovery, production second integration, namespacing, installation, lifecycle, or isolation capability was added.
- Roadmap reconciliation: inspected living roadmap `Overall roadmap for MyMCP and Mnemosyne` at revision 1 during S4, then revised it under explicit user approval after the completion transition. Revision 2 records Phase 1 as delivered by TRACK_027, adds static composition to the delivered baseline, and identifies Phase 2 Tool identity and aggregation contract as the next major step.

Completion notes
- 2026-07-23: Track moved to ACTIVE after user review. S2 host composition is the next TDD chunk.
- 2026-07-23: Completed S2. MyMCP now has a generic static composition boundary over explicit zero-argument integration contributors, host-owned complete-surface `list_tools` binding, and deterministic final-registry collision rejection. Synthetic second-integration coverage passed without adding a production Tool. Startup still uses the existing Mnemosyne-built registry; S3 is the next TDD chunk.
- 2026-07-23: Completed S3. Mnemosyne now contributes ordered real Tool registrations without constructing the final registry or owning `list_tools`; host startup composes the fixed explicit Mnemosyne sequence through the generic boundary. Existing gate order, one-time settings resolution, lazy/fresh service construction, discovery, dispatch, and argument normalization remain green. S4 documentation, complete validation, direct read-only MCP checks, acceptance review, and roadmap reconciliation are next.
- 2026-07-23: Completed S4. README, architecture, and glossary documentation now describe the static integration contract and ownership boundaries. All 761 automated tests, whitespace validation, and configured-client read-only discovery/listing/recall checks passed on compatibility version `0.1.3`; every acceptance criterion and milestone is satisfied. The roadmap was inspected and needs an approval-gated post-completion revision to mark Phase 1 delivered and Phase 2 next. S5 completion transition is the only remaining Track step.
- 2026-07-23: Completed TRACK_027. MyMCP now owns explicit ordered static integration aggregation, complete-surface `list_tools`, immutable final registry construction, and deterministic duplicate rejection. Mnemosyne contributes only its startup-selected ordered registrations while retaining one-time settings resolution and lazy per-operation service/store construction. A test-only second integration proves multi-integration ordering, reporting, dispatch, and collision safety without adding dynamic discovery or a production plugin. Final evidence is 761 passing automated tests, whitespace validation, and configured-client read-only discovery/listing/recall checks on compatibility version `0.1.3`. The living roadmap was subsequently revised under explicit user approval to revision 2, recording Phase 1 as delivered and Phase 2 as next; no commit or push was performed.

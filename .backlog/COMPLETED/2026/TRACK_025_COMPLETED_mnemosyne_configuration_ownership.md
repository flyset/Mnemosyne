# TRACK 025 [COMPLETED]: Mnemosyne configuration ownership

Track
- ID: TRACK_025
- Repository: MyMCP (hosting the Mnemosyne memory domain in-process)
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_025_COMPLETED_mnemosyne_configuration_ownership.md

Problems (PORE)
- P1: As a maintainer evolving MyMCP into a reusable host, I cannot treat `mymcp/settings.py` as a host-owned settings boundary, because it combines server/protocol identity with Mnemosyne memory-root resolution, mutation enablement, and strict local-file parsing.
- P2: As a maintainer of the in-process Mnemosyne integration, its configuration ownership is incomplete, because `mymcp/mcp/startup.py` resolves Mnemosyne settings and passes them into the integration while the integration separately imports the memory-root resolver from host settings.
- P3: As an existing Mnemosyne user, I risk configuration or storage regressions during ownership separation, because environment precedence, strict TOML validation, bounded errors, filesystem safety checks, startup-fixed gates, and the existing `~/.mnemosyne` data path form one compatibility-sensitive contract.

Objective
- Establish an explicit Mnemosyne-owned configuration boundary while leaving `mymcp/settings.py` focused on retained server/process identity and preserving every current public configuration, startup, and storage behavior.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Preserve local-first, single-user, least-privilege, explicit-tool, and per-call consent boundaries.
- Preserve `SERVER_NAME = "mnemosyne"`, the current protocol/package compatibility version, all `MNEMOSYNE_*` variable names, `~/.mnemosyne/config.toml`, `~/.mnemosyne/memory`, the strict TOML schema, source-size and permission checks, environment precedence, stable bounded failures, and disabled defaults.
- Preserve one startup settings resolution, startup-fixed Tool availability, lazy memory-root use, and the rule that configuration reads never initialize or mutate paths.
- Keep HTTP transport thin, generic MCP registry/dispatch independent of Mnemosyne settings, and the memory domain independent of MCP, FastAPI, and routes.
- Do not claim or implement plugin extraction, dynamic configuration discovery, manifests, settings UI, secret storage, Tool renaming/namespacing, or configuration migration.

Acceptance criteria
- [x] A1) [P1] `mymcp/settings.py` contains retained server/process identity and protocol constants but no Mnemosyne memory-root, mutation-gate, environment, local-file, or memory-settings model ownership.
- [x] A2) [P2, P3] One explicit Mnemosyne-owned configuration module exposes the memory root and immutable mutation settings required by the in-process integration without importing MCP Tool packages, FastAPI, or routes.
- [x] A3) [P2] The Mnemosyne integration owns resolution of its configuration and supplies the composed startup registry without generic registry or MCP method code importing Mnemosyne configuration details.
- [x] A4) [P3] All existing `MNEMOSYNE_*` overrides, strict `~/.mnemosyne/config.toml` behavior, defaults, validation order, bounded messages, source limits, path/permission checks, and at-most-once startup file read remain unchanged.
- [x] A5) [P3] Startup and read-only operations still create no configuration or memory paths; enabled valid remember remains the only lazy first-run memory-root initializer.
- [x] A6) [P1, P2, P3] README, architecture, and glossary documentation accurately describe configuration ownership without claiming plugin extraction or changing public setup guidance.
- [x] A7) [P1, P2, P3] Focused, full, whitespace, and direct MCP validation pass with unchanged public Tool discovery and behavior.

Why now / impact
- Track 024 completed the generic Tool-registry, startup-composition, integration-binding, and service-construction seams. Mnemosyne configuration in `mymcp/settings.py` is the remaining mixed seam identified by the incremental host-separation plan, and separating it now reduces host/domain coupling before any plugin or multi-integration contract is considered.

Scope
- In scope:
  - Characterize the current host-versus-Mnemosyne settings ownership and all compatibility-sensitive configuration behavior.
  - Select one explicit Mnemosyne-owned home for memory-root and mutation-gate configuration.
  - Move `MemoryToolSettings`, memory environment constants, root resolution, strict fixed-file parsing, source safety checks, and matching helper functions behind that boundary.
  - Keep retained server identity, package/protocol version, application title, and other host/process constants in `mymcp/settings.py`.
  - Make the Mnemosyne integration resolve its own configuration while preserving a single startup-fixed composition.
  - Update internal imports and tests without retaining a second compatibility facade unless a demonstrated internal consumer requires one.
  - Add focused configuration ownership, import-boundary, startup-read, environment/file precedence, no-initialization, and direct MCP coverage.
  - Update affected README, architecture, and glossary documentation.
- Out of scope:
  - Changing any environment variable, settings path, file key, default, error message, permission rule, source limit, or data path.
  - Splitting or migrating the existing `~/.mnemosyne/config.toml` document.
  - Adding host-generic plugin configuration, manifests, secrets, credentials, encryption, settings UI, reload/watch behavior, or runtime mutation.
  - Plugin discovery, installation, isolation, aggregation, Tool namespacing, or a second integration.
  - Moving or generalizing memory schemas, scopes, kinds, retrieval, persistence, lifecycle, consent, or content policy.
  - Renaming the public Mnemosyne server or changing the compatibility version solely for this internal refactor.

Milestones
- [x] M1) Configuration ownership and compatibility contracts are characterized by focused tests.
- [x] M2) Mnemosyne-specific configuration has one explicit owner outside host settings.
- [x] M3) Integration/startup composition consumes the new boundary without behavior changes.
- [x] M4) Documentation and complete validation establish the configuration seam.

Risks / decisions
- Risk: Moving parsing code can alter environment-before-file precedence, validation order, file-read count, or bounded failure text.
- Mitigation: Characterize those contracts before extraction and move behavior mechanically before refactoring names or structure.
- Risk: Moving root resolution can capture the root at startup and break per-call environment/test isolation or lazy initialization.
- Mitigation: Keep root resolution callable and operation-time; add explicit late-root and no-path-creation tests.
- Risk: Placing operator configuration inside the tool-independent memory domain may mix deployment concerns with memory semantics.
- Mitigation: Decide placement from dependency direction before implementation and enforce it with import-boundary tests.
- Risk: A new Mnemosyne package may be mistaken for completed plugin extraction.
- Mitigation: Document the boundary as in-process configuration ownership only; add no loading, manifest, lifecycle, or public naming contract.
- Decision: Public configuration and storage identities remain unchanged; this Track changes ownership, not behavior.
- Decision: No compatibility facade is assumed. Add one only if repository-wide inventory identifies a concrete internal consumer that cannot move atomically.

Open questions
- [x] Q1) Should Mnemosyne configuration live beside the tool-independent memory domain, beside the MCP integration, or in a new in-process Mnemosyne package boundary?
- [x] Q2) Should `mymcp/mcp/startup.py` call a configured Mnemosyne composition entrypoint with no memory-settings arguments, or should a narrower host composition object supply integration configuration explicitly?
- [x] Q3) Which settings symbols, if any, are genuinely host/process concerns beyond `SERVER_NAME`, `SERVER_VERSION`, `PROTOCOL_VERSION`, and `APP_TITLE`?

Decision log
- Decision (Q1): Place operator-facing memory configuration in `mymcp/mnemosyne/configuration.py`, under a small explicit in-process Mnemosyne ownership package. Configuration is not tool-independent memory meaning, so it does not belong in `mymcp/memory/`; it is also not MCP composition, so it does not belong under the integration module. This package boundary is not plugin extraction, discovery, or a public plugin contract.
- Decision (Q2): The host startup root calls a zero-argument `compose_mnemosyne_registry()`. The Mnemosyne integration resolves its own immutable mutation settings exactly once for registry selection, while operation calls continue to resolve the memory root lazily. Explicit lower-level registry builders remain available for focused in-process tests; the host supplies no Mnemosyne configuration object.
- Decision (Q3): Only `SERVER_NAME`, `SERVER_VERSION`, `PROTOCOL_VERSION`, and `APP_TITLE` remain in host `mymcp/settings.py`. Every memory root, environment gate, file location, parser, source-safety rule, settings model, bounded settings error, and convenience resolver is Mnemosyne configuration.

Plan (execution steps)
- [x] S1) Move TRACK_025 to ACTIVE (folder, filename, title, and current path) and check this step before implementation.
- [x] S2) Execute the configuration-characterization TDD chunk: add focused failing ownership/import-boundary tests and strengthen exact compatibility tests for environment precedence, strict file parsing, bounded failures, at-most-once startup reads, late root resolution, and no path initialization; make only the smallest test-support changes if required; run focused validation; update this Track.
- [x] S3) Execute the configuration-extraction TDD chunk: resolve Q1 and Q3, move Mnemosyne memory configuration to its selected owner without semantic changes, update direct internal consumers and tests, remove obsolete host ownership, run focused settings/import-boundary validation, and update this Track.
- [x] S4) Execute the integration-composition TDD chunk: resolve Q2, make the Mnemosyne integration consume its configuration boundary while generic startup/registry/method code remains free of Mnemosyne configuration details, preserve startup-fixed and operation-time root behavior, run focused integration/startup validation, and update this Track.
- [x] S5) Update package-boundary documentation, run the complete automated suite and whitespace validation, perform direct MCP discovery/read checks, review all acceptance criteria, and record evidence.
- [x] S6) Move TRACK_025 to COMPLETED (folder, filename, title, and current path), check this transition, and record completion outcomes.

Current inventory
- `mymcp/settings.py` now owns only retained public server/process identity: `SERVER_NAME`, `SERVER_VERSION`, `PROTOCOL_VERSION`, and `APP_TITLE`.
- `mymcp/mnemosyne/configuration.py` now exclusively owns `MemoryToolSettings`, all five `MNEMOSYNE_*` environment names, fixed `.mnemosyne/config.toml` names, the 16 KiB source limit, root resolution, strict TOML parsing, permission/path checks, environment precedence, bounded settings errors, and convenience gate helpers. The implementation moved mechanically without semantic changes and imports no MCP, FastAPI, or route package.
- `mymcp/mcp/startup.py` now imports only the Mnemosyne composition entrypoint and calls zero-argument `compose_mnemosyne_registry()` once; it imports no Mnemosyne configuration, Tool package, or memory domain.
- `mymcp/mcp/integrations/mnemosyne.py` now imports `get_memory_tool_settings()` and `get_memory_root()` from the Mnemosyne configuration owner. Composition resolves immutable mutation settings exactly once to select the startup Tool surface, while each validated operation still resolves the root lazily and constructs a fresh store/service.
- `mymcp/mcp/methods.py` and `mymcp/mcp/tools/list_tools/` use only retained server/protocol identity constants from `mymcp.settings` and should remain independent of memory configuration.
- `tests/test_mnemosyne_configuration.py` is the renamed primary strict unit contract for root resolution, environment/file precedence, schema validation, source limits, permissions, stable messages, and file-read behavior; it also fixes the environment-validation order before any file access and proves invalid values are not echoed.
- `tests/mcp/test_startup_settings.py` uses isolated subprocess probes to protect startup-fixed discovery/dispatch, independent gates, environment overrides, failure-before-file-access, no path initialization, and restart semantics.
- `tests/mcp/test_startup_settings.py` now directly counts settings-file opens before importing MyMCP and proves one startup read serves repeated discovery calls without initializing the memory root.
- `tests/mcp/test_mnemosyne_integration.py` now proves zero-argument composition resolves settings exactly once inside the integration, startup owns neither memory configuration nor Tools, lower-level explicit settings preserve all ordered gate combinations, the configured root is resolved afresh for each valid operation after registry composition, and read-only listing creates neither late-selected root.
- Memory Tool tests now import `get_memory_root()` from `mymcp.mnemosyne.configuration` only to construct explicit test-owned services; production handlers remain configuration-independent.
- `tests/memory/test_import_boundaries.py` now fixes the exact four-symbol host settings owner, requires the explicit Mnemosyne configuration owner, forbids MCP/FastAPI/route imports from it, forbids host or Mnemosyne configuration imports from the shared memory domain and Tool handlers, and forbids memory-configuration ownership in generic registry/method code.
- `README.md` now explains host-only identity settings, Mnemosyne-owned configuration, integration-owned one-time mutation settings resolution, lazy operation-time root resolution, and preserved public setup/contracts without claiming plugin extraction.
- `docs/ARCHITECTURE.md` now inventories `mymcp/mnemosyne/configuration.py`, separates host settings/configuration/integration/startup responsibilities, and documents unchanged strict parsing, startup-fixed gates, and lazy storage initialization.
- `docs/GLOSSARY.md` now defines the Mnemosyne configuration boundary and updates startup-registry and integration-layer terms for zero-argument composition and integration-owned resolution.
- TRACK_024 completed and was pushed in commit `4694d2d`, establishing the prerequisite generic registry and in-process Mnemosyne integration boundary.

Artifacts
- Project-memory idea: `Idea: incremental host separation within Mnemosyne`.
- Project-memory ideation: `MyMCP — self-hostable MCP plugin host (project ideation)`.
- Prerequisite Track: `.backlog/COMPLETED/2026/TRACK_024_COMPLETED_mnemosyne_integration_boundary.md`.
- Prerequisite commit: `4694d2d` (`Add Mnemosyne integration boundary`).

Completion notes
- 2026-07-23: Track moved to ACTIVE before implementation. S2 configuration characterization is the next TDD chunk.
- 2026-07-23: Completed S2 without production changes. The first focused run collected 150 tests and produced one failure (`149 passed`) because the startup-read probe imported `mymcp.settings` only after package initialization had already composed the registry, so its internal read hook observed zero opens. The smallest test-support correction counted `config.toml` opens before importing MyMCP. The focused settings/startup/integration/import-boundary suite then passed all 150 tests, and `git diff --check` passed. Existing strict TOML, bounded-error, precedence, source-safety, and no-initialization coverage remains green; new coverage fixes environment validation order, one startup file read, operation-time root resolution, and generic/domain import boundaries. S3 configuration extraction is next.
- 2026-07-23: Completed S3. The focused ownership test first failed because `mymcp/mnemosyne/configuration.py` did not exist. The memory configuration implementation then moved mechanically to that explicit in-process owner, host settings were reduced to exactly four identity constants, and all production/test consumers moved without a compatibility facade. The initial configuration/integration/startup/import-boundary green run passed 151 tests; the broader focused run passed 425 configuration, boundary, startup, integration, memory-Tool, identity, and operational tests. `git diff --check` passed, old memory imports from `mymcp.settings` are absent, and no public name, path, default, parser, error, gate, or storage behavior changed. S4 integration-owned configuration composition is next.
- 2026-07-23: Completed S4. The focused test first failed because `compose_mnemosyne_registry` still required a host-supplied `MemoryToolSettings` argument. The smallest implementation made composition zero-argument, moved the single startup settings resolution into the Mnemosyne integration, and removed Mnemosyne configuration from host startup. Integration tests were then refactored to use explicit lower-level builders where they intentionally select gate combinations. Focused integration/startup/import-boundary/registry/method/route validation passed 132 tests; broad MCP, memory-domain, and MCP-route validation passed 687 tests. `git diff --check` passed. Startup-fixed Tool selection, one settings-file read, lazy operation-time root resolution, no read-path initialization, and all public Tool behavior remain unchanged. S5 documentation and complete validation are next.
- 2026-07-23: Completed S5 documentation and validation. Updated `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` for host-only settings, the in-process Mnemosyne configuration owner, zero-argument startup composition, and integration-owned settings/root resolution without claiming plugin extraction. The complete automated suite passed all 784 tests in 7.43 seconds. `git diff --check` and explicit trailing-whitespace/final-newline checks for untracked Track, package, configuration, and test files passed. Configured-client direct checks reported `mnemosyne 0.1.3` with the expected ordered nine-Tool enabled surface; bounded project-namespace listing returned five items of 29 with no content; bounded project recall returned the existing incremental host-separation context. No mutation Tool was called. Final acceptance review confirms A1-A7: public variables, paths, strict parsing, bounded failures, startup-fixed gates, lazy initialization, Tool contracts, and compatibility version remain unchanged. S6 completion transition is next.
- 2026-07-23: Completed TRACK_025. MyMCP host settings now contain only server/process identity, while `mymcp/mnemosyne/configuration.py` explicitly owns the unchanged Mnemosyne root, environment, strict file, safety, and mutation-settings contracts. The zero-argument Mnemosyne integration resolves immutable startup settings once and continues to resolve the root lazily per validated operation. All 784 automated tests, whitespace checks, and configured-client discovery/listing/recall checks passed on compatibility version `0.1.3`; no plugin extraction, migration, public contract change, commit, or push was performed.

# TRACK 029 [COMPLETED]: Plugin target architecture

Track
- ID: TRACK_029
- Repository: MyMCP
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_029_COMPLETED_plugin_target_architecture.md

Problems (PORE)
- P1: As a maintainer implementing the MyMCP roadmap, I cannot determine whether a minimal change advances the intended product architecture, because the roadmap defines product phases without a concrete target package, plugin, manifest, identity, and dependency design.
- P2: As a future plugin author, I cannot implement against a stable MyMCP boundary, because the current anonymous `ToolIntegration` callable has no plugin identity, version, manifest, Tool-origin metadata, compatibility contract, or public-name binding model.
- P3: As the maintainer of the built-in Mnemosyne domain, I cannot treat it as one coherent plugin implementation, because its configuration, memory domain, MCP adapters, and integration composition are spread across `mymcp/mnemosyne/`, `mymcp/memory/`, `mymcp/mcp/tools/`, and `mymcp/mcp/integrations/`.
- P4: As a user relying on existing Mnemosyne behavior, I risk an architectural extraction changing public Tools, configuration, storage, consent, or record compatibility unless those invariants are explicit before implementation begins.

Objective
- Establish and approve a concrete target architecture that aligns every roadmap phase toward MyMCP as a generic host and Mnemosyne as its first vertically owned built-in plugin, without implementing plugin extraction in this Track.

Non-negotiables
- This Track defines architecture and roadmap alignment; it does not implement plugin contracts, move runtime code, add dynamic loading, or extract Mnemosyne.
- Any later behavior implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Preserve local-first operation, the single-user model, least privilege, explicit Tools, filesystem truth, startup failure safety, operator gates, and per-call user consent.
- Preserve Mnemosyne's current public server identity, `memory_*` Tool names and contracts, `MNEMOSYNE_*` configuration, `~/.mnemosyne` paths, memory record formats, and existing data unless a separately approved compatibility migration changes them.
- Keep HTTP transport thin and generic MCP semantics under host-owned MCP packages.
- Keep Mnemosyne taxonomy, storage, retrieval, lifecycle, refusal policy, configuration, and Tool behavior owned by Mnemosyne rather than generalized into the host.
- Do not claim that an in-process manifest provides operating-system isolation or proves client approval.
- Do not introduce shell execution, unrestricted filesystem access, secret storage, arbitrary import paths, or dynamic third-party code discovery.
- Every minimal implementation Track derived from this architecture must move toward the declared target and must not create a second canonical implementation or a throwaway boundary.

Acceptance criteria
- [x] A1) [P1] One durable architecture document defines the target layers, package tree, ownership rules, dependency direction, static bootstrap, compatibility boundaries, security limitations, and phased migration.
- [x] A2) [P2] The architecture defines stable plugin identity, plugin version, host plugin-API compatibility, qualified Tool identity, Tool origin, effect/consent classification, endpoint-visible name binding, and collision behavior.
- [x] A3) [P2] The architecture defines a strict versioned plugin manifest with explicit responsibilities and non-responsibilities, without duplicating complete Tool schemas or enabling dynamic loading.
- [x] A4) [P3] The target places all Mnemosyne production implementation and policy beneath one coherent boundary such as `mymcp/plugins/mnemosyne/`, while allowing repository documentation, tests, host bootstrap references, and compatibility bindings to remain outside it.
- [x] A5) [P1, P3] The architecture distinguishes generic host protocol/runtime/plugin contracts from concrete bundled plugins and defines import rules that can be enforced by automated boundary tests.
- [x] A6) [P4] The architecture explicitly preserves the current observable Mnemosyne MCP, configuration, storage, record, startup-gate, consent, and client compatibility contracts during structural migration.
- [x] A7) [P1, P2, P3, P4] `VISION.md`, `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` consistently summarize and link the approved target without describing unimplemented capabilities as current behavior.
- [x] A8) [P1] The living MyMCP roadmap is inspected and, under separate user approval, revised so its phases explicitly deliver the target architecture rather than defer architectural direction to later refactoring.
- [x] A9) [P1, P2, P3, P4] Documentation, link, whitespace, applicable automated, and direct read-only MCP validation pass, and no runtime behavior changes in this Track.

Why now / impact
- The active roadmap identifies plugin-author contract and Tool identity as the next phase, but it does not currently commit to a concrete plugin package, manifest, vertical Mnemosyne ownership boundary, or stable identity model. Implementing Phase 1 without that target would allow locally minimal choices that require architectural reversal later.

Scope
- In scope:
  - Define the architectural end state for MyMCP host, plugin contract, bundled plugins, and Mnemosyne ownership.
  - Define the target package tree and enforceable import/dependency rules.
  - Define the conceptual plugin manifest and runtime contribution contracts.
  - Separate plugin identity, qualified Tool identity, and endpoint-visible Tool names.
  - Define static built-in bootstrap as the first implementation mode and dynamic lifecycle/isolation as later phases.
  - Define public compatibility invariants and the treatment of internal Python import paths during migration.
  - Map roadmap phases and future Tracks to incremental steps that all converge on the target.
  - Update durable architecture, vision, orientation, glossary, and roadmap material after review.
- Out of scope:
  - Runtime plugin-contract implementation, manifest parsing, package relocation, import changes, or compatibility shims.
  - Dynamic discovery, Python entry-point loading, configured import paths, installation, enable/disable, update, removal, health, marketplace behavior, or third-party execution.
  - Process isolation, sandboxing, resource limits, network policy, or multi-user security claims.
  - Renaming existing public Mnemosyne Tools, endpoint/server identity, environment variables, settings files, storage paths, or memory data.
  - Generalizing Mnemosyne storage, taxonomy, consent, audit, retrieval, lifecycle, or content policy into host services.
  - Resolving the separate compact-token false-positive correction in TRACK_026.

Milestones
- [x] M1) Current ownership, coupling, compatibility, and migration hazards are recorded.
- [x] M2) The target package, plugin, manifest, identity, runtime, and dependency architecture is approved.
- [x] M3) The product vision, current architecture documentation, glossary, and living roadmap align with the target while remaining honest about current implementation.
- [x] M4) Derived roadmap phases and Track boundaries provide an incremental path from the current static integration seam to the target architecture.

Risks / decisions
- Risk: Treating `manifest.json` as executable discovery configuration could prematurely create an arbitrary code-loading boundary.
- Mitigation: The initial manifest is descriptive and strictly validated; host bootstrap imports built-in plugin factories explicitly in source code.
- Risk: Copying Mnemosyne modules during relocation could split dataclass identity, cursor codecs, mutation locks, or sources of truth.
- Mitigation: Future relocation Tracks move one canonical implementation at a time, update imports, and delete the old implementation; any temporary compatibility module may only re-export canonical objects.
- Risk: A manifest permission declaration could be mistaken for sandbox enforcement.
- Mitigation: Distinguish Tool effect and consent metadata from operating-system isolation, and defer isolation claims until a threat model and enforceable boundary exist.
- Risk: Moving internal modules could accidentally change public MCP, client permission, configuration, or persisted-data behavior.
- Mitigation: Define compatibility by observable contracts and require schema, gate-matrix, storage, direct MCP, and existing-data validation in every extraction Track.
- Risk: Over-specifying future dynamic packaging now could constrain lifecycle work without evidence.
- Mitigation: Stabilize identity, contribution, manifest, and static built-in contracts first; leave external package discovery and lifecycle transport to their roadmap phase.
- Decision: Use `mymcp/plugin/` for generic host plugin contracts and `mymcp/plugins/` for concrete bundled plugin implementations. The singular package is the host-owned author contract; the plural package contains source-controlled built-ins.
- Decision: Place all Mnemosyne production implementation and policy under `mymcp/plugins/mnemosyne/`, including configuration, the memory domain, MCP Tool adapters, and plugin composition. Repository documentation, tests, explicit host bootstrap references, and compatibility bindings remain outside that implementation boundary.
- Decision: Retain host-owned HTTP transport, transport-neutral MCP protocol/registry/dispatch, complete-surface `list_tools`, immutable runtime composition, and explicit built-in bootstrap outside concrete plugins.
- Decision: Keep the initial plugin mode static and in-process; a packaged manifest describes and validates Mnemosyne but does not dynamically load it.

Open questions
- [x] Q1) Should the generic host plugin contract live at `mymcp/plugin/`, `mymcp/host/plugins/`, or another single clearly host-owned package?
- [x] Q2) Should the immutable composed runtime be introduced as an explicit `HostRuntime` in the target, or should the existing registry remain the runtime boundary until gateway policy requires more state?
- [x] Q3) Which manifest fields are essential in schema version 1 beyond plugin identity/version, host-API range, Tool IDs, effect classification, and consent requirement?
- [x] Q4) Should endpoint-visible Tool names be declared in host bindings, requested by manifests and approved by the host, or derived by one host naming policy with explicit Mnemosyne compatibility aliases?
- [x] Q5) Which current internal Python import paths require temporary re-export compatibility, if any, versus an atomic repository-internal migration?
- [x] Q6) Should the final target retain the name `domain/` or `memory/` inside `mymcp/plugins/mnemosyne/`?
- [x] Q7) Which architectural invariants need new automated dependency and manifest-contract tests when implementation Tracks begin?

Decision log
- Decision: The project will use architectural minimalism: each smallest step must implement part of a declared end-state architecture rather than create an intentionally temporary structure for unspecified later refactoring.
- Decision: The target architecture will make Mnemosyne a vertically owned built-in plugin and will not treat its memory semantics as generic host infrastructure.
- Decision: Plugin identity and plugin-local Tool identity are distinct from endpoint-visible MCP Tool names so current Mnemosyne names can remain compatible while future naming policy evolves.
- Decision: The architecture document will distinguish current implementation, committed target, and deferred capabilities; it will not describe plugin extraction or dynamic loading as already implemented.
- Decision (Q1): Use `mymcp/plugin/` for stable host-owned plugin contracts, manifest parsing, and generic plugin composition. Use `mymcp/plugins/` only for concrete bundled implementations. This makes the author API distinct from the collection of built-ins without introducing a broader `host/plugins/` hierarchy.
- Decision (Q2): The target includes immutable `mymcp/host/runtime.py` and explicit `mymcp/host/bootstrap.py`. `HostRuntime` holds the composed Tool registry plus bounded plugin, qualified-identity, effect, consent, and public-binding metadata needed by later gateway policy. Bootstrap is the only generic-host location allowed to import concrete built-ins. Ordinary `mymcp` package imports must not compose the runtime as a side effect.
- Decision (Q3): Manifest schema version 1 requires `manifest_version`, `id`, `title`, `description`, `version`, `requires.host_api.min`, `requires.host_api.max`, and a complete `tools` array. Every Tool entry requires plugin-local `id`, explicit boolean `read_only`, `destructive`, `idempotent`, and `open_world` dimensions, plus `consent` limited to `none` or `per_call`. Optional `$schema` supports authoring. Full Tool schemas/descriptions, public names, executable imports, commands, arguments, environment values, secrets, runtime enablement, installation, health, permissions, and isolation metadata are excluded.
- Decision (Q4): Endpoint-visible Tool names are host-owned explicit bindings. Manifests declare plugin-local Tool IDs only; the runtime retains qualified `(plugin_id, tool_id)` origin. Mnemosyne's current `memory_*` endpoint names remain canonical bindings rather than aliases. A future default namespacing rule requires evidence from another plugin and does not add duplicate public aliases.
- Decision (Q5): No current internal Python module path is a documented supported external API, so extraction should migrate repository imports to one canonical implementation without permanent shims. If coherent TDD chunks temporarily require an old path, it may only re-export canonical objects, must not duplicate class/singleton identity, and must be removed within the extraction phase.
- Decision (Q6): Use `mymcp/plugins/mnemosyne/memory/`. `memory` states the concrete domain, preserves recognizable module ownership, and avoids a generic `domain` catch-all inside a single-domain plugin.
- Decision (Q7): Later implementation Tracks require automated tests for strict manifest shape/bounds and unknown-field rejection; manifest/contribution inventory parity; selected-registration subset validation; host-API compatibility; duplicate plugin, local Tool, qualified Tool, and public-name rejection; host-reserved names; explicit static bootstrap; one immutable runtime; dependency direction; absence of Mnemosyne implementation outside its plugin boundary; transport-neutral MCP semantics; and unchanged public Mnemosyne discovery, schemas, gates, results, errors, configuration, storage, and existing-data behavior.
- Decision: MCPB and MCP Registry metadata describe whole independently installable or discoverable MCP servers and are not the MyMCP in-process plugin contract. Reuse their separation of machine identity, display metadata, versions, and compatibility concepts without adopting their package execution, client configuration, remote endpoint, or publication fields.
- Decision: MCP Tool annotations are public untrusted hints. MyMCP's trusted internal effect and consent contract may use corresponding dimensions but must not treat annotations as policy enforcement, client approval proof, or isolation.

Plan (execution steps)
- [x] S1) Complete read-only current-state and standards inventory; resolve Q1 through Q7; record the exact approved target tree, contracts, manifest schema boundary, dependency rules, compatibility invariants, and roadmap migration sequence in this Track.
- [x] S2) Move TRACK_029 to ACTIVE (folder, filename, title, and current path) and check this step before changing durable architecture, vision, glossary, README, or roadmap material.
- [x] S3) Execute the architecture-documentation chunk: add `docs/PLUGIN_ARCHITECTURE.md` and update `docs/ARCHITECTURE.md` to distinguish current structure from the approved target; add or update focused documentation-consistency tests only where a concrete invariant justifies them; run focused validation; update this Track.
- [x] S4) Execute the product-and-terminology alignment chunk: update `VISION.md`, `README.md`, and `docs/GLOSSARY.md` with concise target summaries and links without claiming implementation; run focused documentation, identity, link, and whitespace validation; update this Track.
- [x] S5) Inspect the living MyMCP roadmap and propose its complete revised content for separate per-call user approval; if approved, revise it to align phases with the target architecture, inspect the result, and update this Track.
- [x] S6) Run complete applicable automated and whitespace validation, perform direct read-only MCP discovery and roadmap inspection, review all acceptance criteria, and record the derived first implementation Track boundary.
- [x] S7) Move TRACK_029 to COMPLETED (folder, filename, title, and current path), check this transition, and record completion outcomes.

Current inventory
- `mymcp/mcp/tool_registry.py` owns generic immutable ordered Tool registration, discovery, schema-aware dispatch, and duplicate public-name rejection.
- `mymcp/mcp/composition.py` defines `ToolIntegration` only as a zero-argument callable returning `tuple[ToolRegistration, ...]`; it carries no plugin identity, version, compatibility, origin, effect, consent, manifest, naming, lifecycle, or isolation metadata.
- `mymcp/mcp/startup.py` explicitly composes the one built-in `mnemosyne_integration`; static explicit selection is an appropriate minimal precursor to the target bootstrap.
- `mymcp/mcp/integrations/mnemosyne.py` owns Mnemosyne Tool selection, mutation-gate resolution, typed operation binding, and lazy per-operation root/store/service composition.
- Mnemosyne production ownership is physically split across `mymcp/mnemosyne/` configuration, the eleven-file `mymcp/memory/` domain, eight public memory Tool packages plus private adapters under `mymcp/mcp/tools/`, and `mymcp/mcp/integrations/mnemosyne.py`.
- `mymcp/mcp/tools/list_tools/` is host-owned and must remain outside Mnemosyne; it reports the complete final composed surface.
- `mymcp/mcp/methods.py` and `mymcp/mcp/protocol.py` currently return FastAPI `JSONResponse` values, so the documented transport/protocol distinction is not yet complete. The target makes MCP envelopes transport-neutral and leaves HTTP serialization in routes; this requires a separate behavior Track rather than incidental documentation work here.
- `mymcp/__init__.py` imports `mymcp.app`, which transitively imports methods and composes the startup registry. The target removes generic-package-import startup side effects and makes application/bootstrap assembly explicit.
- `tests/memory/test_import_boundaries.py` enforces useful current dependency rules but is path-specific to the transitional layout and will need target-oriented replacement during later implementation Tracks.
- Current package and tests depend on singular domain class identities, one process-shared list-cursor codec, one shared mutation-lock registry, startup-fixed settings resolution, exact Tool package shapes, and current monkeypatch seams; future moves must not duplicate implementations.
- Public compatibility includes current HTTP endpoints, Mnemosyne server marker, ordered Tool names and schemas, bounded results/errors/logging, client-prefixed permission names, independent default-off mutation gates, strict configuration, lazy memory-root initialization, version-1/version-2 records, deterministic storage paths, and filesystem truth.
- The active `MyMCP host and gateway roadmap` is now revision 2. It names `docs/PLUGIN_ARCHITECTURE.md` as the approved target, makes architectural minimalism an execution rule, commits Phase 1 to the generic identity/manifest/runtime/binding contracts, commits Phase 2 to the complete `mymcp/plugins/mnemosyne/` vertical package, and retains lifecycle/isolation, governance, and proven reusable services in dependency order.
- TRACK_026 remains an independent DRAFT for narrowing compact-token false positives. There are no ACTIVE or BLOCKED Tracks after TRACK_029 completion.
- `docs/PLUGIN_ARCHITECTURE.md` now defines the approved target package tree, layers, identity/version model, qualified and public Tool identity, effect/consent metadata, strict manifest v1 boundary, contribution invariants, static bootstrap, dependency rules, compatibility and security contracts, ecosystem relationship, phased delivery, and completion definition while explicitly stating that the target is not current behavior.
- `docs/ARCHITECTURE.md` remains the authoritative current-layout document and now links to the target, summarizes its ownership boundaries, and labels the target packages and manifest as architectural commitments rather than implemented capabilities.
- `VISION.md` now commits MyMCP to architectural minimalism, the generic plugin contract/runtime/bootstrap target, and Mnemosyne's future vertical ownership while explicitly retaining static in-process composition as the current state.
- `README.md` now gives users concise current-versus-target orientation, aligns its intended roles and roadmap shape with the plugin package and manifest design, and links the durable architecture without changing setup or public MCP guidance.
- `docs/GLOSSARY.md` now defines architectural minimalism, host plugin API, plugin manifest, bundled plugin, qualified Tool identity, public Tool binding, and host runtime, while labeling Tool integration and static integration composition as current transitional precursors.
- The first derived implementation Track should be `Versioned plugin manifest and identity contract`. Its bounded objective is to add the generic `mymcp/plugin/` identity, version, host-API interval, Tool-effect/consent, and strict manifest-v1 parsing/validation models through TDD. It must not change runtime composition, create the concrete Mnemosyne manifest, move Mnemosyne code, add dynamic loading, expose new MCP metadata, or alter public behavior. This gives later composition/runtime work one stable validated author contract rather than another anonymous integration seam.

Target architecture proposal
- Generic host packages:
  - `mymcp/routes/` owns HTTP transport.
  - `mymcp/mcp/` owns transport-neutral MCP parsing, protocol semantics, Tool registry/dispatch, argument compatibility, and host-owned Tools.
  - `mymcp/plugin/` owns stable plugin-facing contracts, strict manifest parsing/validation, and generic composition rules.
  - `mymcp/host/runtime.py` owns the immutable composed `HostRuntime` without importing concrete plugins.
  - `mymcp/host/bootstrap.py` owns explicit source-controlled built-in selection and is the only generic-host module that imports concrete plugin factories.
- Concrete bundled plugins:
  - `mymcp/plugins/mnemosyne/manifest.json` declares bounded static identity and capabilities.
  - `mymcp/plugins/mnemosyne/plugin.py` contributes Mnemosyne registrations and owns service composition.
  - `mymcp/plugins/mnemosyne/configuration.py` preserves all current operator configuration contracts.
  - `mymcp/plugins/mnemosyne/memory/` owns all memory meaning and persistence.
  - `mymcp/plugins/mnemosyne/mcp/tools/` owns every `memory_*` definition, handler, and private MCP adapter.
- Identity model:
  - Plugin identity: stable manifest ID, initially `mnemosyne`.
  - Plugin-local Tool identity: stable local ID such as `memory_recall`.
  - Qualified Tool identity: immutable pair `(plugin_id, tool_id)` retained by host composition as origin.
  - Endpoint-visible Tool name: host-approved binding that remains `memory_recall` for current compatibility and may follow a future namespacing policy for other plugins.
- Initial manifest responsibilities:
  - Require `manifest_version`, stable plugin `id`, `title`, `description`, semantic `version`, bounded `requires.host_api.min` and `max`, and a complete possible Tool inventory.
  - Require each Tool's local `id`, explicit `read_only`, `destructive`, `idempotent`, and `open_world` booleans, and `consent` of `none` or `per_call`.
  - Support strict startup validation against the actual selected contribution and fail closed on malformed, incompatible, duplicate, undeclared, or inconsistent registrations.
- Initial manifest non-responsibilities:
  - No executable import path, dynamic discovery, handlers, complete duplicated Tool schemas, runtime configuration values, secrets, arbitrary paths, mutation enablement, approval proof, installation, process isolation, or memory-data indexing.
- Static bootstrap:
  - Host source explicitly imports and orders built-in plugin factories.
  - Composition validates manifest and contribution identity, host compatibility, Tool declaration parity, qualified identity uniqueness, public-name bindings, host-reserved names, and final collisions before constructing one immutable runtime.
  - No partial runtime is returned after failure.
- Dependency rules:
  - Routes may depend on FastAPI and the composed host runtime but not plugin domains or plugin configuration.
  - Generic MCP, plugin contracts, and runtime code may not import concrete plugins; only bootstrap may do so.
  - Mnemosyne's plugin entrypoint may depend on generic plugin/MCP contracts and its own configuration, memory, and MCP adapters, but not routes, application assembly, host bootstrap, or another plugin.
  - Mnemosyne memory and configuration modules may use the standard library and their own narrow packages but not FastAPI, routes, host startup, or generic MCP behavior.
  - Plugins may not import each other, and no host service may absorb Mnemosyne semantics without a second real consumer.

Roadmap alignment proposal
- Architecture baseline: approve this target and make it the constraint for all later Tracks.
- Phase 1 — Plugin author contract and Tool identity: implement identified plugin contributions, qualified Tool identity/origin, host plugin-API compatibility, effect/consent metadata, endpoint-name binding, and collision rules without moving Mnemosyne yet.
- Phase 2 — Manifest and built-in plugin packaging: add strict packaged manifests and validation, move Mnemosyne MCP adapters, domain, and configuration into `mymcp/plugins/mnemosyne/` in coherent compatibility-proven chunks, and keep static in-process bootstrap.
- Phase 3 — Plugin lifecycle and isolation: define installation, enable/disable, update/remove, health, containment, resource boundaries, package loading, and the local threat model before making isolation claims.
- Phase 4 — Client-neutral governance gateway: apply server-enforced routing and policy using stable plugin/Tool origin and effect metadata behind one machine-local endpoint.
- Phase 5 — Reusable host services: generalize approval, audit, storage, or other mechanisms only after a second real plugin demonstrates a shared requirement.

Artifacts
- Living roadmap: `project/mymcp/roadmaps`, `MyMCP host and gateway roadmap`, active at revision 2 after approved reconciliation.
- Current architecture: `docs/ARCHITECTURE.md`.
- Target plugin architecture: `docs/PLUGIN_ARCHITECTURE.md`.
- Product direction: `VISION.md`.
- Canonical terminology: `docs/GLOSSARY.md`.
- Prerequisite completed Track: `.backlog/COMPLETED/2026/TRACK_027_COMPLETED_static_multi_integration_composition.md`.
- Prerequisite completed Track: `.backlog/COMPLETED/2026/TRACK_028_COMPLETED_complete_mymcp_identity_inversion.md`.
- Independent DRAFT: `.backlog/DRAFT/2026/TRACK_026_DRAFT_narrow_compact_token_refusal.md`.
- Standards inventory: MCP Tools specification, <https://modelcontextprotocol.io/specification/2025-11-25/server/tools>.
- Standards inventory: official MCP Registry, <https://github.com/modelcontextprotocol/registry>.
- Standards inventory: official MCPB repository and manifest specification, <https://github.com/modelcontextprotocol/mcpb>.

Completion notes
- 2026-07-24: Completed S1 through read-only repository inventory, exact current-boundary inspection, durable roadmap inspection, and review of the current MCP Tool, Registry, and MCPB contracts. Q1-Q7 are resolved with a concrete target package, immutable runtime, strict narrow manifest, host-owned public-name binding, atomic internal import migration, `memory/` domain name, and enforceable test strategy. No repository file other than this Track and no memory record changed during planning.
- 2026-07-24: Moved TRACK_029 to ACTIVE after explicit user approval. S3 architecture documentation is the next declared chunk; no runtime implementation, package move, roadmap mutation, commit, or push has occurred.
- 2026-07-24: Completed S3. Added `docs/PLUGIN_ARCHITECTURE.md` as the durable end-state architecture and updated `docs/ARCHITECTURE.md` to separate that target from the current transitional implementation. No new automated test was justified because the chunk changes no runtime behavior; the applicable `tests/test_project_identity.py` passed (`1 passed`), `git diff --check` passed, and direct inspection verified both local documentation links and current/target status language. A1-A6 and M2 now pass. S4 product and terminology alignment is next.
- 2026-07-24: Completed S4. Updated `VISION.md`, `README.md`, and `docs/GLOSSARY.md` so product intent, user orientation, roadmap shape, and canonical terminology all point to the approved plugin architecture while clearly distinguishing target contracts from current static integration behavior. No runtime or public MCP contract changed and no new automated test was justified; `tests/test_project_identity.py` passed (`1 passed`), `git diff --check` passed, and direct inspection verified local links and current/target wording. A7 now passes. S5 living-roadmap reconciliation is next and remains separately memory-approval-gated.
- 2026-07-24: Completed S5. Fresh exact inspection found the living MyMCP roadmap active at revision 1. After the complete replacement text and metadata were shown, the user separately approved the exact `memory_revise` call. The roadmap changed to active revision 2, and immediate exact inspection verified stable identity, title, provenance, creation time, and the complete approved architecture-aligned content/tags. A8 and M3 now pass. S6 complete validation, acceptance review, and first derived implementation-Track boundary are next.
- 2026-07-24: Completed S6. The complete automated suite passed all 761 tests in 7.71 seconds. `git diff --check` passed; explicit checks confirmed final newlines, no trailing whitespace in the untracked architecture/Track files, and valid local architecture links from current architecture, vision, and README. Configured-client `list_tools` still reported `mnemosyne 0.1.3` with the expected ordered nine-Tool enabled surface. Exact roadmap inspection verified active revision 2 and its complete approved architecture content. The repository diff contains documentation and backlog changes only; no runtime, schema, Tool, route, configuration, storage, package version, or existing memory data changed. A1-A9 and M1-M4 all pass. The first derived implementation boundary is a versioned plugin manifest and identity contract under `mymcp/plugin/`, with composition, concrete Mnemosyne packaging, dynamic loading, and public MCP changes explicitly deferred. S7 completion transition is the only remaining Track step.
- 2026-07-24: Completed TRACK_029. MyMCP now has one approved durable target architecture connecting product direction to a generic `mymcp/plugin/` author contract, immutable `mymcp/host/` runtime/bootstrap, and vertically owned bundled implementations under `mymcp/plugins/`, with all Mnemosyne production implementation converging on `mymcp/plugins/mnemosyne/`. The design fixes manifest, identity, public-binding, dependency, compatibility, security, ecosystem, and incremental-delivery boundaries without implementing or claiming plugin extraction. `VISION.md`, `README.md`, current architecture, glossary, and the living roadmap are aligned; the roadmap remains active at revision 2 with Phase 1 next. Final evidence is 761 passing tests, whitespace/link checks, unchanged direct MCP discovery, and exact roadmap inspection. No runtime code, public MCP contract, commit, push, or changelog event was produced.
- Roadmap reconciliation: the living `MyMCP host and gateway roadmap` was freshly inspected, revised under separate exact user approval from revision 1 to active revision 2, and re-inspected successfully. It now makes the approved plugin architecture authoritative, retains Phase 1 as next, and sequences concrete Mnemosyne packaging in Phase 2 before lifecycle/isolation, gateway governance, and proven reusable services.

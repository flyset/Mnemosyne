# TRACK 035 [COMPLETED]: Agent-operation scope for Mnemosyne memory

Track
- ID: TRACK_035
- Repository: MyMCP
- Branch: track-035-agent-scope
- Current path: .backlog/COMPLETED/2026/TRACK_035_COMPLETED_agent_scope.md

Problems (PORE)
- P1: As a global agent operating across projects, I need durable, session-updatable, user-approved operational configuration, because my persona defaults, policies, checklists, and failure-mode mitigations currently live only in boot-time files (e.g., neuromancer.md, reflect.json) outside Mnemosyne — making mid-session updates impossible through MCP tools and blocking cross-project configuration maintenance.

Objective
- Add a canonical agent-operation scope to Mnemosyne with namespace kind "agent", memory kinds "persona", "policy", "checklist", and "failure_mode", and a hybrid model where structural configuration stays in the agent boot file while user-approved session-managed refinements live in Mnemosyne memory.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Existing six scopes, their kinds, guidance, and behavior must remain unchanged.
- The agent scope must preserve the existing Mnemosyne consent, lifecycle, recall, listing, inspection, and revision contracts.
- The scope name "agent" must not conflict with existing or reserved identifiers.
- Agent records are user-approved agent-operation configuration, not user-profile memory; they remain subject to the existing no-secrets policy and all mutation approval gates.

Acceptance criteria
- [x] A1) [P1] A memory can be written to and read from scope=agent, namespace=<agent_id>, collection=<collection_name> using standard memory_remember and memory_recall.
- [x] A2) Agent scope supports memory kinds: persona, policy, checklist, failure_mode with correct per-kind writing guidance.
- [x] A3) Agent scope namespace kind is "agent", distinct from existing namespace kinds.
- [x] A4) memory_list, memory_inspect, memory_revise, memory_archive, memory_restore, memory_forget all work with agent-scope records under existing contracts.
- [x] A5) All existing scopes continue to work unchanged.
- [x] A6) All eight public `memory_*` Tool schemas and scope documentation publish the seventh scope and preserve their existing contracts.
- [x] A7) Mnemosyne and its capabilities publish the approved additive-feature versions, MyMCP remains independently `0.2.1`, all eight capability definitions match new versioned ledger entries, and every unchanged version dimension remains unchanged for its recorded reason.

Why now / impact
- The neuromancer agent rebuild revealed that cross-project agent configuration cannot be managed through MCP tools. Adding agent scope unlocks session-native config management without building a separate mechanism.

Scope
- In scope:
  - New scope="agent" with namespace kind="agent".
  - Memory kinds: persona, policy, checklist, failure_mode with canonical writing guidance.
  - Full Mnemosyne lifecycle support for agent-scope records.
  - Updates to scopes.py, records.py, normalization.py, paths.py, service.py, store.py.
  - Updates to MCP tool definitions and handlers.
  - Schema updates and coverage for all eight `memory_*` Tools: memory_recall, memory_list, memory_inspect, memory_remember, memory_revise, memory_archive, memory_restore, and memory_forget.
  - Explicit validation that MyMCP distribution/server remains `0.2.1`, plus the Mnemosyne plugin additive-feature version update, per-capability minor version updates, packaged manifest parity, and preserved historical capability-ledger entries.
  - Compatibility tests for all six existing scopes.
  - Updates to README.md, VISION.md, docs/ARCHITECTURE.md, docs/GLOSSARY.md, docs/MANUAL.md, docs/PLUGIN_ARCHITECTURE.md, docs/MNEMOSYNE_VISION.md, and applicable AGENTS.md guidance for the public seventh-scope contract and independently owned versions.
- Out of scope:
  - Changes to the MyMCP host plugin architecture.
  - Automatic migration of existing file-based config into Mnemosyne.
  - New MCP tools beyond the existing memory_* family.
  - Agent-scope-specific permission or governance rules.
  - Special cross-agent authority, routing, discovery controls, or isolation; the existing scope-wide listing contract continues to enumerate records in its selected scope.

Milestones
- [x] M1) Domain: scope, namespace kind, memory kinds, paths, guidance added to shared memory domain.
- [x] M2) MCP: all eight memory_* Tools accept the new scope with correct schema branches and reference validation.
- [x] M3) Validation: existing scope tests pass; new agent-scope tests pass.
- [x] M4) Integration: neuromancer.md updated with usage section (done in ideation).

Risks / decisions
- Risk: Adding a 7th scope increases schema complexity in memory_remember's oneOf branches. Mitigation: the agent scope has a simple structure (one namespace kind, four memory kinds, no event/occurred_at).
- Risk: Adding a public enum value can break generated clients that model scope as a closed union. Mitigation: preserve every existing value and contract, document the additive schema change, and test the exact published enum for every Tool.
- Decision: The agent scope name is "agent". This is a plain string enum addition, not a structural change to the scope model.
- Decision: Hybrid model — file is authoritative for boot config; Mnemosyne records overlay at session start. No automatic sync between file and memory.
- Decision: Agent records are user-approved operational configuration for a named agent and are governed by Mnemosyne's existing consent, lifecycle, storage, and no-secrets rules; they are not user-profile memories.
- Version impact: MyMCP distribution and endpoint/server marker remain `0.2.1`. Bundling does not collapse host and plugin version ownership, and this Track changes no host-owned runtime, endpoint identity, MCP mechanism, composition, or governance contract; Mnemosyne plugin and capability versions identify the additive domain/public-schema change.
- Version impact: Mnemosyne plugin advances from `0.2.0` to `0.3.0` because it gains additive agent-operation domain behavior across storage and every public capability.
- Version impact: `memory_recall` advances from `1.1.0` to `1.2.0`; `memory_list`, `memory_inspect`, `memory_archive`, `memory_restore`, `memory_remember`, `memory_revise`, and `memory_forget` each advance from `1.0.0` to `1.1.0`. Each Tool definition gains the additive `agent` scope in a direct scope enum or canonical-reference scope enum, and `memory_remember` additionally gains its scope-specific branch. Historical ledger entries remain unchanged and new entries are required for all eight selected versions.
- Version impact: The MCP protocol version is unchanged because request transport, negotiation, methods, and JSON-RPC semantics do not change. Host plugin API remains `1` because capability identity, definition, activation, and contribution semantics are unchanged. Manifest schema remains `1` because only declared semantic versions change within its existing shape. External worker protocol remains unimplemented and unchanged because this bundled plugin executes through the reviewed in-process adapter.
- Version impact: Configuration schema remains `1` because no operator setting or secret reference changes. Plugin-data schema remains `1` because existing storage interpretation and migration rules remain valid and the new deterministic top-level scope directory is an additive value under the current data contract. Memory record schema remains `2` because record shape, field meaning, lifecycle, and path projection structure are unchanged; only allowed scope, namespace-kind, and memory-kind values expand.
- Version impact: Runtime generations remain opaque and are newly issued by normal bootstrap without semantic-version meaning. Endpoint-visible Tool names, public bindings, result and error shapes, effect/consent metadata, requested authority, policy revision, and artifact model remain unchanged because the Track adds no Tool, privilege, governance, installation, or isolation behavior.

Open questions
- [x] Q1) Should agent-scope records appear in scope-wide listing (listing without namespace_id)? Yes: preserve the existing generic listing contract, which enumerates all records in the selected scope. No special cross-agent discovery control is introduced by this Track.
- [x] Q2) Are there any MCP protocol implications for adding a new scope to the six-value enum? The change is additive to MCP schemas and preserves existing values and result shapes, but clients with generated closed unions must update to accept `agent`; publish and test the exact expanded enum.

Decision log
- Decision (from ideation, 2026-07-26): scope=agent, namespace=neuromancer, collections=persona/policy/checklist/failure_mode. Hybrid file+memory model. Agent definition goes in neuromancer.md not MEMORY.md.
- Decision (Q1, 2026-07-26): Scope-wide `memory_list(scope="agent")` retains the existing complete selected-scope inventory semantics. The Track does not add special cross-agent discovery, routing, authority, or isolation behavior.
- Decision (Q2, 2026-07-26): `agent` is an additive value in each public scope schema. Existing enum values and all request/result semantics remain unchanged; generated closed-union clients must refresh their schema bindings.
- Decision (activation, revised 2026-07-31): Approve the complete version impact above: MyMCP remains `0.2.1`, Mnemosyne plugin advances to `0.3.0`, `memory_recall` capability advances to `1.2.0`, and the other seven capabilities advance to `1.1.0`; preserve every historical capability-ledger entry and every independently unchanged protocol, API, schema, identity, authority, and runtime dimension for the recorded reasons. This supersedes the initially approved host `0.3.0` interpretation because bundled packaging does not make the host and plugin one versioning unit.

Plan (execution steps)
- [x] S1) Move Track 035 to ACTIVE (folder, filename, and title status).
- [x] S2) TDD domain chunk: add a focused failing test for `agent` scope parsing, namespace kind, four kind/guidance pairs, path derivation, and non-event record validation; make the smallest shared-domain change, refactor, run focused tests, and update this Track.
- [x] S3) TDD MCP-schema chunk: add focused failing definition tests proving that all eight public `memory_*` Tools publish `agent` in every relevant direct or reference scope schema and that remember narrows its namespace kind and four kinds; make the smallest change, refactor, run focused tests, and update this Track.
- [x] S4) Lifecycle/integration characterization chunk: exercise remember, recall, list, inspect, revise, archive, restore, and forget for one agent record through the real registry, existing gates, filesystem store, and structured-reference contracts; make no production change when the generic lifecycle already passes, run focused regressions, and update this Track.
- [x] S5) Compatibility characterization chunk: add focused regression coverage proving all six existing scopes, their kinds, and their published schemas remain unchanged before the additive seventh scope; run the relevant test groups without manufacturing a production change and update this Track.
- [x] S6) Documentation: update README.md, VISION.md, docs/ARCHITECTURE.md, docs/GLOSSARY.md, docs/MANUAL.md, docs/PLUGIN_ARCHITECTURE.md, docs/MNEMOSYNE_VISION.md, and applicable AGENTS.md guidance for the public seventh-scope contract, additive-enum client compatibility, and independent host/plugin/capability versions.
- [x] S7) Validate: run the full test suite and direct MCP protocol checks for all eight Tools; record evidence in this Track.
- [x] S8) Review final acceptance and move Track 035 to COMPLETED (folder, filename, title, and Current path).

Current inventory
- mymcp/plugins/mnemosyne/memory/scopes.py (MemoryScope, SCOPE_DEFINITIONS, SCOPE_VALUES, namespace kinds)
- mymcp/plugins/mnemosyne/memory/records.py (CanonicalMemoryRecord, scope validation)
- mymcp/plugins/mnemosyne/memory/normalization.py (scope normalization)
- mymcp/plugins/mnemosyne/memory/paths.py (deterministic path derivation)
- mymcp/plugins/mnemosyne/memory/service.py (MemoryService)
- mymcp/plugins/mnemosyne/memory/store.py (FilesystemMemoryStore)
- mymcp/plugins/mnemosyne/memory/__init__.py (shared exports)
- mymcp/plugins/mnemosyne/mcp/tools/memory_recall/definition.py (scope enum derived from shared registry)
- mymcp/plugins/mnemosyne/mcp/tools/memory_remember/definition.py (schema branches)
- mymcp/plugins/mnemosyne/mcp/tools/memory_list/definition.py (scope enum)
- mymcp/plugins/mnemosyne/mcp/tools/memory_inspect/definition.py (scope enum)
- mymcp/plugins/mnemosyne/mcp/tools/_memory_lifecycle.py and _memory_revise.py (canonical reference scope schemas)
- mymcp/plugins/mnemosyne/plugin.py and manifest.json (plugin and per-capability versions)
- tests/plugin/capability_contract_ledger.json and test_capability_version_ledger.py (version-keyed definition guard and preserved history)
- mymcp/settings.py, pyproject.toml, and package/version tests (independently unchanged MyMCP `0.2.1` distribution and endpoint marker)
- README.md, docs/ARCHITECTURE.md, docs/GLOSSARY.md, docs/MANUAL.md (published seven-scope contract)
- S2 implemented `MemoryScope.AGENT`, its fixed `agent` directory and namespace kind, and `persona`, `policy`, `checklist`, and `failure_mode` definitions with bounded operational guidance. Existing generic parsing, non-event occurrence validation, and deterministic path projection required no special-case changes.
- S3 confirmed the shared registry projects `agent` into all eight public Tool definitions, including both inspect reference variants and the narrowed remember branch. MyMCP/server remains independently `0.2.1`; Mnemosyne plugin is `0.3.0`, recall capability is `1.2.0`, and the other seven capabilities are `1.1.0`; manifest parity and new version-keyed ledger entries retain all historical entries.
- S4 added one real-registry characterization in `tests/mcp/test_agent_scope_lifecycle.py`. With all existing mutation gates enabled against an isolated temporary root, it creates an agent policy, recalls/lists/inspects it, revises it, proves archive exclusion and archived inspection, restores recall eligibility, then re-archives, forgets, and proves exact absence. Generic domain, Tool, service, and store behavior required no production special case.
- S5 added `tests/mcp/test_existing_scope_compatibility.py`, which pins the original six scopes before `agent`: order, descriptions, directories, namespace kinds, allowed kinds, all eight public scope schemas, remember namespace/kind branches, and project-event occurrence constraints. It passed immediately, so no compatibility repair or production change was needed.
- S6 documents the seven-scope contract, exact agent kind guidance, hybrid boot-file/record boundary, unchanged consent/no-secrets/lifecycle behavior, ordinary scope-wide listing, no cross-agent authority, the `agent/` directory, all-eight-schema compatibility, and generated closed-union client refresh. Current guidance records MyMCP `0.2.1`, Mnemosyne `0.3.0`, recall `1.2.0`, and the other seven capabilities `1.1.0` without rewriting historical release statements.

Artifacts
- Idea memory: project/mnemosyne/ideas mem_ff2838aeea4146e783250b7e6a79ee50 (revision 2)
- Agent definition with scope usage: /Users/kosta/.config/opencode/agents/neuromancer.md
- Not roadmap-derived (new capability, not phase work)

Completion notes
- S2 red evidence: `python -m pytest tests/memory/test_scopes.py tests/memory/test_records.py tests/memory/test_paths.py` failed during collection because `MemoryScope.AGENT` did not exist.
- S2 green evidence: the same focused command passed `59` tests after the minimal shared-domain additions. Coverage proves ordered scope parsing/metadata, exact kind/guidance pairs, non-event canonical record round-trip and mismatch rejection, and deterministic agent reference paths.
- S3 red evidence: the focused schema/version run passed the transitive eight-Tool agent schema assertion and failed the expected plugin/capability/ledger assertions. It also failed host-version assertions that had been advanced under the initial, subsequently superseded interpretation that bundled packaging joined host and plugin version ownership.
- S3 green evidence: `python -m pytest tests/mcp/test_memory_agent_scope_definitions.py tests/mcp/test_memory_recall.py tests/mcp/test_memory_list.py tests/mcp/test_memory_inspect.py tests/mcp/test_memory_remember.py tests/mcp/test_memory_archive.py tests/mcp/test_memory_restore.py tests/mcp/test_memory_revise.py tests/mcp/test_memory_forget.py tests/mcp/test_mnemosyne_integration.py tests/mcp/test_list_tools.py tests/mcp/test_startup_settings.py tests/host/test_bootstrap.py tests/test_project_identity.py tests/test_production_compatibility.py tests/plugin/test_capability_version_ledger.py tests/plugin/test_mnemosyne_manifest.py tests/plugin/test_parity.py` passed `425` tests. This covers all eight exact definitions, remember flat/branch compatibility, host/package/plugin/capability versions, manifest parity, bootstrap inventory, and preserved historical ledger entries.
- S3 ownership correction: under user-approved review, `mymcp/settings.py`, `pyproject.toml`, and host-facing expectations were restored to `0.2.1`; Mnemosyne `0.3.0` and the eight capability increments remain. The corrected focused validation is recorded below.
- S3 corrected green evidence: the same `425`-test schema, integration, bootstrap, manifest, parity, ledger, and host/package command passed with MyMCP `0.2.1`, Mnemosyne `0.3.0`, recall `1.2.0`, and the other seven capabilities `1.1.0`; `git diff --check` also passed.
- S4 characterization evidence: `python -m pytest tests/mcp/test_agent_scope_lifecycle.py` passed immediately (`1` test), confirming the planned generic lifecycle support was already complete after S2/S3 rather than exposing a new behavior defect. No artificial failing test or production change was introduced.
- S4 regression evidence: `python -m pytest tests/mcp/test_agent_scope_lifecycle.py tests/mcp/test_mnemosyne_integration.py tests/memory` passed `344` tests, and `git diff --check` passed.
- S5 characterization evidence: `python -m pytest tests/mcp/test_existing_scope_compatibility.py` passed `3` focused tests immediately. The combined original/new domain and all-eight-Tool command passed `345` tests, and `git diff --check` passed.
- S6 evidence: the approved documentation files were authored by the `docs` subagent and reviewed by the primary agent; the primary corrected the Mnemosyne vision's obsolete “personal-only” wording and clarified that agent scope retains the independent MyMCP marker. `python -m pytest tests/test_project_identity.py tests/test_packaging.py tests/memory/test_import_boundaries.py` passed `36` tests; `git diff --check` and current-version/seven-scope consistency searches passed with historical completed-Track and release statements preserved.
- S7 independent automated evidence: the `test` subagent reviewed acceptance coverage and ran `python -m pytest` with `1174 passed` and no failures, a focused S7 suite with `76 passed`, and `git diff --check` successfully. It confirmed agent lifecycle, original-six compatibility, all-eight schemas, independent versions, manifest parity, and current/historical ledger coverage; it changed no files.
- S7 direct connected-MCP evidence: `list_tools` reported MyMCP `0.2.1` and all nine Tools. `memory_recall(scope="agent", namespace_id="track-035-validation", ...)` returned `no_matches`; `memory_list` returned a successful empty inventory; exact inspect of the all-zero nonexistent agent reference returned `not_found`. The approved no-write mutation checks returned `invalid_kind` for an agent `memory_remember` using project-only kind `decision`, and `not_found` for revise, archive, restore, and forget against the same nonexistent agent reference. A final agent-namespace list remained empty, proving the connected checks created no record.
- S7 repository evidence: version consistency confirms MyMCP package/server `0.2.1`, Mnemosyne plugin/manifest `0.3.0`, recall `1.2.0`, and the other seven capability declarations `1.1.0`. Status contained only Track 035's intended Track move, implementation, tests, documentation, and guidance files; no unrelated test-run change appeared.
- Acceptance review: A1-A7 and M1-M4 are satisfied. The test subagent noted that positive all-eight lifecycle coverage is registry-level rather than HTTP-level and that not every historical digest is separately hard-coded in Python; connected no-write calls now supplement all eight Tools, while the version-keyed JSON ledger remains complete and Git-reviewable. Neither observation blocks the declared acceptance.
- Final outcome: Mnemosyne now has the canonical `agent` scope, namespace kind `agent`, and `persona`, `policy`, `checklist`, and `failure_mode` kinds under the existing user-governed memory lifecycle. All eight public `memory_*` schemas and operations support it while the original six scopes remain unchanged. MyMCP remains independently `0.2.1`; Mnemosyne is `0.3.0`, recall is `1.2.0`, and the other seven capabilities are `1.1.0` with manifest parity and preserved historical ledger entries.
- Roadmap disposition: this Track is explicitly not roadmap-derived and does not change the MyMCP host-and-gateway roadmap's delivered baseline, phase sequence, dependencies, or next Phase 3A installation step. No roadmap revision is required.
- Completion transition: user-approved S8 moved folder, filename, title status, and Current path to COMPLETED. No commit, push, release, or durable changelog event was performed.

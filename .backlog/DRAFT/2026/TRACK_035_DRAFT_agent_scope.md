# TRACK 035 [DRAFT]: Agent-operation scope for Mnemosyne memory

Track
- ID: TRACK_035
- Repository: MyMCP
- Branch: track-035-agent-scope
- Current path: .backlog/DRAFT/2026/TRACK_035_DRAFT_agent_scope.md

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
- [ ] A1) [P1] A memory can be written to and read from scope=agent, namespace=<agent_id>, collection=<collection_name> using standard memory_remember and memory_recall.
- [ ] A2) Agent scope supports memory kinds: persona, policy, checklist, failure_mode with correct per-kind writing guidance.
- [ ] A3) Agent scope namespace kind is "agent", distinct from existing namespace kinds.
- [ ] A4) memory_list, memory_inspect, memory_revise, memory_archive, memory_restore, memory_forget all work with agent-scope records under existing contracts.
- [ ] A5) All existing scopes continue to work unchanged.
- [ ] A6) All eight public `memory_*` Tool schemas and scope documentation publish the seventh scope and preserve their existing contracts.

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
  - Compatibility tests for all six existing scopes.
  - Updates to README.md, docs/ARCHITECTURE.md, docs/GLOSSARY.md, and docs/MANUAL.md for the public seventh-scope contract.
- Out of scope:
  - Changes to the MyMCP host plugin architecture.
  - Automatic migration of existing file-based config into Mnemosyne.
  - New MCP tools beyond the existing memory_* family.
  - Agent-scope-specific permission or governance rules.
  - Special cross-agent authority, routing, discovery controls, or isolation; the existing scope-wide listing contract continues to enumerate records in its selected scope.

Milestones
- [ ] M1) Domain: scope, namespace kind, memory kinds, paths, guidance added to shared memory domain.
- [ ] M2) MCP: all eight memory_* Tools accept the new scope with correct schema branches and reference validation.
- [ ] M3) Validation: existing scope tests pass; new agent-scope tests pass.
- [ ] M4) Integration: neuromancer.md updated with usage section (done in ideation).

Risks / decisions
- Risk: Adding a 7th scope increases schema complexity in memory_remember's oneOf branches. Mitigation: the agent scope has a simple structure (one namespace kind, four memory kinds, no event/occurred_at).
- Risk: Adding a public enum value can break generated clients that model scope as a closed union. Mitigation: preserve every existing value and contract, document the additive schema change, and test the exact published enum for every Tool.
- Decision: The agent scope name is "agent". This is a plain string enum addition, not a structural change to the scope model.
- Decision: Hybrid model — file is authoritative for boot config; Mnemosyne records overlay at session start. No automatic sync between file and memory.
- Decision: Agent records are user-approved operational configuration for a named agent and are governed by Mnemosyne's existing consent, lifecycle, storage, and no-secrets rules; they are not user-profile memories.

Open questions
- [x] Q1) Should agent-scope records appear in scope-wide listing (listing without namespace_id)? Yes: preserve the existing generic listing contract, which enumerates all records in the selected scope. No special cross-agent discovery control is introduced by this Track.
- [x] Q2) Are there any MCP protocol implications for adding a new scope to the six-value enum? The change is additive to MCP schemas and preserves existing values and result shapes, but clients with generated closed unions must update to accept `agent`; publish and test the exact expanded enum.

Decision log
- Decision (from ideation, 2026-07-26): scope=agent, namespace=neuromancer, collections=persona/policy/checklist/failure_mode. Hybrid file+memory model. Agent definition goes in neuromancer.md not MEMORY.md.
- Decision (Q1, 2026-07-26): Scope-wide `memory_list(scope="agent")` retains the existing complete selected-scope inventory semantics. The Track does not add special cross-agent discovery, routing, authority, or isolation behavior.
- Decision (Q2, 2026-07-26): `agent` is an additive value in each public scope schema. Existing enum values and all request/result semantics remain unchanged; generated closed-union clients must refresh their schema bindings.

Plan (execution steps)
- [ ] S1) Move Track 035 to ACTIVE (folder, filename, and title status).
- [ ] S2) TDD domain chunk: add a focused failing test for `agent` scope parsing, namespace kind, four kind/guidance pairs, path derivation, and non-event record validation; make the smallest shared-domain change, refactor, run focused tests, and update this Track.
- [ ] S3) TDD MCP-schema chunk: add focused failing definition tests proving that all eight public `memory_*` Tools publish `agent` in every relevant direct or reference scope schema and that remember narrows its namespace kind and four kinds; make the smallest change, refactor, run focused tests, and update this Track.
- [ ] S4) TDD lifecycle/integration chunk: add focused failing tests that remember, recall, list, inspect, revise, archive, restore, and forget agent records under existing gates and structured-reference contracts; make the smallest change, refactor, run focused tests, and update this Track.
- [ ] S5) TDD compatibility chunk: add focused regression coverage proving all six existing scopes, their kinds, and their published schemas remain unchanged; run the relevant test groups and update this Track.
- [ ] S6) Documentation: update README.md, docs/ARCHITECTURE.md, docs/GLOSSARY.md, and docs/MANUAL.md for the public seventh-scope contract and additive-enum client compatibility.
- [ ] S7) Validate: run the full test suite and direct MCP protocol checks for all eight Tools; record evidence in this Track.

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
- README.md, docs/ARCHITECTURE.md, docs/GLOSSARY.md, docs/MANUAL.md (published six-scope contract)

Artifacts
- Idea memory: project/mnemosyne/ideas mem_ff2838aeea4146e783250b7e6a79ee50 (revision 2)
- Agent definition with scope usage: /Users/kosta/.config/opencode/agents/neuromancer.md
- Not roadmap-derived (new capability, not phase work)

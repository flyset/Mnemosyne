# TRACK 028 [COMPLETED]: complete MyMCP identity inversion

Track
- ID: TRACK_028
- Repository: MyMCP (hosting the Mnemosyne memory domain in-process)
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_028_COMPLETED_complete_mymcp_identity_inversion.md

Problems (PORE)
- P1: As a maintainer planning MyMCP host work, I receive a Mnemosyne-centred project-memory map, because `MEMORY.md` routes the general project, roadmap, decisions, reviews, ideas, issues, checkpoints, and changelog to the `mnemosyne` namespace even though MyMCP is the repository and host project.
- P2: As a future MyMCP plugin author, I cannot identify the project’s primary product direction from its repository guidance, because the current top-level vision and user-facing orientation remain centred on Mnemosyne’s memory substitute rather than MyMCP as a plugin host and client-neutral governance gateway.
- P3: As a maintainer resuming work, I can be steered by stale MyMCP context, because the active collectionless MyMCP summary still describes MyMCP as ideation rather than the current host project with a forward roadmap.
- P4: As a maintainer preserving the repository’s history, I risk losing or misclassifying Mnemosyne context during inversion, because existing changelog and domain records must remain historical/domain evidence rather than be bulk-moved into MyMCP.

Objective
- Complete the final Mnemosyne-to-MyMCP identity inversion so repository guidance and durable project memory make MyMCP the default project perspective while preserving Mnemosyne’s public memory-domain identity and historical context.

Non-negotiables
- All implementation follows TDD when behavior changes; this Track must not change runtime code, MCP behavior, Tool schemas, routes, storage layout, or the fixed six-scope memory taxonomy.
- Preserve local-first, single-user, least-privilege, explicit-tool, and per-call consent boundaries.
- Preserve Mnemosyne’s public server, `memory_*` Tool, configuration, storage, and existing-record identities.
- Do not bulk-migrate, rewrite, relocate, archive, or forget existing project records merely because their namespace is Mnemosyne. Classify existing records only when this Track explicitly requires it.
- Preserve the existing Mnemosyne changelog as inspectable memory-domain project history; do not move or rewrite its events.
- Every `memory_remember`, `memory_revise`, and `memory_archive` call remains independently user-approved through the MCP client after current-state inspection.
- Keep exactly one active forward MyMCP roadmap and one active transition roadmap until inversion acceptance. Archive the transition roadmap only after all acceptance criteria pass and its lifecycle mutation receives separate approval.
- Do not begin Phase 1 of the MyMCP host and gateway roadmap until this Track completes.
- Do not commit or push unless explicitly requested after repository changes have been reviewed.

Acceptance criteria
- [x] A1) [P1] `MEMORY.md` identifies `project/mymcp` as the default home for project-wide orientation and future host plans, decisions, critiques, reviews, ideas, issues, checkpoints, and host changelog events.
- [x] A2) [P1, P4] `MEMORY.md` explicitly distinguishes MyMCP host context from Mnemosyne domain/history context, retains the existing Mnemosyne changelog mapping for its historical events, and does not direct new host work to the Mnemosyne namespace.
- [x] A3) [P2] Root guidance and user-facing project orientation describe MyMCP as the repository and host product, with Mnemosyne as its built-in user-governed memory domain; a clearly domain-scoped document retains Mnemosyne’s product vision without claiming plugin extraction or changing public behavior.
- [x] A4) [P3] The active collectionless MyMCP summary accurately describes the current MyMCP host project and no longer characterizes it as uncommitted ideation.
- [x] A5) [P1, P4] The active `mymcp/roadmaps` record remains the forward host roadmap; the active `mnemosyne/roadmaps` record remains limited to the transition and is archived only after completion acceptance.
- [x] A6) [P4] Existing Mnemosyne changelog events, memory-domain records, public identities, and on-disk record locations remain unchanged.
- [x] A7) [P1, P2, P3, P4] Read-only inspection verifies the final project-memory map and exact active/archive lifecycle states; repository documentation checks and the applicable automated suite pass without runtime behavior changes.
- [x] A8) [P1, P2, P3, P4] The completed transition roadmap and forward MyMCP roadmap are reconciled: the former is archived as inspectable history, and the latter is inspected as the authoritative active roadmap.

Why now / impact
- TRACK_027 completed static composition and the living roadmap split now establishes a forward MyMCP roadmap plus a final Mnemosyne-to-MyMCP transition roadmap. Phase 1 of the forward MyMCP roadmap concerns plugin-author contract and Tool identity, so project instructions and durable placement must be inverted before those decisions accrue under the wrong namespace.

Scope
- In scope:
  - Update project instructions and memory-map guidance to make MyMCP the default project perspective.
  - Reframe top-level repository orientation and vision around MyMCP as host/gateway while retaining Mnemosyne’s domain-specific vision in an explicit domain document.
  - Revise the existing collectionless MyMCP ideation summary into current project orientation after current-state inspection.
  - Verify the already-created MyMCP forward roadmap and Mnemosyne transition roadmap; archive the transition roadmap after accepted inversion.
  - Establish routing for future MyMCP host changelog events without moving existing Mnemosyne changelog history.
  - Add or adjust documentation-consistency tests only if a concrete repository convention or behavior requires them; otherwise validate the documentation and memory map directly.
  - Perform direct read-only MCP inspection of every changed/created/archived record and the final map.
- Out of scope:
  - Runtime, package, HTTP, MCP protocol, Tool, schema, storage, configuration, consent, taxonomy, or memory-record-format changes.
  - Plugin extraction, dynamic discovery, external plugin loading, package installation, lifecycle implementation, namespacing implementation, or Phase 1 MyMCP host work.
  - Bulk migration, rewriting, relocation, archival, or deletion of existing Mnemosyne project records or changelog events.
  - Creating a Mnemosyne feature roadmap before memory-domain work needs its own durable long-range plan.
  - Rewriting the generic agent operating manual or unrelated getting-started material unless inventory demonstrates a concrete MyMCP-identity contradiction.
  - Commit, push, release, or changelog event creation unless separately requested.

Milestones
- [x] M1) The target identity, memory routing, document homes, and treatment of current MyMCP/Mnemosyne records are explicitly decided and reviewed.
- [x] M2) Repository instructions and durable MyMCP orientation consistently identify MyMCP as the host project while preserving Mnemosyne domain identity.
- [x] M3) The memory lifecycle reaches the accepted final state: MyMCP forward roadmap active, transition roadmap archived, and existing Mnemosyne history unchanged.
- [x] M4) Documentation, direct memory inspection, and required automated validation establish the completed inversion.

Risks / decisions
- Risk: Replacing the top-level Mnemosyne vision can erase or dilute the memory-domain product’s purpose.
- Mitigation: Move or reproduce that purpose in one explicitly Mnemosyne-scoped document and preserve all public memory-domain boundaries.
- Risk: A broad namespace cleanup could rewrite historical records or destroy useful provenance.
- Mitigation: Limit mutations to the stale MyMCP orientation, the two explicit roadmap records, and newly approved records; leave existing Mnemosyne history in place.
- Risk: Two active roadmaps can leave agents uncertain which governs host work during transition.
- Mitigation: The transition roadmap explicitly defers MyMCP Phase 1 until inversion completes; `MEMORY.md` will name the MyMCP forward roadmap as the destination and the transition roadmap as temporary.
- Risk: Updating `MEMORY.md` before current records are inspected can create a map that points to absent or stale context.
- Mitigation: Inspect exact records before each mutation and validate the final map against their references/lifecycle states.
- Decision: The existing `mnemosyne/roadmaps` record is transition history, not a Mnemosyne feature roadmap; it will be archived rather than repurposed after inversion acceptance.
- Decision: Existing Mnemosyne changelog events remain where they are. Future MyMCP host events use the MyMCP map after inversion; this does not relocate historical events.

Open questions
- [x] Q1) Which domain-scoped document should retain the current Mnemosyne vision: a new `docs/MNEMOSYNE_VISION.md`, a renamed document, or another focused location?
- [x] Q2) Does root `AGENTS.md` require substantive wording changes beyond its already MyMCP-first project intent, or should the Track limit instruction edits there to any demonstrated contradiction?
- [x] Q3) Should the current collectionless MyMCP ideation summary be revised in place as current MyMCP orientation, or archived after a new canonical MyMCP overview record is approved?
- [x] Q4) Which existing collectionless or collected `mnemosyne` project records, if any, are presently host-wide rather than historical/domain-specific and therefore require an explicitly approved exception to the no-bulk-migration rule?
- [x] Q5) What repository validation is appropriate for documentation and memory-map changes that do not alter runtime behavior?

Decision log
- Decision (Q1): Keep root `VISION.md` as the project-wide MyMCP product vision and preserve the current Mnemosyne product vision in new focused document `docs/MNEMOSYNE_VISION.md`. Root `VISION.md` will link to the domain document; existing historical Track references remain unchanged.
- Decision (Q2): Root `AGENTS.md` already states the correct MyMCP-host/Mnemosyne-domain relationship and requires no substantive identity change. `docs/ARCHITECTURE.md`, `docs/GLOSSARY.md`, `docs/GETTING_STARTED.md`, and `docs/MANUAL.md` likewise have no demonstrated identity contradiction requiring this Track to edit them.
- Decision (Q3): Revise the existing collectionless MyMCP summary in place. Preserving its stable identity avoids a duplicate overview and removes its obsolete ideation framing. The inventory also found stale ideation wording in the active collectionless MyMCP GitHub reference; revise that exact reference rather than leaving contradictory active context.
- Decision (Q4): No existing `project/mnemosyne` record requires migration or relocation. Memory-domain records remain Mnemosyne context; the host-separation idea, rename plan, transition events, and transition roadmap remain historical transition evidence. Existing Mnemosyne changelog events remain unchanged and future MyMCP host events route to `project/mymcp/changelog`.
- Decision (Q5): This documentation-only inversion changes no runtime behavior, so no new automated test is justified. Validate focused identity invariants with `python -m pytest -q tests/test_project_identity.py`, use `git diff --check`, directly verify local document links and final text, run the complete automated suite in S5, and supplement it with direct read-only MCP listing/inspection.
- Decision: The minimal repository-guidance change set is `VISION.md`, new `docs/MNEMOSYNE_VISION.md`, `README.md`, `MEMORY.md`, and `.backlog/README.md`, plus this Track. The root and scoped `AGENTS.md` files, architecture, glossary, generic manual/getting-started guidance, runtime code, tests, and ignored local OpenCode agent file remain unchanged.
- Decision: `MEMORY.md` will route project-wide MyMCP orientation, roadmaps, decisions, critiques, reviews, ideas, issues, checkpoints, and future host changelog events to `project/mymcp`; it will add an explicit `project/mnemosyne` domain/history exception and retain the existing Mnemosyne changelog as inspectable history rather than moving records.
- Decision: After fresh exact inspection and independent approval for each call, revise `project/mymcp/<collectionless>/mem_6ae48572863146e6ae5cd49cf5afb95a` from current revision 3 with namespace label `MyMCP`, title `MyMCP host project overview`, tags `mymcp`, `overview`, `plugin-host`, `gateway`, `architecture`, and `governance`, and content stating the current host identity, delivered Tracks 023–027 baseline, retained Mnemosyne public/domain identities, unimplemented plugin extraction/dynamic loading, forward-roadmap authority, next plugin-contract phase, and preserved governance boundaries.
- Decision: After fresh exact inspection and separate approval, revise `project/mymcp/<collectionless>/mem_55dffd17f8934cbeb8bf2f64f78a4425` from current revision 1 with namespace label `MyMCP`, unchanged title `MyMCP GitHub repository URL`, tags `mymcp`, `github`, `repository`, `reference`, and `transition`, and content stating that `https://github.com/flyset/MyMCP` is the intended source repository while the current implementation remains at `https://github.com/flyset/Mnemosyne` with MyMCP repository-distribution and package identity.
- Decision: Do not revise the active forward roadmap or any Mnemosyne record. Re-inspect both roadmaps after the MyMCP revisions; keep the transition roadmap active through complete repository and memory validation. Only after acceptance passes, obtain separate approval to archive `project/mnemosyne/roadmaps/mem_cc934e9399044ab2a9ba656def5cd26b` at its freshly inspected revision (currently 3), then inspect it as archived and the MyMCP roadmap as active.

Plan (execution steps)
- [x] S1) Move TRACK_028 to ACTIVE (folder, filename, title, and current path) and check this step before implementation.
- [x] S2) Execute the identity-inventory and decision TDD/planning chunk: inspect all relevant MyMCP and Mnemosyne project records, current document references, and exact roadmap revisions; resolve Q1 through Q5; record the minimal document list, exact memory mutations, lifecycle order, and non-migrated historical records; run any focused consistency checks justified by the selected document changes; update this Track.
- [x] S3) Execute the repository-guidance chunk: update `VISION.md`, add `docs/MNEMOSYNE_VISION.md`, update the MyMCP orientation and roadmap links in `README.md`, invert the project map in `MEMORY.md`, and correct the `.backlog/README.md` Track template; preserve all excluded documents and runtime behavior; run focused documentation/link/format and project-identity validation; update this Track.
- [x] S4) Execute the memory-inversion chunk: freshly inspect and independently obtain per-call approval to revise the two approved collectionless MyMCP records; inspect both roadmaps and verify that each remains active; do not archive the transition roadmap yet; inspect every result and update this Track.
- [x] S5) Run the complete required validation and direct read-only MCP map/roadmap/history checks; review acceptance criteria; after acceptance passes, freshly inspect and separately obtain approval to archive the transition roadmap as the final mutation; inspect the archived transition roadmap and active forward MyMCP roadmap; record reconciliation evidence.
- [x] S6) Move TRACK_028 to COMPLETED (folder, filename, title, and current path), check this transition, and record completion outcomes.

Current inventory
- `mymcp` is the repository distribution and top-level Python host package; `mymcp/mcp/startup.py` composes the built-in Mnemosyne integration through host-owned static composition.
- `README.md` now states MyMCP's client-neutral host/gateway direction and separates the MyMCP and Mnemosyne intended roles, non-goals, roadmap shape, and vision links. Root `VISION.md` now owns MyMCP product intent, while new `docs/MNEMOSYNE_VISION.md` preserves the prior Mnemosyne notebook vision.
- `MEMORY.md` now maps project-wide general, overview, roadmap, decision, critique, review, idea, issue, checkpoint, and host changelog context to `project/mymcp`. Its explicit `project/mnemosyne` exception preserves domain/history context and existing changelog events without routing new host work there.
- The active forward roadmap is `project/mymcp/roadmaps/mem_5f3b5f4871d0406995f222d48e0357b7`, titled `MyMCP host and gateway roadmap`, revision 1.
- The transition roadmap `project/mnemosyne/roadmaps/mem_cc934e9399044ab2a9ba656def5cd26b`, titled `Mnemosyne-to-MyMCP transition roadmap`, is archived as inspectable history at revision 4 after final acceptance.
- The active collectionless MyMCP summary `mem_6ae48572863146e6ae5cd49cf5afb95a` is now titled `MyMCP host project overview` at revision 4. It records the current host identity, delivered Tracks 023–027 baseline, retained Mnemosyne identities, explicit unimplemented boundaries, forward roadmap, next phase, and governance constraints.
- The active collectionless MyMCP reference `mem_55dffd17f8934cbeb8bf2f64f78a4425` is now revision 2. It distinguishes the intended MyMCP GitHub repository from the current implementation at `flyset/Mnemosyne` and no longer characterizes MyMCP as ideation.
- The archived collectionless MyMCP reference `mem_be8ec6cc29b149b6b85cf13cff616f6a` remains historical and requires no mutation.
- The active MyMCP gateway idea `mem_8d6a8a8ed614495e97dcbad7511225b3` remains an idea and does not require mutation unless review finds a concrete contradiction.
- Existing Mnemosyne changelog events, including Track 027’s pushed completion event, are historical/domain context and remain unchanged.
- Complete bounded listing found five MyMCP records and 33 Mnemosyne records. Exact inspection covered every MyMCP record and the potentially host-wide Mnemosyne overview, host-separation idea, rename plan, changelog rule, Tracks 023–027 transition events, review, and transition roadmap; remaining listed Mnemosyne titles/kinds are explicitly memory-domain records. No migration exception is required.
- Repository-reference inventory found no Markdown link checker, documentation-consistency test, Markdown linter, or documentation CI job. `tests/test_project_identity.py` is the applicable focused identity invariant; the full suite remains required at S5.
- Root `AGENTS.md`, architecture, and glossary continue to define MyMCP as host and Mnemosyne as its in-process memory domain. `.backlog/README.md` now uses `Repository: MyMCP` in the current Track template; historical completed Tracks remain unchanged.
- TRACK_026 remains a separate DRAFT for compact-token refusal correction and is out of scope.

Artifacts
- Transition roadmap: `Mnemosyne-to-MyMCP transition roadmap`, `project/mnemosyne/roadmaps`, archived revision 4.
- Forward roadmap: `MyMCP host and gateway roadmap`, `project/mymcp/roadmaps`, revision 1.
- Project-memory map: `MEMORY.md`.
- MyMCP product vision: `VISION.md`.
- Mnemosyne domain vision: `docs/MNEMOSYNE_VISION.md`.
- Current MyMCP overview: `project/mymcp/<collectionless>/mem_6ae48572863146e6ae5cd49cf5afb95a`, revision 4.
- Current MyMCP repository reference: `project/mymcp/<collectionless>/mem_55dffd17f8934cbeb8bf2f64f78a4425`, revision 2.
- Prerequisite Track: `.backlog/COMPLETED/2026/TRACK_027_COMPLETED_static_multi_integration_composition.md`.
- Unrelated DRAFT: `.backlog/DRAFT/2026/TRACK_026_DRAFT_narrow_compact_token_refusal.md`.

Completion notes
- TRACK_028 moved to ACTIVE and S1 was checked on 2026-07-23 after explicit user approval.
- S2 completed a read-only bounded inventory of both project namespaces, exact inspection of current MyMCP and relevant Mnemosyne records, repository-reference analysis, Q1–Q5 decisions, and lifecycle sequencing. No repository-guidance file or memory record was changed during S2.
- Focused S2 validation passed on 2026-07-23: `git diff --check`; `python -m pytest -q tests/test_project_identity.py` (`1 passed`). Direct MCP discovery reported Mnemosyne server version 0.1.3 and the expected nine enabled Tools; bounded project listings and exact inspections returned normal results.
- S3 completed the approved repository-guidance inversion without runtime, schema, Tool, storage, configuration, test, or existing-memory-record changes. The five-document change set is root `VISION.md`, new `docs/MNEMOSYNE_VISION.md`, `README.md`, `MEMORY.md`, and `.backlog/README.md`; excluded guidance and implementation files remain unchanged.
- Focused S3 validation passed on 2026-07-23: `git diff --check`; untracked-file trailing-whitespace/final-newline checks; direct new-link and MyMCP/Mnemosyne routing text checks; `python -m pytest -q tests/test_project_identity.py` (`1 passed`).
- S4 completed two independently approved exact revisions. The MyMCP overview changed from revision 3 to 4 and the MyMCP repository reference changed from revision 1 to 2; immediate exact inspection verified their complete replacement text, active lifecycle, stable identity, kind, language, provenance, and creation time.
- Post-mutation read-only checks verified the MyMCP forward roadmap active at revision 1, the transition roadmap still active at revision 3, all five MyMCP records present with expected lifecycle states, and all eight existing Mnemosyne changelog records still present. No Mnemosyne record was mutated.
- Complete S5 validation passed on 2026-07-23: `git diff --check`; changed-file trailing-whitespace/final-newline and local-link/routing checks; the complete automated suite (`761 passed in 7.41s`). The diff contains documentation/backlog changes only; no runtime, test, package, schema, Tool, route, storage, configuration, or compatibility version changed.
- Final read-only MCP checks verified the revised MyMCP overview active at revision 4, the revised repository reference active at revision 2, all five MyMCP records present, and all eight existing Mnemosyne changelog records present with unchanged references and lifecycle states.
- After acceptance passed, the user independently approved the final archive call. The transition roadmap changed from active revision 3 to archived revision 4 with content and identity preserved; exact inspection and bounded listing verified it remains inspectable history. The MyMCP host and gateway roadmap remains active at revision 1 and is now the authoritative forward roadmap.
- Roadmap reconciliation: the forward MyMCP roadmap remains current without revision. Identity inversion satisfies its stated authority precondition, while Phase 1 remains next and its delivered baseline, sequencing, dependencies, intended outcomes, and next major step do not otherwise change.
- TRACK_028 moved to COMPLETED on 2026-07-23 after every acceptance criterion, milestone, validation, memory inspection, and roadmap lifecycle requirement passed.

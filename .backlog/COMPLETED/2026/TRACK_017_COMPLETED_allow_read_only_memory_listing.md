# TRACK 017 [COMPLETED]: Allow read-only memory listing

Track
- ID: TRACK_017
- Repository: Mnemosyne
- Branch: main
- Current path: `.backlog/COMPLETED/2026/TRACK_017_COMPLETED_allow_read_only_memory_listing.md`

Problems (PORE)
- P1: As the local Mnemosyne user, I experience an approval prompt whenever an agent lists memory metadata, because the bundled OpenCode policy treats complete read-only inventory access like a consent-gated mutation.

Objective
- Allow the read-only `memory_list` Tool without an approval prompt while preserving exact per-call approval for every mutation Tool.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Change only bundled client permission policy and its documentation; do not change MCP registration, Tool behavior, storage, or mutation gates.
- Preserve the agent's broad `mnemosyne_*` denial followed by explicit narrow read-only allows and exact mutation asks.

Acceptance criteria
- [x] A1) [P1] Project and Mnemosyne-agent OpenCode policies explicitly allow `mnemosyne_memory_list` without prompting.
- [x] A2) [P1] Every memory mutation Tool remains configured as `ask` at both applicable policy levels.
- [x] A3) [P1] Automated policy tests enforce the intended order and focused/full validation passes.
- [x] A4) [P1] README guidance describes listing with the other allowed read-only Tools and reserves approval guidance for mutation calls.

Why now / impact
- Direct use showed that a prompt on every bounded read-only listing interrupts normal memory discovery, and the user explicitly rejected that interaction.

Scope
- In scope:
  - `opencode.json` top-level and inline-agent permission rules.
  - `.opencode/agents/mnemosyne.md` permission rules.
  - Focused policy tests and README OpenCode guidance.
- Out of scope:
  - MCP Tool schemas, handlers, registry, transport, storage, or results.
  - Mutation enablement or consent policy.
  - Broader wildcard permissions or auto-approval.

Milestones
- [x] M1) Change the bundled client policy through one focused TDD chunk.
- [x] M2) Reconcile documentation and complete validation.

Risks / decisions
- Risk: A complete inventory exposes compact metadata without a prompt; this is an explicit user-selected local client policy tradeoff.
- Decision: Treat all current read-only Mnemosyne Tools consistently as explicit `allow` rules while retaining `ask` for mutations.
- Decision: Supersede Track 016's initial bundled-client `ask` decision without changing the server-side least-privilege list contract.

Open questions
- [x] Q1) Should `memory_list` remain `ask` because it enumerates complete metadata?

Decision log
- Decision (Q1): No. On 2026-07-19 the user explicitly requested that read-only listing not require allowance and approved changing both policy levels, tests, and documentation.

Plan (execution steps)
- [x] S1) Move Track 017 to ACTIVE (folder, filename, and title status).
- [x] S2) TDD the permission policy: first change focused expectations to require explicit list `allow` while preserving mutation `ask`, run them to observe failure, then minimally update both bundled policy files and rerun focused validation.
- [x] S3) Update README OpenCode guidance, run the full suite and repository checks, record evidence, and move Track 017 to COMPLETED.

Current inventory
- `opencode.json` now explicitly allows `mnemosyne_memory_list` at top level and in the inline Mnemosyne agent while retaining exact mutation asks.
- `.opencode/agents/mnemosyne.md` now explicitly allows the exact list Tool after the broad denial and alongside the other read-only allows.
- `tests/test_opencode_config.py` enforces exact ordered list allows and mutation asks in both policy representations.
- `README.md` documents listing as an explicitly allowed read-only Tool and reserves per-call approval guidance for mutations.
- Track 016 and its complete memory-list implementation are present as uncommitted existing work; this Track must preserve those changes and alter only the approved client-policy decision.

Artifacts
- Activated on 2026-07-19 after the user approved explicit read-only list allows at both bundled OpenCode policy levels, with mutation approvals preserved.
- S2 TDD evidence (2026-07-19): `PYTHONPATH=. pytest -q tests/test_opencode_config.py` first failed both tests because all three existing policy representations still used `ask`; after the minimal policy edits it passed with 2 tests.
- S3 validation (2026-07-19): `PYTHONPATH=. pytest -q` passed with 696 tests and `git diff --check` passed.
- Final review confirmed the change is limited to bundled client policy, its focused tests, README guidance, and this Track; MCP registration, Tool behavior, storage, and mutation gates are unchanged.

Completion notes
- Completed on 2026-07-19. `memory_list` is now explicitly allowed by the project, inline-agent, and file-agent OpenCode policies; remember, revise, archive, restore, and forget remain exact `ask` rules.
- OpenCode must be restarted to load the updated client policy.

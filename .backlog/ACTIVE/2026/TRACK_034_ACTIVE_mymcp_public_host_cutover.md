# TRACK 034 [ACTIVE]: MyMCP public-host cutover

Track
- ID: TRACK_034
- Repository: MyMCP
- Branch: main
- Current path: .backlog/ACTIVE/2026/TRACK_034_ACTIVE_mymcp_public_host_cutover.md

Problems (PORE)
- P1: As a MyMCP user, I still discover the endpoint, application, and compatibility marker as Mnemosyne 0.1.4, because the completed host/package identity inversion has not yet performed its mandatory public-host cutover.
- P2: As a repository maintainer, the canonical implementation still lives at `flyset/Mnemosyne` while `flyset/MyMCP` is only a one-commit LICENSE placeholder, so the public repository identity disagrees with the delivered host architecture.
- P3: As a client operator, changing the configured MCP connection key and permission prefix could accidentally bypass mutation approval or retain a stale mixed identity, because current OpenCode and local client policies are keyed by `mnemosyne` rather than `mymcp`.
- P4: As a Mnemosyne user, I risk domain and storage incompatibility if the host cutover is treated as a broad rename, because plugin `mnemosyne`, `memory_*`, `MNEMOSYNE_*`, `~/.mnemosyne`, records, logging, and consent must remain unchanged.

Objective
- Atomically release MyMCP 0.2.0 as the public host, canonical GitHub repository, application, and official client identity while preserving every Mnemosyne plugin, Tool, configuration, storage, record, logging, and consent identity.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Execute one declared coherent TDD chunk at a time and update this Track immediately after validation.
- Preserve local-first operation, single-user scope, filesystem truth, least privilege, explicit Tools, operator enablement, and per-call client consent.
- Preserve `/mcp`, `/health`, `/version`, MCP protocol version `2024-11-05`, package/import name `mymcp`, and CLI commands `mymcp`, `mymcp-dev`, and `mymcp-test`.
- Preserve plugin ID `mnemosyne`, plugin version `0.1.0`, all eight `memory_*` names/order/schemas/results/errors, `MNEMOSYNE_*`, `~/.mnemosyne/config.toml`, `~/.mnemosyne/memory`, version-1/version-2 records, deterministic paths, logging, cursors, locks, gates, and mutation semantics.
- Change the public host/application/package compatibility marker to MyMCP 0.2.0 without adding endpoint, Tool, permission, repository, or runtime identity aliases.
- Official client policy must use one `mymcp` connection/agent identity, broad `mymcp_*` denial before narrow read-only allows, and exact mutation `ask` rules last. Server enablement remains distinct from per-call approval.
- A denied or dismissed mutation approval must produce no Tool HTTP call and no filesystem or log change. An approved exact-call check must remain separately approved and bounded.
- Keep the old verified 0.1.4 artifact and complete old client policy available only for operational rollback; never run old and new public identities concurrently.
- Use no force push or unrelated-history merge for repository migration. Preserve commit hashes, branches, tags, and GitHub repository state through server-side renames.
- Every GitHub mutation, commit/push, tag/release, local ignored client-file mutation, server/client restart, and direct mutation check requires separate exact user approval before execution.
- Do not create a replacement `flyset/Mnemosyne` repository or implement external plugin installation, activation, isolation, lifecycle, gateway governance, or public effect/consent metadata in this Track.

Acceptance criteria
- [x] A1) [P1] MCP initialize, `/version`, FastAPI metadata, and `list_tools` identify host `mymcp` version `0.2.0`; package metadata uses version `0.2.0` and canonical repository `https://github.com/flyset/MyMCP`.
- [x] A2) [P1, P4] Automated baseline comparison proves `/mcp`, `/health`, `/version` shape, MCP protocol version, `list_tools` ownership/first position, and every `memory_*` Tool definition/order/result/error remain compatible except for the approved host name/version marker.
- [x] A3) [P4] Plugin manifest/adapter identity remains `mnemosyne` 0.1.0 and all Mnemosyne environment, settings-file, memory-root, schema, path, lifecycle, logging, cursor, lock, and consent contracts remain unchanged.
- [x] A4) [P3] Tracked OpenCode policy uses only the `mymcp` connection/agent/prefix, preserves deny-first/read-only-allow/mutation-ask ordering at every policy level, and contains no old connection or permission prefix.
- [ ] A5) [P3] Officially supported local client configurations are inventoried and migrated atomically or explicitly excluded; ignored local files do not silently grant a mutation Tool or remain required by clean-clone automated tests.
- [ ] A6) [P3] Direct client checks after reconnect prove discovery uses the new host marker, each denied mutation approval makes no Tool HTTP call and changes no source/log/root state, and each separately approved exact mutation check makes one expected bounded change only.
- [ ] A7) [P2] `flyset/MyMCP` becomes the full canonical repository through a no-force server-side rename, retaining main history, commit hashes, `mnemosyne-v0.1.3-pre-mymcp`, visibility, license, and settings; the one-commit placeholder is preserved under an approved temporary name or disposed of through a separately approved decision.
- [ ] A8) [P2] Every maintained clone and repository/package/documentation URL points to `flyset/MyMCP`; GitHub and Git verification prove `origin/main`, HEAD, history, tags, and redirect behavior; no unrelated history is merged.
- [ ] A9) [P1, P2, P3, P4] A verified `mymcp` 0.2.0 artifact/tag/release is published only after complete automated compatibility, package, client-policy, and operational validation pass with no secret or generated artifact.
- [ ] A10) [P1, P4] README, vision, architecture, glossary, test guidance, scoped guidance, and release notes describe the completed cutover, current MyMCP host identity, permanently preserved Mnemosyne identities, and still-deferred external/lifecycle/gateway work.

Why now / impact
- TRACK_033 delivered complete bundled Mnemosyne extraction. The living roadmap revision 6 marks this mandatory 0.2.0 public-host cutover as NEXT and requires it before external activation or gateway operation.

Scope
- In scope:
  - Characterize the complete Mnemosyne 0.1.4 compatibility baseline before changing host identity.
  - Change `SERVER_NAME`, `SERVER_VERSION`, `APP_TITLE`, package version, description where needed, and canonical repository metadata as one 0.2.0 candidate.
  - Update host identity assertions while freezing every Mnemosyne plugin/domain contract.
  - Replace the official tracked OpenCode connection, agent, and generated permission prefix atomically with `mymcp`.
  - Inventory ignored/local OpenCode and Claude client files and define their supported migration or exclusion without committing private local configuration.
  - Add automated policy/order/absence checks and direct client denial/no-call plus separately approved exact-call evidence.
  - Update current documentation, examples, repository URLs, and release guidance.
  - Build and inspect the complete 0.2.0 wheel before publication.
  - Preserve the one-commit `flyset/MyMCP` placeholder under an approved temporary name, rename the full `flyset/Mnemosyne` repository to `flyset/MyMCP`, update `origin`, and verify GitHub state without force pushing.
  - Commit/push, tag, and publish the verified cutover only through separately approved exact operations.
  - Stop/restart the official server and clients in one controlled operational cutover with explicit rollback evidence.
- Out of scope:
  - Renaming plugin `mnemosyne`, any `memory_*` Tool, `MNEMOSYNE_*`, `.mnemosyne`, memory namespace/collection data, record fields, storage paths, or logger compatibility names.
  - Creating a new `flyset/Mnemosyne` repository or separately distributing the Mnemosyne plugin.
  - Plugin installation, `PluginContext`, isolated workers, external activation, supervision, lifecycle publication, gateway policy, host-verifiable approval evidence, or security audit.
  - Endpoint aliases, duplicate public server identities, Tool aliases, permission-prefix fallbacks, concurrent old/new runtimes, unrelated Git history merges, or force pushes.
  - Memory feature, schema, ranking, policy, listing, lifecycle, or storage redesign.

Milestones
- [x] M1) Exact host/repository/client/release identity inventory, compatibility baseline, atomic sequence, rollback, and acceptance map are resolved in DRAFT.
- [x] M2) The complete local 0.2.0 candidate and official tracked client policy pass focused TDD and complete automated compatibility.
- [x] M3) Current documentation, package metadata, wheel, and release candidate consistently identify MyMCP while preserving Mnemosyne.
- [ ] M4) GitHub repository, local origin, official client, and running endpoint are cut over and verified without force, aliases, or mixed identity.
- [ ] M5) Direct approval/no-call checks, release publication, roadmap reconciliation, and final acceptance pass.

Risks / decisions
- Risk: GitHub rename target `flyset/MyMCP` is occupied by a one-commit LICENSE placeholder.
- Mitigation: Rename the placeholder to an approved temporary name before renaming the full repository; never force-push or merge unrelated histories.
- Risk: Creating a new `flyset/Mnemosyne` immediately would consume the old-name redirect and imply separately supported plugin distribution.
- Mitigation: Keep replacement Mnemosyne repository creation out of scope until a later explicit separation Track.
- Risk: Client permission-prefix changes could convert mutation prompts into denial bypass or implicit allow.
- Mitigation: Drive exact policy order and old-prefix absence through focused tests, then require direct deny/no-call and separately approved exact-call checks after client restart.
- Risk: Ignored local `.opencode/` or `.claude/` state may disagree with tracked policy or be absent in clean clones.
- Mitigation: Inventory it explicitly, remove clean-clone test dependence on ignored files, and mutate local client state only through separately approved operational steps.
- Risk: A partial code/config/repository/server cutover presents mixed identities or stale discovery.
- Mitigation: Validate a complete candidate first; quiesce clients; perform approved repository, client, and runtime steps in one documented sequence; restart/reconnect before validation; retain a bounded rollback procedure.
- Risk: Version changes accidentally alter plugin or protocol versions.
- Mitigation: Add exact tests for independent host/package 0.2.0, plugin 0.1.0, host API 1, and MCP protocol `2024-11-05`.
- Decision: This Track owns the complete mandatory public-host cutover; a Git-only rename is insufficient and prohibited as an isolated outcome.
- Decision: Preserve the full repository through GitHub rename rather than copying or force-pushing it into the placeholder.
- Decision: Preserve all completed backlog history and the historical `mnemosyne-v0.1.3-pre-mymcp` tag.

Open questions
- [x] Q1) What exact temporary name and final disposition apply to the one-commit `flyset/MyMCP` placeholder?
- [x] Q2) What exact candidate commit, repository rename, local-origin update, tag, release, client restart, and server restart ordering produces the narrowest atomic cutover and rollback?
- [x] Q3) What tag name and GitHub release title/body identify the 0.2.0 cutover while preserving the historical Mnemosyne tag?
- [x] Q4) Which client configurations are official beyond tracked `opencode.json`, and how should ignored `.opencode/agents/mnemosyne.md` and `.claude/settings.local.json` be migrated or excluded?
- [x] Q5) How will direct OpenCode denial prove no Tool HTTP request occurred, and which bounded exact calls are safe and necessary to prove mutation approval after the prefix change?
- [x] Q6) Is rollback to the old public identity permitted only before release publication, or also as a bounded incident response after cutover validation begins?
- [x] Q7) Which repository description, topics, project URLs, README clone commands/badges, package metadata, and release assets must change?
- [x] Q8) What exact automated baseline freezes every intentionally preserved Mnemosyne identity without freezing incidental implementation details?

Decision log
- Decision: Begin with planning only. No implementation-driving test, identity/configuration change, GitHub mutation, local ignored-client mutation, server/client restart, commit/push, tag/release, documentation contract, or memory record change while this Track remains DRAFT.
- Decision: The living `MyMCP host and gateway roadmap` revision 6 and `docs/PLUGIN_ARCHITECTURE.md` mandatory compatibility cutover are authoritative.
- Decision: Current GitHub inspection found public `flyset/Mnemosyne` contains the full 58-commit history at `28f7cfc`, one historical tag, and no issues/PRs/releases/automation state; public `flyset/MyMCP` contains only commit `285a69f` and `LICENSE`. Both are admin-accessible and unarchived.
- Decision (Q1): Rename the one-commit placeholder to `flyset/mymcp-placeholder` and retain it unchanged through Track completion. Deletion, transfer, reuse, or archival is not required for the cutover and needs a later separate exact decision and approval.
- Decision (Q2): Complete and validate one local 0.2.0 candidate, commit and push it to the current full repository, then quiesce the old server and OpenCode before any public rename. Rename the placeholder, rename the full repository server-side, update local `origin`, verify history/settings/redirects, start exactly one MyMCP 0.2.0 server, reconnect a freshly restarted client, run direct checks, and only then tag and publish the release. Never run old and new public identities concurrently.
- Decision (Q3): Use annotated tag `mymcp-v0.2.0` and release title `MyMCP 0.2.0: public-host cutover`. The release body states that MyMCP is now the public host, enumerates the preserved Mnemosyne plugin/Tool/configuration/storage/record identities, names the compatibility and client-policy validation, and keeps installation, activation, isolation, lifecycle, and gateway work deferred. Preserve `mnemosyne-v0.1.3-pre-mymcp` unchanged.
- Decision (Q4): Tracked `opencode.json` is the official distributable client policy. The ignored `.opencode/agents/mnemosyne.md` is this clone's operator-local development-agent companion and will be separately approved for rename to `mymcp.md` plus MyMCP purpose/path/prefix updates during operational cutover; automated clean-clone tests must not read it. Ignored `.claude/settings.local.json` is unsupported local state and not an approval boundary; separately remove its stale `mcp__mnemosyne__*` grants without adding ambient `mcp__mymcp__*` mutation grants. No other local client is official in this Track.
- Decision (Q5): Use one rejected and one separately approved exact `memory_archive` request for a syntactically valid nonexistent canonical reference while a validation server has only archive/restore enabled and points at an absent isolated memory root. Rejection must show the client denial, no new Uvicorn `POST /mcp`, no MCP request/response log, no `mcp.memory_archive` event, and no root creation. Approval-once of the same request must produce exactly one Tool HTTP call and one bounded `not_found` archive event with no root or record creation. Automated tests, not repeated live mutations, prove all five mutation rules remain exact `ask` entries.
- Decision (Q6): Before release publication, a failed cutover may fully roll back under separate approvals by quiescing MyMCP/client state, restoring the complete old client policy and verified 0.1.4 artifact, reversing repository names and `origin`, and starting only the old endpoint. After public tag/release publication, incident response may stop service, withdraw an asset/release under separate approval, or issue a corrective MyMCP release, but must retain MyMCP public identity and must not revive a public Mnemosyne host.
- Decision (Q7): Set the canonical repository description to `Local-first MCP host for narrowly scoped integrations, with bundled Mnemosyne memory.` and topics to `mcp`, `local-first`, `ai-memory`, `mymcp`, `mnemosyne`, `python`, and `fastapi`. Package metadata uses version `0.2.0`, a MyMCP-host description, and `Homepage`, `Repository`, and `Issues` URLs under `https://github.com/flyset/MyMCP`. Current docs and examples use the MyMCP clone/repository/client identity; historical completed Tracks and the historical tag remain unchanged. Publish only the inspected `mymcp-0.2.0-py3-none-any.whl` release asset.
- Decision (Q8): Freeze observable compatibility by asserting the approved host-marker delta and unchanged routes, protocol, host API, plugin identity/version, selected Tool names/order/definitions, results/errors, argument normalization, mutation gates, environment/settings/root names, record schemas/paths, cursors, locks, logging bounds, and consent semantics. Reuse canonical definitions and representative existing contract suites rather than snapshotting private module paths, directory/file counts, opaque generations/cursors, timing, absolute paths, ignored client files, or incidental log formatting.

Identity matrix
- Public host/application/release: server `mymcp`, marker/package `0.2.0`, FastAPI title `MyMCP`, repository `https://github.com/flyset/MyMCP`, OpenCode connection/agent/prefix `mymcp`/`mymcp`/`mymcp_*`.
- Preserved transport/protocol: `/mcp`, `/health`, `/version`, MCP protocol `2024-11-05`, host API `1`, manifest schema `1`, `list_tools` first and host-owned.
- Preserved distribution/import/commands: distribution and package `mymcp`; commands `mymcp`, `mymcp-dev`, and `mymcp-test`.
- Preserved Mnemosyne plugin/domain: plugin `mnemosyne` version `0.1.0`; all eight `memory_*` capabilities and their public bindings; all `MNEMOSYNE_*`; `~/.mnemosyne/config.toml`; `~/.mnemosyne/memory`; version-1/version-2 records; deterministic paths; lifecycle, refusal, logging, cursor, lock, gate, and exact-mutation semantics.

Candidate file and test map
- S4 production/policy: `mymcp/settings.py`, `pyproject.toml`, and tracked `opencode.json`.
- S4 identity/compatibility tests: `tests/test_project_identity.py`, `tests/test_production_compatibility.py`, `tests/test_app.py`, `tests/routes/test_operational.py`, `tests/mcp/test_dispatcher.py`, `tests/mcp/test_list_tools.py`, `tests/mcp/test_mnemosyne_integration.py`, `tests/mcp/test_startup_settings.py`, `tests/host/test_bootstrap.py`, `tests/plugin/test_mnemosyne_manifest.py`, `tests/plugin/test_parity.py`, `tests/test_mnemosyne_configuration.py`, and `tests/test_opencode_config.py`.
- S5 client safety: `tests/test_opencode_config.py` and tracked `opencode.json`; remove all automated dependency on ignored `.opencode/` and `.claude/` files. The two ignored local-file mutations remain separately approved operational actions, not implementation fixtures.
- S6 current documentation/guidance: `README.md`, `VISION.md`, `docs/ARCHITECTURE.md`, `docs/PLUGIN_ARCHITECTURE.md`, `docs/GLOSSARY.md`, `tests/README.md`, root `AGENTS.md`, `mymcp/mcp/AGENTS.md`, and `mymcp/routes/AGENTS.md`. Review `docs/GETTING_STARTED.md`, `docs/MANUAL.md`, `docs/MNEMOSYNE_VISION.md`, `MEMORY.md`, and plugin-scoped guidance, changing only stale current-host or official-client claims.
- Preserved implementation suites remain authoritative for Mnemosyne MCP adapters, manifest/parity, configuration, and `tests/memory/`; do not mechanically rewrite `mnemosyne` where it denotes the plugin/domain.

Operational sequence and exact commands
- Candidate validation remains local and precedes all repository/runtime/client mutations. S7 separately approves `git add`/commit and then push to current `origin`; the intended commit subject is `Release MyMCP 0.2.0 public-host cutover` and it is not amended after publication.
- After separately approved quiescence, rename the placeholder with `gh repo rename mymcp-placeholder --repo flyset/MyMCP --yes`, then rename the full repository with `gh repo rename MyMCP --repo flyset/Mnemosyne --yes`. Each rename is separately approved and verified before the next mutation.
- Separately approve `git remote set-url origin git@github.com:flyset/MyMCP.git`; then verify `git remote -v`, `git fetch origin`, local/remote HEAD equality, full 58-commit ancestry, both tag refs, visibility/default branch/license/settings, and the old repository URL redirect. Do not create a replacement `flyset/Mnemosyne`.
- Separately approve final repository metadata mutation after rename. Apply the Q7 description/topics without changing visibility or unrelated repository settings.
- Separately approve the ignored OpenCode-agent rename/update and Claude stale-grant cleanup, server start/stop, and OpenCode restart/reconnect. Start only the candidate MyMCP server and confirm discovery before any mutation check.
- Separately approve each rejected and approved Q5 client attempt with the complete exact arguments displayed. Preserve terminal evidence and before/after absence of the isolated root; do not create an ad-hoc protocol script.
- After all post-cutover checks, separately approve annotated tag creation `git tag -a mymcp-v0.2.0 -m "MyMCP 0.2.0: public-host cutover"`, tag push `git push origin mymcp-v0.2.0`, and GitHub release creation with the already inspected wheel and Q3 title/body. Never publish before the tag target, wheel bytes, repository identity, and direct client evidence agree.

Validation and acceptance commands
- S4 focused identity/compatibility: `python -m pytest -p no:cacheprovider tests/test_project_identity.py tests/test_production_compatibility.py tests/test_app.py tests/routes/test_operational.py tests/mcp/test_dispatcher.py tests/mcp/test_list_tools.py tests/mcp/test_mnemosyne_integration.py tests/mcp/test_startup_settings.py tests/host/test_bootstrap.py tests/plugin/test_mnemosyne_manifest.py tests/plugin/test_parity.py tests/test_mnemosyne_configuration.py tests/test_opencode_config.py -q`.
- S5 focused client safety: `python -m pytest -p no:cacheprovider tests/test_opencode_config.py -q` from both the working clone and a clean-clone-equivalent source tree without ignored client files.
- S6 packaging and complete validation: `python -m pytest -p no:cacheprovider tests/test_packaging.py tests/test_production_compatibility.py -q`, then `python -m pytest -p no:cacheprovider tests -q`, `git diff --check`, and source/wheel secret/generated-artifact review. Build the publication wheel only under separate approval and verify filename, METADATA name/version/description/URLs, exact source inventory, packaged manifest bytes, and absence of transitional/generated files.
- Direct read-only protocol acceptance after restart: initialize, `/version`, FastAPI metadata, `tools/list`, `list_tools`, representative `memory_list`, `memory_inspect`, and no-match `memory_recall`; verify MyMCP host marker and exact preserved enabled Tool surface without changing the memory root.
- Git/release acceptance: compare candidate HEAD with `origin/main` and the tag target; verify the 58-commit ancestry and `mnemosyne-v0.1.3-pre-mymcp`; inspect repository metadata and old-name redirect; download and hash the published wheel and compare it with the approved local artifact.

Plan (execution steps)
- [x] S1) Complete initial read-only roadmap, repository, GitHub, source, client-policy, release, documentation, and test inventory; create this DRAFT Track after explicit user approval.
- [x] S2) Resolve Q1-Q8 and record the exact identity matrix, preserved baseline, candidate file/test map, client support boundary, GitHub/release commands, no-call evidence method, operational sequence, rollback, and acceptance commands in this DRAFT Track.
- [x] S3) Move TRACK_034 to ACTIVE (folder, filename, title, current path, and this checkbox) after explicit user approval and before adding any implementation-driving test.
- [x] S4) Execute the baseline and candidate-identity TDD chunk: first write focused failing tests for MyMCP 0.2.0 host/application/package/repository/client identity and exact preserved Mnemosyne/plugin/protocol contracts; implement the smallest complete local candidate across identity constants, package metadata, tracked official client policy, and affected assertions; refactor, validate, and update this Track.
- [x] S5) Execute the client-safety TDD chunk: remove automated dependence on ignored local files, enforce deny-first/read-only-allow/mutation-ask ordering and old-prefix absence, define supported local migration instructions, validate no ambient mutation allow, and update this Track.
- [x] S6) Execute the documentation/release-candidate chunk: update current docs, examples, scoped guidance, repository URLs, clone commands, release notes, and exact preserved/deferred claims; build and inspect the 0.2.0 artifact; run focused and complete automated validation; update this Track.
- [ ] S7) Review the complete candidate and request separate exact approval to commit/push it to the current full repository before any GitHub rename.
- [ ] S8) Request separate exact approval and execute the no-force GitHub rename sequence, local-origin update, and history/tag/redirect/settings verification with rollback available; update this Track.
- [ ] S9) Request separate exact approval and execute the operational client/server restart and reconnect sequence; perform direct discovery, denied/no-call checks, and separately approved bounded exact-call checks; update this Track.
- [ ] S10) Request separate exact approval to create/push the 0.2.0 tag and GitHub release only after post-cutover checks pass; verify artifact/release state and update this Track.
- [ ] S11) Inspect the linked living roadmap and repository-reference memory; propose any required revisions through separate exact approvals and record reconciliation.
- [ ] S12) Review A1-A10 and M1-M5, record final outcomes and evidence, then move TRACK_034 to COMPLETED after explicit approval.

Current inventory
- `mymcp/settings.py` now owns public constants `mymcp`, `0.2.0`, protocol `2024-11-05`, and `MyMCP`; initialize, `/version`, FastAPI metadata, and `list_tools` derive from them.
- `pyproject.toml` now identifies distribution `mymcp` version `0.2.0`, preserves the three MyMCP CLI scripts, uses the approved MyMCP host description, and publishes canonical Homepage/Repository/Issues URLs under `flyset/MyMCP`.
- The bundled plugin manifest/adapter remain independently `mnemosyne` 0.1.0 and must not change.
- Tracked `opencode.json` now uses only connection and agent key `mymcp` and generated `mymcp_*` permissions while preserving broad denial, read-only allows, and exact mutation asks; S5 still owns explicit stale-prefix absence checks and clean-clone independence.
- `tests/test_opencode_config.py` now reads only tracked `opencode.json`, requires the same exact ordered broad deny/four read-only allows/five mutation asks at top level and under agent `mymcp`, requires the sole MCP connection key `mymcp`, and rejects old connection, agent, and permission-prefix identity. Ignored `.opencode/agents/mnemosyne.md` and `.claude/settings.local.json` remain untouched local operational state; they are not test fixtures or approval boundaries and retain the separately approved migration/exclusion treatment in Decision (Q4).
- `tests/test_project_identity.py` now fixes the public host/application/package/repository/command identity. Production compatibility additionally fixes initialize, `/version`, FastAPI metadata, `list_tools`, the unchanged read-only Tool surface, and no-write behavior. Prior hardcoded marker assertions now expect only the approved MyMCP host delta; tests deriving identity constants remain unchanged.
- README, vision, current/target architecture, glossary, project-memory guidance, Mnemosyne vision, test guidance, root/MCP/route/plugin scoped guidance, and `docs/releases/0.2.0.md` now describe the local MyMCP 0.2.0 candidate, canonical target URL, exact tracked client policy, permanently preserved Mnemosyne identities, pending repository/operational/publication steps, and deferred external/lifecycle/gateway work without rewriting historical completed Tracks.
- The retained untracked publication candidate is `dist/mymcp-0.2.0-py3-none-any.whl`, SHA-256 `531cc9a603d16399b12650fd09d3bc76f43b4d5d1b15fed0377a6197c820e3e7`. Its metadata, complete inventory, source-manifest parity, and absence of transitional/cache entries are verified. It is a release asset and must not enter the source commit.
- Current local `origin` is `git@github.com:flyset/Mnemosyne.git`; local `main` and `origin/main` are clean and equal at `28f7cfc`.
- `flyset/Mnemosyne` is public, unarchived, admin-accessible, and contains the full 58-commit project history plus tag `mnemosyne-v0.1.3-pre-mymcp`; it has no issues, pull requests, releases, workflows, secrets, webhooks, branch protection, or additional collaborators.
- `flyset/MyMCP` is public, unarchived, admin-accessible, and contains only one unrelated initial LICENSE commit `285a69f`; it has no tags, issues, pull requests, releases, or configured automation state.
- The repository working tree was clean when this Track was drafted. There were no ACTIVE, BLOCKED, or other DRAFT Tracks.

Artifacts
- Living roadmap: `project/mymcp/roadmaps`, `MyMCP host and gateway roadmap`, active revision 6; mandatory MyMCP 0.2.0 public-host cutover is NEXT.
- Repository reference: `project/mymcp/<collectionless>`, `MyMCP GitHub repository URL`, active revision 2; intended repository is `flyset/MyMCP`, current implementation repository is `flyset/Mnemosyne`.
- Authoritative target: `docs/PLUGIN_ARCHITECTURE.md`, especially public identity cutover, compatibility contract, incremental delivery, and gateway approval boundaries.
- Planned release body: `docs/releases/0.2.0.md`; it explicitly remains unpublished until S10.
- Retained release asset: `dist/mymcp-0.2.0-py3-none-any.whl`; SHA-256 `531cc9a603d16399b12650fd09d3bc76f43b4d5d1b15fed0377a6197c820e3e7`; excluded from the source commit.
- Completed prerequisite: `.backlog/COMPLETED/2026/TRACK_033_COMPLETED_vertical_mnemosyne_extraction.md`.
- Backlog workflow: `.backlog/README.md` and `.backlog/PORE.md`.

Completion notes
- 2026-07-26: Completed initial read-only roadmap, repository, GitHub, identity, client-policy, package/release, documentation, and test inventory. Confirmed TRACK_033 and roadmap revision 6 make the mandatory MyMCP 0.2.0 public-host cutover next; the full repository remains `flyset/Mnemosyne`; `flyset/MyMCP` is a one-commit LICENSE placeholder; current host/client identity remains Mnemosyne 0.1.4; and plugin/domain identities must remain unchanged. After explicit user approval, created this DRAFT Track only. No implementation-driving test, production/configuration change, GitHub mutation, ignored local-client mutation, server/client restart, commit/push, tag/release, documentation contract, or memory record changed. S2 detailed planning is next; implementation remains prohibited while DRAFT.
- 2026-07-26: Completed S2 detailed planning after explicit approval to edit this DRAFT Track only. Resolved Q1-Q8; fixed the local full-history inventory at 58 commits; recorded the exact host/plugin identity matrix, compatibility baseline, candidate files/tests/docs, official-client boundary, placeholder/repository/tag/release choices, denied/no-call and approved-once archive evidence, quiesced operational sequence, pre-publication rollback, post-publication incident boundary, and focused/full/package/Git/release acceptance commands. M1 and S2 now pass. No implementation-driving test, production/configuration/client file, GitHub state, runtime, memory, dependency/environment state, commit, push, tag, or release changed. S3 ACTIVE transition is next and requires separate explicit approval.
- 2026-07-26: Moved TRACK_034 to ACTIVE after explicit approval. Synchronized the folder, filename, title, current path, and S3 checkbox before any implementation-driving test. No production code, test, package configuration, client policy, GitHub state, runtime, memory, dependency/environment state, commit, push, tag, or release changed. S4 baseline and candidate-identity TDD is next.
- 2026-07-26: Completed S4 through focused TDD. Added literal MyMCP 0.2.0 host/application/package/repository/command assertions, updated exact public-marker and tracked OpenCode identity expectations, and first ran the approved focused suite against the old implementation: 15 intended identity failures and 223 preserved-contract passes. The smallest implementation changed only `mymcp/settings.py`, `pyproject.toml`, and tracked `opencode.json`; plugin `mnemosyne` 0.1.0, all `memory_*`, protocol `2024-11-05`, routes, schemas, results/errors, configuration/storage/record identities, and mutation semantics remain unchanged. The focused suite then passed all 238 tests and `git diff --check` passed. Independent verification repeated the recorded 237-test suite plus the focused identity test, passed all 238 tests and whitespace validation, found no accidental Mnemosyne change or S6 scope leak, and confirmed that ignored-client independence and explicit stale-prefix absence correctly remain S5 work. S4 now passes. No ignored local client file, documentation, GitHub state, runtime, memory, build artifact, dependency/environment state, commit, push, tag, or release changed. S5 client-safety TDD is next.
- 2026-07-26: Completed S5 through focused TDD. Refactored the tracked-policy test to define one exact ordered policy for both levels, removed its ignored `.opencode/agents/mnemosyne.md` read, and added explicit sole-connection plus old connection/agent/prefix absence assertions. The red run failed exactly because the top-level tracked policy lacked broad deny and three read-only allows. The smallest implementation added `mymcp_*` deny followed by `list_tools`, recall, and inspect allows before the existing list allow and five mutation asks; the agent policy already had the required order. The focused test then passed and `git diff --check` passed. Independent verification repeated the one focused test, whitespace validation, exact 10-entry ordering at both levels, sole `mymcp` MCP identity, old-identity absence, and no ignored-client file read with no blocker. A4 and S5 now pass. The ignored OpenCode development-agent migration and unsupported Claude stale-grant cleanup remain separately approved operational actions under Q4; neither file changed. No production runtime, documentation, GitHub state, memory, build artifact, dependency/environment state, commit, push, tag, or release changed. S6 documentation/release-candidate work is next.
- 2026-07-26: Completed S6 documentation and release-candidate validation through separately approved actions. Updated current product, vision, architecture, glossary, project-memory, Mnemosyne-vision, test, and scoped-guidance documents plus the planned 0.2.0 release body; all describe a local candidate and preserve pending repository rename, reconnect/direct approval checks, tag/release publication, and later external/lifecycle/gateway work. Independent read-only documentation review found no stale current identity, accidental Mnemosyne rename, premature completion claim, policy count/order error, or broken local link. The approved focused packaging/production command passed 2 tests, and the complete no-cache suite passed all 1139 tests. The separately approved publication build produced `dist/mymcp-0.2.0-py3-none-any.whl`; metadata identifies MyMCP 0.2.0 and all canonical URLs, its packaged manifest exactly matches source, its 76-entry inventory contains no transitional/cache file, and its SHA-256 is `531cc9a603d16399b12650fd09d3bc76f43b4d5d1b15fed0377a6197c820e3e7`. Removed only the approved intermediate `build/` directory and retained the untracked wheel for release verification. Independent read-only candidate review confirmed artifact bytes/RECORD/manifest, metadata, no secret or S6 scope leak, no unsupported completion claim, and no remaining build intermediate; it warned correctly that the wheel must not enter the source commit. `git diff --check` passed. A1-A3, M2-M3, and S6 now pass. No ignored local client file, GitHub state, running server/client, memory, dependency installation, source commit, push, tag, or release changed. S7 candidate review and separately approved commit/push are next.

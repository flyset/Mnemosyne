# TRACK 038 [COMPLETED]: plugin capability version governance

Track
- ID: TRACK_038
- Repository: MyMCP
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_038_COMPLETED_plugin_capability_version_governance.md

Problems (PORE)
- P1: As a plugin consumer, I cannot tell that Mnemosyne's implementation and
  memory_recall contract changed in TRACK_037, because the plugin remained
  `0.1.0` and memory_recall remained `1.0.0` even though its public input schema
  gained an optional namespace_id.
- P2: As a maintainer, I can change a Tool definition while leaving its declared
  capability version stale, because manifest/adapter parity proves only that two
  declarations agree; it does not couple a capability version to the definition
  whose semantic compatibility that version represents.
- P3: As a future installer or lifecycle manager, I cannot rely on plugin and
  capability versions in installation receipts, compatibility checks, updates,
  or rollback if bundled development does not already apply those versions
  consistently.

Objective
- Correct the Mnemosyne and memory_recall versions after TRACK_037 and establish
  explicit per-capability declarations, automated contract/version drift
  detection, and a mandatory version-impact review so future public MCP changes
  cannot silently retain stale semantic versions.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing
  implementation, then refactoring and validation.
- MyMCP's host/package/server marker remains `0.2.1`; this Track changes
  plugin-owned semantic versions, not host, endpoint, MCP protocol, host-plugin
  API, manifest schema, configuration schema, plugin-data schema, runtime
  generation, or record schema versions.
- Mnemosyne plugin identity remains `mnemosyne`; every public memory_* name,
  binding, schema, result, error, effect/consent classification, configuration,
  storage, record, logging, and mutation boundary remains unchanged.
- Only memory_recall's capability-contract version advances; the other seven
  capability contracts remain `1.0.0`.
- Manifest and trusted-adapter definitions must retain exact parity and startup
  must continue to fail closed on version disagreement.
- Enforcement must make a Tool-definition change under an existing capability
  version fail an automated test and must keep the required version decision
  review-visible; workflow prose alone is insufficient.
- Roadmap mutation remains separately approval-gated. Detailed execution history
  stays in this Track, Git, and the changelog rather than roadmap snapshots.
- Automated tests are required; direct MCP checks supplement and do not replace
  them.

Acceptance criteria
- [x] A1) [P1] The packaged manifest, trusted adapter definition, contribution,
  runtime inventory, and focused compatibility tests agree on Mnemosyne plugin
  version `0.2.0`.
- [x] A2) [P1] memory_recall alone declares capability-contract version `1.1.0`;
  memory_list, memory_inspect, memory_archive, memory_restore, memory_remember,
  memory_revise, and memory_forget remain `1.0.0`.
- [x] A3) [P2] The implementation has no single shared capability-version value
  that can silently stamp every Tool; each capability's version is explicit and
  reviewable in the canonical declaration path.
- [x] A4) [P2] A focused automated guard couples each current Mnemosyne Tool
  definition to its declared capability-contract version through the approved
  version-keyed canonical-JSON digest ledger, fails when a Tool definition drifts
  from its selected entry, and preserves prior entries for reviewable history.
- [x] A5) [P2] Project workflow requires every public MCP contract change to
  record an explicit impact decision against the canonical identity/version model,
  including distribution, endpoint marker, MCP protocol, host-plugin API,
  manifest schema, worker protocol, plugin, capability-contract, configuration,
  plugin-data, runtime-generation, and record-schema dimensions, with an approved
  reason for every unchanged relevant layer.
- [x] A6) [P3] Architecture and glossary documentation explain that Phase 3A
  receipts and Phase 3C update/rollback consume author-declared plugin and
  capability versions but cannot infer a missed increment; current bundled
  governance is therefore a prerequisite.
- [x] A7) Existing manifest parsing, definition/contribution parity, bootstrap,
  production compatibility, packaging, and all memory_* behavior remain green.
- [x] A8) The complete automated suite, whitespace/link checks, package-content
  validation, and direct read-only discovery pass with no host marker or public
  Tool behavior change.
- [x] A9) The living MyMCP roadmap is reconciled under separate user approval:
  version governance is recorded as a Phase 3A prerequisite, then retained as a
  delivered prerequisite when this Track completes; no per-edit roadmap snapshot
  history is created.

Why now / impact
- TRACK_037 correctly preserved MyMCP `0.2.1` but its version review did not
  inspect the independently owned plugin and capability-contract layers. The
  existing parity boundary accepted matching stale declarations. Correcting the
  versions now, before native installation and lifecycle work consume them,
  prevents unreliable receipts and compatibility decisions from becoming part of
  Phase 3.

Scope
- In scope:
  - Mnemosyne plugin version correction in its packaged manifest and trusted
    adapter definition/contribution.
  - A memory_recall-only capability-contract minor increment.
  - Explicit per-capability version declarations in the canonical Mnemosyne
    declaration table.
  - A focused, reviewable Tool-definition/version snapshot or ledger guard,
    including a preserved memory_recall `1.0.0` baseline and current `1.1.0`
    contract.
  - Exact manifest, adapter, contribution, runtime, bootstrap, packaging, and
    compatibility tests.
  - Version-impact gates in `.backlog/README.md`, `docs/AI_WORKFLOW.md`, and the
    applicable root/plugin guidance.
  - Public architecture/glossary/status documentation needed to distinguish host,
    plugin, and capability versions and their roadmap role.
  - Separately approved living-roadmap reconciliation and final changelog memory
    after commit/push.
- Out of scope:
  - A MyMCP host/package/server version increment or release.
  - Any memory_recall or other memory_* schema/result/error/behavior change.
  - Host-plugin API, manifest format, worker protocol, configuration schema,
    plugin-data schema, record schema, policy revision, or runtime-generation
    changes.
  - Native installation receipts, external activation, update/rollback,
    migration, public metadata projection, or general plugin lifecycle
    implementation.
  - Generic semantic-version inference from arbitrary Python behavior or result
    semantics; the automated guard covers declared Tool definitions while the
    mandatory impact review covers the complete public contract.
  - Reconstructing or storing every historical living-roadmap revision.

Milestones
- [x] M1) Version correction: plugin and memory_recall capability versions are
  independently correct across manifest, definition, contribution, and runtime.
- [x] M2) Drift prevention: explicit per-capability declarations and automated
  definition/version coupling are enforced.
- [x] M3) Governance: Track/workflow guidance requires a complete version-impact
  decision for public contract changes.
- [x] M4) Validation and documentation: focused/full/package/direct checks pass
  and public version ownership is documented.
- [x] M5) Roadmap reconciliation and completion are approved and recorded.

Risks / decisions
- Risk: A single `_CAPABILITY_VERSION` currently stamps all eight declarations;
  changing it would incorrectly version seven unchanged contracts. Mitigation:
  make each declaration carry its own explicit version before applying the
  memory_recall increment.
- Risk: Manifest/adapter parity can validate two equally stale declarations.
  Mitigation: couple the selected declaration version to a versioned Tool-
  definition snapshot or ledger in focused tests.
- Risk: A digest-only guard can be opaque during review, while a complete
  snapshot of large composed schemas can be noisy. Mitigation: resolve the exact
  readable bounded representation before activation and preserve historical
  entries rather than rewriting an existing version's contract identity.
- Risk: Tool definitions do not declare complete runtime result/error semantics.
  Mitigation: automated definition drift detection supplements, not replaces, the
  mandatory complete version-impact decision and focused behavioral tests.
- Decision: Treat TRACK_037's optional namespace_id as backwards-compatible new
  functionality: Mnemosyne plugin `0.1.0` -> `0.2.0` and memory_recall capability
  `1.0.0` -> `1.1.0`; keep MyMCP `0.2.1` and all other capability versions.
- Decision: Do not rewrite TRACK_037 or its changelog event. TRACK_038 records the
  correction and its rationale as a separate auditable outcome.
- Decision: This is a corrective prerequisite for Phase 3A, not a new roadmap
  phase and not implementation of installation or lifecycle behavior.

Open questions
- [x] Q1) Use a test-owned, version-keyed canonical-JSON SHA-256 digest ledger
  with bounded readable properties/required-field fingerprints. Preserve prior
  entries by rule; the guard detects definition drift while Git review protects
  historical ledger entries from being rewritten.
- [x] Q2) Keep capability versions in the canonical plugin declaration table,
  with an explicit version on every capability row and no shared stamp. The table
  couples each local identity, version, effects, and consent without adding
  imports to leaf Tool definitions or generic plugin modules.
- [x] Q3) Enforce the impact gate in root `AGENTS.md`, `.backlog/README.md`,
  `docs/AI_WORKFLOW.md`, and `mymcp/plugins/mnemosyne/AGENTS.md`; also reconcile
  stale version wording in `mymcp/mcp/AGENTS.md`.
- [x] Q4) Revise the one living roadmap before activation because TRACK_038 adds
  a real Phase 3A prerequisite. Revision 8 now records the pending prerequisite;
  completion will revise the same record to retain it as delivered and restore
  Phase 3A as NEXT.

Decision log
- Decision (initial): Correct plugin and memory_recall capability versions without
  changing MyMCP `0.2.1` or any public Tool behavior.
- Decision (initial): Require both an automated definition/version coupling guard
  and a human-reviewable complete version-impact gate.
- Decision (initial): Preserve one living roadmap plus its archived predecessor;
  use Track/Git/changelog evidence for detailed history rather than creating a
  roadmap snapshot per revision.
- Decision (Q1): Use canonical JSON over each complete public TOOL definition,
  SHA-256 it into a version-keyed test ledger, and include bounded properties and
  required-field fingerprints for readable review. The ledger covers declared
  Tool definitions, not complete handler result/error semantics; behavioral tests
  and the version-impact gate cover that residual boundary.
- Decision (Q2): The plugin declaration table remains the canonical owner and
  gives each capability an explicit semantic version beside its local identity
  and metadata. Remove the shared `_CAPABILITY_VERSION`.
- Decision (Q3): The minimum enforcement surface is root guidance, canonical
  backlog gates, AI workflow, and plugin-scoped guidance; MCP-scoped guidance is
  additionally updated because its adapter version becomes stale.
- Decision (Q4): The user approved living-roadmap revision 7 -> 8 before
  activation. It records TRACK_038 as the next Phase 3A prerequisite without
  creating a second roadmap record or snapshot history.

Plan (execution steps)
- [x] S1) Review current version ownership, declaration/parity/runtime tests,
  versioned Tool-definition guard options, and scoped guidance; resolve Q1-Q4;
  obtain separate approval for the exact living-roadmap revision; revise it if
  approved; then move Track 038 to ACTIVE and check this step. No implementation
  before activation.
- [x] S2) TDD declaration/version chunk: add focused failing tests for plugin
  `0.2.0`, memory_recall `1.1.0`, seven unchanged `1.0.0` capability versions,
  exact manifest/adapter/contribution/runtime parity, and absence of one shared
  capability-version stamp; implement minimally; refactor; validate; update this
  Track.
- [x] S3) TDD contract-drift chunk: add the approved failing definition/version
  coupling test and historical/current entries; implement the smallest bounded
  snapshot/ledger mechanism; prove same-version Tool-definition drift fails;
  refactor; validate; update this Track.
- [x] S4) Governance/documentation chunk: update the approved workflow, scoped
  guidance, architecture, glossary, README/status, and roadmap references; run
  focused governance/project-identity/documentation checks; update this Track.
- [x] S5) Compatibility chunk: run manifest, parity, bootstrap, runtime,
  production-compatibility, packaging, MCP, memory, and complete suites; run
  whitespace/link/package-content checks and direct read-only discovery; update
  this Track.
- [x] S6) Validate and complete: review A1-A9, reconcile the living roadmap under
  approval so the prerequisite remains recorded as delivered, move this Track to
  COMPLETED, then request separate approval for commit/push and the required
  changelog event.

Current inventory
- `mymcp/plugins/mnemosyne/plugin.py`: `_PLUGIN_VERSION = 0.2.0`; each ordered
  capability declaration carries an explicit version; memory_recall is `1.1.0`
  and the other seven are `1.0.0`; definition and contribution share the table.
- `mymcp/plugins/mnemosyne/manifest.json`: plugin `0.2.0`; memory_recall `1.1.0`;
  seven other capabilities `1.0.0`; host API 1; manifest schema 1;
  configuration/data schema 1.
- `mymcp/plugins/mnemosyne/mcp/tools/*/definition.py`: canonical public Tool
  definitions; memory_recall gained namespace_id in TRACK_037.
- `tests/plugin/test_mnemosyne_manifest.py`: exact plugin version and currently
  uniform capability-version assertions plus manifest/adapter parity.
- `tests/mcp/test_mnemosyne_integration.py`, `tests/host/test_bootstrap.py`, and
  `tests/host/test_runtime.py`: contribution/runtime plugin-version expectations.
- `tests/plugin/test_definition.py`, `test_manifest.py`, `test_parity.py`, and
  `test_contracts.py`: generic strict SemVer, immutable definition, manifest, and
  exact parity behavior.
- `tests/mcp/test_memory_recall.py`: exact current memory_recall Tool definition.
- `tests/plugin/capability_contract_ledger.json`: test-owned version-keyed
  canonical Tool-definition digests plus readable properties/required
  fingerprints; preserves memory_recall `1.0.0` and current `1.1.0`.
- `tests/plugin/test_capability_version_ledger.py`: validates all ledger entries,
  Tool/capability identity and current version coverage, deterministic canonical
  serialization, historical recall preservation, same-version drift failure, and
  missing-version failure.
- `.backlog/README.md`, `docs/AI_WORKFLOW.md`, root `AGENTS.md`, and
  `mymcp/plugins/mnemosyne/AGENTS.md`: complete pre-implementation version-impact
  gates plus explicit per-capability/ledger rules.
- `mymcp/mcp/AGENTS.md`: MCP-scoped guidance now identifies the current
  Mnemosyne `0.2.0` adapter.
- `README.md`, `VISION.md`, `docs/ARCHITECTURE.md`, `docs/GLOSSARY.md`, and
  `docs/PLUGIN_ARCHITECTURE.md`: current host `0.2.1`, plugin `0.2.0`,
  memory_recall `1.1.0`, other-capability `1.0.0`, ledger boundary, and Phase
  3A/3C version-governance prerequisite.

Artifacts
- Corrected predecessor: TRACK_037, commit `9a64203`, added namespace_id to the
  public memory_recall input schema while retaining MyMCP `0.2.1`, Mnemosyne
  `0.1.0`, and capability `1.0.0`.
- Version architecture: TRACK_030 Q10; TRACK_031 plugin-version decision;
  TRACK_032 manifest/capability-version decisions; `docs/PLUGIN_ARCHITECTURE.md`
  Identity and version model plus Phase 3A/3C lifecycle rules.
- Living roadmap: `project/mymcp/roadmaps`, “MyMCP host and gateway roadmap”,
  active revision 9. Under explicit user approval it retains TRACK_038 as a
  delivered Phase 3A prerequisite, records its concise outcome in the delivered
  baseline, and restores Phase 3A native installation as NEXT.
- Historical roadmap: archived `project/mnemosyne/roadmaps`,
  “Mnemosyne-to-MyMCP transition roadmap”. It is a superseded predecessor, not a
  complete revision history of the living roadmap.
- S2 red evidence: the declared manifest, integration, bootstrap, and parity run
  collected 106 tests and produced 20 expected version failures with 86 passes
  before implementation.
- S2 green evidence: the same focused command passed all 106 tests after the
  minimal manifest/adapter correction and explicit per-capability declaration
  refactor; `git diff --check` passed. Independent verification passed the 67
  manifest, integration, and bootstrap tests and found no version, parity,
  runtime, host-marker, or Tool-behavior defect.
- S3 red evidence: the initial ledger-focused run collected four tests and
  produced one expected incomplete-ledger failure with three passes. After the
  first green implementation, independent review identified missing explicit
  determinism and historical-entry shape coverage; the corrective focused red
  run produced three expected failures with five passes before validation was
  added.
- S3 green evidence: the final ledger, manifest, and parity set passed all 62
  tests and `git diff --check` passed. Independent re-review confirmed stable
  canonical digests, structural and semantic-version validation for every
  historical/current entry, allowed history for known Tools, exact current
  definition/version coverage, and no remaining blocker.
- S4 validation evidence: the ledger, manifest, project-identity, and packaging
  set passed 25 tests and `git diff --check` passed. Relative Markdown-link
  review passed. Independent documentation review found no current/historical
  version, ledger-boundary, roadmap-prerequisite, terminology, or link defect.
  Independent guidance review confirmed the complete gate is reachable before
  implementation, exposed by the Track template, accurate against code/tests,
  and non-contradictory. The canonical identity/version table now gives memory
  record schema its own explicit row.
- S5 automated evidence: the declared plugin/manifest/parity/bootstrap/runtime,
  production-compatibility, packaging, complete MCP, and complete memory set
  passed 807 tests. The complete repository suite passed 1,162 tests;
  repository-wide relative Markdown links and `git diff --check` passed.
  Configured-client validation remains pending because the running process
  predates the current plugin-version implementation and plugin/capability
  versions are intentionally not projected publicly; a restart from the current
  working tree is required before the direct unchanged-surface check is valid.
- S5 direct evidence: after the user restarted MyMCP from the current working
  tree, configured-client `list_tools` reported the unchanged `mymcp 0.2.1`
  ordered nine-Tool surface. A read-only project recall succeeded and returned
  the revision-8 living roadmap as the leading match, confirming the unchanged
  memory Tool path and recorded TRACK_038 prerequisite. Plugin and capability
  versions remain intentionally absent from public MCP projection; their exact
  values are verified through manifest/definition/contribution/runtime tests. No
  mutation Tool was called.
- S6 review evidence: independent acceptance review passed A1-A8, reran 373
  focused tests and all 1,162 tests, and found only the expected approval-gated
  roadmap/completion transition outstanding. Independent repository review found
  only intended Track files, no host/package version change, historical rewrite,
  secret, unrelated change, or whitespace defect. Packaging review generated
  temporary `build/` and `dist/` directories; both were removed and verified
  absent before completion.
- S6 roadmap evidence: the first approved revision-9 proposal exceeded the
  4,000-character record bound and was rejected without changing revision 8. A
  separately approved bounded retry succeeded as revision 9, retaining the
  delivered prerequisite and restoring Phase 3A as NEXT.

Completion notes
- S2 completed: Mnemosyne is `0.2.0`; memory_recall alone is capability contract
  `1.1.0`; seven unchanged capabilities remain `1.0.0`; the shared capability
  version stamp is removed; manifest, definition, contribution, runtime, gates,
  effects/consent, and public Tool behavior remain aligned.
- S3 completed: a test-owned canonical-JSON digest ledger now binds each current
  Tool definition to its declared capability version, retains the pre-namespace
  memory_recall `1.0.0` contract beside `1.1.0`, exposes readable top-level
  fingerprints, and fails focused tests for same-version drift, missing entries,
  malformed history, identity mismatch, or incomplete capability coverage.
- S4 completed: project-wide, backlog, AI-workflow, plugin, and MCP guidance now
  require a complete version-impact decision and applicable guard before public
  contract implementation/completion. Current documentation distinguishes MyMCP
  `0.2.1`, Mnemosyne `0.2.0`, memory_recall `1.1.0`, and seven `1.0.0`
  capabilities, and records why Phase 3A/3C cannot infer missed increments.
- S5 automated validation is complete with 807 focused/broad and 1,162 full-suite
  tests passing plus package, link, and whitespace checks. Post-restart direct
  configured-client discovery and read-only recall passed with the unchanged
  host marker and Tool surface.
- S6 completed: all acceptance criteria and milestones pass; final automated,
  package, link, whitespace, direct MCP, independent acceptance, and repository
  reviews pass; the roadmap is reconciled at revision 9; and Track 038 moved to
  COMPLETED with synchronized title, filename, path, and status.
- No commit, push, release, or changelog memory was performed. Those remain
  separate exact approval gates.

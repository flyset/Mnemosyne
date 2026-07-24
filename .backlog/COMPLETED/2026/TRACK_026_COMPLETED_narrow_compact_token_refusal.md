# TRACK 026 [COMPLETED]: Narrow compact-token refusal

Track
- ID: TRACK_026
- Repository: MyMCP (hosting the Mnemosyne memory domain in-process)
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_026_COMPLETED_narrow_compact_token_refusal.md

Problems (PORE)
- P1: As a user preserving ordinary project history, I cannot store benign three-part versions such as `0.1.3`, because the compact-token signature treats every three dot-separated alphanumeric sequence as a possible token.
- P2: As a user relying on no-secret handling, I still need realistic compact authentication tokens refused before storage, because narrowing the false-positive-prone signature must not remove the bounded credential safety boundary.

Objective
- Narrow compact-token detection so ordinary dotted versions and similar benign text are accepted while realistic compact tokens remain deterministically refused without exposing matched values.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Preserve local-first, single-user, least-privilege, explicit-tool, and per-call consent boundaries.
- Preserve deterministic first-match classification, bounded `field` and `reason` diagnostics, rejected-value non-retention, content-free logs, and policy evaluation before storage access.
- Do not weaken declared private-key, credential, payment-card, or government-identifier signatures.
- Do not claim complete semantic secret detection; this remains a bounded signature policy.

Acceptance criteria
- [x] A1) [P1] Remember and revision policy accept ordinary numeric three-part versions including `0.1.3`, `1.25.0`, and `2026.07.23` in otherwise valid content.
- [x] A2) [P1] Public `memory_remember` and `memory_revise` no longer return `compact_token_shape` solely because content contains an accepted dotted version.
- [x] A3) [P2] A realistic three-part compact token remains classified as `compact_token_shape` before any storage access.
- [x] A4) [P2] Credential-shaped text that also contains a compact token retains deterministic earlier `credential_shape` classification.
- [x] A5) [P1, P2] Refusals continue to expose only bounded field/reason/remediation metadata and retain no rejected value, segment, offset, regex, path, or exception detail.
- [x] A6) [P1, P2] README, architecture, glossary, Tool descriptions, and compatibility version are updated only where the final public behavior requires it.
- [x] A7) [P1, P2] Focused, full, whitespace, and direct MCP validation pass.

Why now / impact
- Track 025's required changelog event was refused twice because its benign `0.1.3` compatibility version matched the broad compact-token regex. The workaround spelled the version in words, demonstrating a concrete usability problem in normal project-history storage.

Scope
- In scope:
  - Characterize benign dotted-version and realistic compact-token cases at domain and MCP adapter boundaries.
  - Replace or constrain the current broad three-segment compact-token signature with the narrowest justified recognizer.
  - Preserve policy ordering and refusal projection for remember and revise.
  - Remove tests that require ordinary dotted versions to be refused and replace them with regression coverage for accepted versions.
  - Update affected public documentation and compatibility markers if required by the final behavior.
- Out of scope:
  - General semantic DLP, entropy scoring, network validation, token introspection, or provider-specific expansion unrelated to this false positive.
  - Storing confirmed secrets, weakening other signature categories, or returning the matched substring.
  - Changing memory schemas, Tool argument/result shapes, storage layout, mutation enablement, consent, or lifecycle behavior.
  - Plugin extraction, host configuration changes, or unrelated refactoring.

Milestones
- [x] M1) Current false positive and required true positives are fixed by focused tests.
- [x] M2) Compact-token recognition is narrowly corrected without weakening policy ordering or bounded diagnostics.
- [x] M3) Documentation and complete validation establish the revised public behavior.

Risks / decisions
- Risk: A simple numeric-version exemption may leave other common dotted identifiers falsely blocked.
- Mitigation: Choose the recognizer from positive token evidence rather than accumulating unrelated exemptions.
- Risk: Length-only thresholds may miss short synthetic cases or still reject benign long dotted text.
- Mitigation: Compare explicit structural evidence, bounded segment rules, and representative near misses before selecting the implementation.
- Risk: Strong JWT-specific recognition may narrow beyond the intended generic compact-token category.
- Mitigation: Record the supported signature boundary honestly and retain tests for every claimed positive class.
- Decision: This Track fixes a demonstrated false positive; it does not attempt complete secret detection.

Open questions
- [x] Q1) What minimum structural evidence should distinguish a realistic compact token: bounded segment lengths, base64url/JWT-header evidence, or another small deterministic rule?
- [x] Q2) Which benign dotted forms beyond numeric three-part versions must be accepted to avoid implementing only a one-example exception?
- [x] Q3) Does this public policy correction require compatibility build `0.1.4`?

Decision log
- Decision (Q1): The recognizer requires positive JOSE compact-serialization evidence: a first segment beginning `eyJ` (the base64url encoding of `{"` that starts every JOSE JSON header) with at least eight further base64url characters, followed by two non-empty base64url segments. Length-only or entropy rules were rejected because they either miss short synthetic cases or still refuse benign long dotted text; the supported positive class is honestly bounded to JOSE-header-shaped compact tokens, and longer JWE serializations still match through their first three segments.
- Decision (Q2): No benign-form exemption list exists; acceptance follows from requiring positive token evidence. Regression coverage locks in numeric versions (`0.1.3`, `1.25.0`), calendar dates (`2026.07.23`), semver prerelease (`1.0.0-rc.1`), module paths (`mymcp.memory.policy`), and hostnames (`api.example.com`) at the domain boundary plus dotted-version acceptance through public remember and revise.
- Decision (Q3): Yes. Every prior public-behavior change to the Tool surface bumped the compatibility patch version (most recently Track 022's refusal diagnostics delivering `0.1.3`), and this Track changes which public remember/revise content is accepted, so the compatibility build becomes `0.1.4` in `pyproject.toml` and `mymcp/settings.py` together.

Plan (execution steps)
- [x] S1) Move TRACK_026 to ACTIVE (folder, filename, title, and current path) and check this step before implementation.
- [x] S2) Execute the compact-token characterization TDD chunk: replace the current version-refusal expectations with focused failing domain and MCP remember/revise tests for accepted benign versions, retain realistic compact-token and first-match refusal tests, run the red evidence, and update this Track.
- [x] S3) Execute the matcher-narrowing TDD chunk: resolve Q1 and Q2, implement the smallest deterministic compact-token recognizer that passes the characterized boundary, refactor without broadening scope, run focused policy/service/Tool validation, and update this Track.
- [x] S4) Resolve Q3, update affected public documentation and compatibility markers, run the complete automated suite and whitespace validation, perform direct MCP checks without storing suspected sensitive content, review all acceptance criteria, and update this Track.
- [x] S5) Move TRACK_026 to COMPLETED (folder, filename, title, and current path), check this transition, and record completion outcomes.

Current inventory
- `mymcp/memory/policy.py` now defines `COMPACT_TOKEN_SHAPE` with the JOSE-evidence recognizer of Decision (Q1); the previous regex matched any three non-empty dot-separated `[A-Za-z0-9_-]+` segments without length, encoding, semantic, or numeric-version distinctions.
- `validate_remember_content()` and `validate_revision_content()` apply the same ordered signature list to every caller-owned free-form field before payment-card checks and before service storage access.
- `mymcp/memory/errors.py` exposes only the broad `compact_token_shape` reason through `DisallowedMemoryContent`, without retaining the rejected value.
- `mymcp/mcp/tools/_memory_content_refusal.py` provides stable safe-review guidance without identifying the matching substring.
- `tests/memory/test_policy.py::test_remember_policy_classifies_dotted_version_as_compact_token_shape` explicitly requires `Compatibility build 0.1.0` to be refused; the declared-sensitive-signature matrix separately protects a realistic three-part encoded token.
- `tests/mcp/test_memory_remember.py::test_memory_remember_classifies_dotted_version_without_source_access` requires the same false-positive refusal at the Tool boundary.
- `tests/mcp/test_memory_revise.py` protects compact-token reason projection for revision, while policy/service tests protect pre-storage refusal, first-match ordering, and rejected-value non-retention.
- TRACK_025 completed and was pushed in commit `76a7ee8`; its changelog event succeeded only after replacing dotted compatibility notation with words.

Artifacts
- Triggering event: Track 025 changelog remember calls refused `content` with reason `compact_token_shape` while the content contained compatibility version `0.1.3`.
- Related completed Track: `.backlog/COMPLETED/2026/TRACK_022_COMPLETED_actionable_disallowed_content_refusals.md`.
- Related completed Track: `.backlog/COMPLETED/2026/TRACK_025_COMPLETED_mnemosyne_configuration_ownership.md`.

Completion notes
- 2026-07-24: Moved to ACTIVE (S1) after recording the Tracks 029/030 changelog event.
- 2026-07-24: Completed S2. Replaced the dotted-version refusal expectations with characterization coverage: domain remember/revision policy acceptance for `0.1.3`, `1.25.0`, `2026.07.23`, `1.0.0-rc.1`, `mymcp.memory.policy`, and `api.example.com`; an MCP remember acceptance test storing dotted-version content; an MCP revise acceptance test revising to dotted-version content; a retained MCP remember compact-token refusal test using the realistic `eyJ` three-segment token with no storage access; a two-segment `eyJ` near miss; and a first-match test whose rejected value now contains both a credential signature and a realistic compact token. Red evidence: exactly the 14 new acceptance tests fail with `compact_token_shape`; all 159 retained tests pass, including declared-sensitive signatures, first-match ordering, and rejected-value non-retention. S3 matcher narrowing is next.
- 2026-07-24: Completed S3. Replaced the broad any-three-dot-separated-segments regex in the policy signature list with a JOSE-evidence recognizer per Decision (Q1); the change is one pattern plus a bounding comment, policy ordering, bounded diagnostics, and non-retention are untouched, and no further refactor was justified. All 14 red acceptance tests now pass with every retained refusal test; complete memory and MCP validation passed 661 tests. S4 documentation, Q3 resolution, and complete validation are next.
- 2026-07-24: Completed S4. Resolved Q3 as yes and bumped the compatibility build to `0.1.4` through a focused failing version test, `mymcp/settings.py`, `pyproject.toml`, and the five discovery-marker test strings. Updated the README policy paragraph and stale dotted-version retry example, the README discovery marker, and the glossary Remember content policy entry to state the JOSE-evidence boundary; architecture documentation and Tool descriptions contained no stale wording and are unchanged. The complete automated suite passed 775 tests; `git diff --check` reported no whitespace problems. Direct MCP checks against a freshly started server on a scratch memory root confirmed `/version` and `list_tools` report `mnemosyne 0.1.4` with the ordered nine-Tool surface, dotted-version content is remembered, and a synthetic three-segment `eyJ` token is refused as `compact_token_shape` with bounded metadata and nothing stored; the scratch server was stopped afterward. All acceptance criteria and milestones pass. S5 completion transition is the only remaining step.
- 2026-07-24: Completed TRACK_026. Compact-token refusal now requires positive JOSE compact-serialization evidence, so ordinary dotted versions, dates, hostnames, and module paths are stored normally while realistic `eyJ`-headed three-segment tokens remain deterministically refused before storage with unchanged bounded diagnostics, first-match ordering, non-retention, and content-free logs. The compatibility build is `0.1.4`. Evidence: 14 red characterization tests turned green, 775 total tests pass, whitespace validation is clean, and direct MCP checks verified the new accept/refuse boundary end to end. This Track is not roadmap-derived; the living MyMCP host and gateway roadmap was inspected during activation and remains current, with the kind-qualified runtime foundation still the next phase. Commit, push, and the changelog event follow separately.

# TRACK 026 [DRAFT]: Narrow compact-token refusal

Track
- ID: TRACK_026
- Repository: MyMCP (hosting the Mnemosyne memory domain in-process)
- Branch: main
- Current path: .backlog/DRAFT/2026/TRACK_026_DRAFT_narrow_compact_token_refusal.md

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
- [ ] A1) [P1] Remember and revision policy accept ordinary numeric three-part versions including `0.1.3`, `1.25.0`, and `2026.07.23` in otherwise valid content.
- [ ] A2) [P1] Public `memory_remember` and `memory_revise` no longer return `compact_token_shape` solely because content contains an accepted dotted version.
- [ ] A3) [P2] A realistic three-part compact token remains classified as `compact_token_shape` before any storage access.
- [ ] A4) [P2] Credential-shaped text that also contains a compact token retains deterministic earlier `credential_shape` classification.
- [ ] A5) [P1, P2] Refusals continue to expose only bounded field/reason/remediation metadata and retain no rejected value, segment, offset, regex, path, or exception detail.
- [ ] A6) [P1, P2] README, architecture, glossary, Tool descriptions, and compatibility version are updated only where the final public behavior requires it.
- [ ] A7) [P1, P2] Focused, full, whitespace, and direct MCP validation pass.

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
- [ ] M1) Current false positive and required true positives are fixed by focused tests.
- [ ] M2) Compact-token recognition is narrowly corrected without weakening policy ordering or bounded diagnostics.
- [ ] M3) Documentation and complete validation establish the revised public behavior.

Risks / decisions
- Risk: A simple numeric-version exemption may leave other common dotted identifiers falsely blocked.
- Mitigation: Choose the recognizer from positive token evidence rather than accumulating unrelated exemptions.
- Risk: Length-only thresholds may miss short synthetic cases or still reject benign long dotted text.
- Mitigation: Compare explicit structural evidence, bounded segment rules, and representative near misses before selecting the implementation.
- Risk: Strong JWT-specific recognition may narrow beyond the intended generic compact-token category.
- Mitigation: Record the supported signature boundary honestly and retain tests for every claimed positive class.
- Decision: This Track fixes a demonstrated false positive; it does not attempt complete secret detection.

Open questions
- [ ] Q1) What minimum structural evidence should distinguish a realistic compact token: bounded segment lengths, base64url/JWT-header evidence, or another small deterministic rule?
- [ ] Q2) Which benign dotted forms beyond numeric three-part versions must be accepted to avoid implementing only a one-example exception?
- [ ] Q3) Does this public policy correction require compatibility build `0.1.4`?

Decision log
- Decision: Pending focused policy inventory and TDD evidence.

Plan (execution steps)
- [ ] S1) Move TRACK_026 to ACTIVE (folder, filename, title, and current path) and check this step before implementation.
- [ ] S2) Execute the compact-token characterization TDD chunk: replace the current version-refusal expectations with focused failing domain and MCP remember/revise tests for accepted benign versions, retain realistic compact-token and first-match refusal tests, run the red evidence, and update this Track.
- [ ] S3) Execute the matcher-narrowing TDD chunk: resolve Q1 and Q2, implement the smallest deterministic compact-token recognizer that passes the characterized boundary, refactor without broadening scope, run focused policy/service/Tool validation, and update this Track.
- [ ] S4) Resolve Q3, update affected public documentation and compatibility markers, run the complete automated suite and whitespace validation, perform direct MCP checks without storing suspected sensitive content, review all acceptance criteria, and update this Track.
- [ ] S5) Move TRACK_026 to COMPLETED (folder, filename, title, and current path), check this transition, and record completion outcomes.

Current inventory
- `mymcp/memory/policy.py` defines `COMPACT_TOKEN_SHAPE` with a regex matching any three non-empty dot-separated `[A-Za-z0-9_-]+` segments, without length, encoding, semantic, or numeric-version distinctions.
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
- Not started; Track is DRAFT and implementation is prohibited.

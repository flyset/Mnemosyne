# TRACK 022 [COMPLETED]: actionable disallowed-content refusals

Track
- ID: TRACK_022
- Repository: Mnemosyne
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_022_COMPLETED_actionable_disallowed_content_refusals.md

Problems (PORE)
- P1: As an MCP caller without repository-source access, I cannot safely recover from a benign `disallowed_content` false positive, because the current refusal identifies neither the caller-owned field nor a bounded reason category.
- P2: As a user governing durable memory, I need actionable refusal diagnostics without rejected values being repeated or retained, because returning matches, offsets, detector rules, or submitted content would expand sensitive-data exposure.
- P3: As an agent operating in another project or client, I cannot rely on source-code inspection to interpret a refusal, because the public Tool contract and result do not currently provide self-contained remediation guidance.

Objective
- Make remember and revision content-policy refusals safely actionable through bounded, non-content-bearing field and reason metadata plus self-contained retry guidance, without weakening refusal policy or storage boundaries.

Non-negotiables
- This Track remains planning-only while DRAFT; no implementation or implementation-driving tests begin until the Track is moved to ACTIVE and its Move-to-ACTIVE step is checked.
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- The shared `mnemosyne/memory/` domain continues to own content-policy classification; MCP adapters only map bounded domain metadata to their public request fields and Tool results.
- Refusals return only the first detected caller-owned field and one broad stable reason. They never return or retain the matched value, tag index, character offset, regex, detector identifier, fingerprint, or exception detail.
- Refusal metadata must not require repository access to interpret. Tool descriptions and public documentation must explain safe remediation.
- Guidance must never encourage obfuscating suspected sensitive data. A retry is appropriate only after the user confirms that the formatting is benign and approves the exact revised call.
- Existing refusal-before-storage behavior, mutation gates, exact per-call consent, local-first assumptions, and content-free logging remain unchanged.
- No commit or push occurs unless explicitly requested.

Acceptance criteria
- [x] A1) [P1, P2] Shared remember and revision policy raises a bounded refusal carrying exactly one canonical caller-owned field and one reason from the fixed broad reason vocabulary, while retaining no rejected value or match object.
- [x] A2) [P1, P3] `memory_remember` returns `status`, `code`, bounded `field`, bounded `reason`, and stable remediation `message` for content refusal; the result remains a Tool error and contains no submitted value or storage detail.
- [x] A3) [P1, P3] `memory_revise` returns the same refusal shape and maps canonical nested domain fields to its flat public replacement fields without changing its input schema.
- [x] A4) [P1, P2] The fixed public reason vocabulary is `private_key_shape`, `credential_shape`, `compact_token_shape`, `payment_card_shape`, and `government_identifier_shape`; provider-specific detector details remain private.
- [x] A5) [P1, P3] A regression using benign `0.1.0` content returns `field: content` and `reason: compact_token_shape`, allowing a caller to request user-approved rewording without source inspection.
- [x] A6) [P2] Automated tests prove refusals still occur before discovery/read/write and that Tool results and logs omit the rejected value, nested match details, paths, fingerprints, exception text, and tracebacks.
- [x] A7) [P3] Remember and revise Tool descriptions plus `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` document the exact result shape, reason vocabulary, first-match rule, privacy boundary, and safe retry guidance.
- [x] A8) [P1, P2, P3] The compatibility build is advanced from `0.1.2` to `0.1.3`; focused tests, the full suite, whitespace validation, and isolated direct MCP checks pass.

Why now / impact
- The Track 007 changelog migration exposed a benign false positive when compatibility build `0.1.0` matched the compact-token detector. Diagnosing it required reading `policy.py`, which an ordinary MCP caller or another project model may not be able to do.
- The current generic refusal is intentionally non-disclosing but too opaque for portable recovery. Bounded field and broad-reason metadata can preserve privacy while making the public Tool contract sufficient for safe user-guided remediation.

Scope
- In scope:
  - Bounded first-match field and reason classification in the shared content policy.
  - Safe metadata on `DisallowedMemoryContent` without retaining rejected values or match objects.
  - Public result mapping for `memory_remember` and `memory_revise`.
  - Canonical-to-public field mapping for nested remember dimensions and flat revision replacements.
  - Self-contained Tool descriptions and stable remediation language.
  - Focused domain, service, MCP adapter, logging, compatibility-marker, and direct protocol coverage.
  - Public documentation and compatibility patch-version updates.
- Out of scope:
  - A separate validation or content-scanning Tool.
  - Returning matched text, offsets, regular expressions, detector names, fingerprints, or tag indexes.
  - Automatically rewording, approving, or retrying a refused request.
  - Weakening, removing, or materially broadening the current detector signatures.
  - Provider-specific public reason categories.
  - Input-schema, memory-record-schema, storage-layout, mutation-gate, permission, or lifecycle changes.
  - Historical Track rewrites or background memory migration.

Milestones
- [x] M1) Domain field/reason semantics and privacy invariants pass focused TDD.
- [x] M2) Remember and revise expose the same actionable bounded refusal contract through focused TDD.
- [x] M3) Tool guidance, documentation, compatibility build, full validation, and isolated direct checks are complete.

Risks / decisions
- Risk: Diagnostic metadata can become an oracle for policy evasion; reasons therefore remain broad, first-match only, and accompanied by guidance prohibiting obfuscation of suspected sensitive data.
- Risk: Returning a nested field path or tag index could disclose unnecessary structure; public results use only bounded caller-visible field names.
- Risk: Different remember and revision field shapes could drift; the domain retains canonical fields and each MCP adapter owns an explicit bounded mapping.
- Risk: Adding keys to Tool errors is a public compatibility change even though request schemas and successful results remain unchanged.
- Risk: Pattern overlap makes classification order observable; first-match precedence must be deterministic and tested without publishing detector-level detail.
- Decision: The public metadata keys are `field` and `reason`.
- Decision: The public reason vocabulary is limited to the five categories named in A4.
- Decision: Refusals report only the first match and never include a matched value, position, pattern, fingerprint, or tag index.
- Decision: Refusal diagnostics belong in the existing remember/revise Tool error rather than a new Tool.
- Decision: Logs retain their current content-free operational purpose and do not add the refusal reason or rejected value.
- Decision: The stable remediation message tells callers to review the named field and retry only when the user confirms that the formatting is benign.

Open questions
- [x] Q1) Should the result use `field` plus `reason`, or expose a matched value? Use bounded `field` plus broad `reason`; never expose the match.
- [x] Q2) Should the server return every match? Return only the deterministic first match.
- [x] Q3) Should tags identify an array index? No; return only the top-level `tags` field.
- [x] Q4) Should the change add a validation Tool? No; enrich the existing refusal result.
- [x] Q5) Should logs include reason metadata? No; keep current minimized operational logging and test that no rejected data appears.
- [x] Q6) Does this require a compatibility marker change? Yes; advance the patch build to `0.1.3` because Tool error results and descriptions are public contract.

Decision log
- Decision (user-approved planning direction): An external model should be able to understand a benign false positive from the MCP contract without reading repository source.
- Decision (privacy boundary): Actionability comes from bounded caller-visible field and broad category metadata, not from echoing content or detector internals.
- Decision (safe retry): The server does not authorize policy evasion; the user must identify the formatting as benign and approve every exact reformulated call.

Plan (execution steps)
- [x] S1) Move Track 022 to ACTIVE (folder, filename, title, and current path) and check this step before implementation begins.
- [x] S2) Execute one TDD chunk for shared first-match field/reason classification, enriched `DisallowedMemoryContent`, deterministic precedence, and no retained rejected value.
- [x] S3) Execute one TDD chunk for `memory_remember` result mapping, safe Tool guidance, `0.1.0` regression behavior, and content-free refusal logging.
- [x] S4) Execute one TDD chunk for `memory_revise` canonical-to-flat field mapping, matching result/guidance behavior, and content-free refusal logging.
- [x] S5) Update `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md`; advance the compatibility build to `0.1.3`; run focused and full automated validation, whitespace checks, and isolated direct MCP refusal checks.
- [x] S6) Confirm all acceptance criteria and milestones, move Track 022 to COMPLETED with synchronized status, and record final outcomes and evidence.

Current inventory
- `mnemosyne/memory/errors.py` now defines the five-value `ContentRefusalReason` string enum. `DisallowedMemoryContent` retains only canonical field and reason metadata while its exception arguments remain the bounded `disallowed_content` code.
- `mnemosyne/memory/policy.py` now pairs every signature with one broad reason, yields canonical field/value pairs, reports the deterministic first match, and discards regex matches and submitted values. Payment-card classification remains a separate bounded Luhn check.
- `MemoryService.remember()` and `MemoryService.revise()` continue applying content policy before duplicate discovery or storage read/write respectively and propagate the enriched domain refusal unchanged.
- `mnemosyne/mcp/tools/memory_remember/handler.py` now maps canonical namespace and collection refusal fields to bounded top-level public names, returns field/reason plus stable safe-retry guidance, and leaves refusal logs unchanged without field, reason, or rejected content.
- `mnemosyne/mcp/tools/_memory_revise.py` now maps canonical refusal fields to flat replacement names and returns the same bounded field/reason/message shape as remember while keeping revision refusal logs unchanged.
- `mnemosyne/mcp/tools/_memory_content_refusal.py` owns the shared stable remediation message without storage or Tool capability, preventing remember/revise result drift.
- Remember and revise Tool definitions now provide the same self-contained safe refusal guidance. Neither Tool publishes an output schema, and both input schemas remain unchanged.
- `tests/memory/test_policy.py`, `tests/memory/test_service.py`, `tests/mcp/test_memory_remember.py`, and `tests/mcp/test_memory_revise.py` contain the primary policy, ordering, adapter, and content-free logging coverage to extend.
- The compatibility build is now `0.1.3` across `mnemosyne/settings.py`, `pyproject.toml`, the README marker, and registry/startup/list-tools assertions.
- `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` now publish the exact refusal result, field mappings, five broad reasons, deterministic first-match rule, privacy exclusions, safe retry boundary, and private shared-message ownership.
- No registry ordering, Tool enablement, input schema, storage schema, route, permission, or memory migration change is currently required.
- The working tree already contains unrelated user changes in `AGENTS.md` and untracked `MEMORY.md`; this Track must not modify or absorb them.

Artifacts
- Triggering behavior: a changelog event containing benign compatibility build `0.1.0` was refused as compact-token-shaped and succeeded only after user-approved wording changed it to words.
- Historical prerequisites: `.backlog/COMPLETED/2026/TRACK_007_COMPLETED_consent_gated_memory_remember.md`, `.backlog/COMPLETED/2026/TRACK_015_COMPLETED_consent_gated_memory_revision.md`, and `.backlog/COMPLETED/2026/TRACK_021_COMPLETED_event_kind_and_guidance.md`.
- S2 TDD evidence: the focused red run stopped with two collection errors because `ContentRefusalReason` did not exist. The minimal domain implementation then passed all 88 policy/service tests in 0.60 seconds, including every reason family, canonical remember/revision fields, deterministic overlap precedence, benign `0.1.0` classification, no retained rejected value, and refusal-before-storage assertions. `git diff --check` passed.
- S3 TDD evidence: the focused red run collected 63 remember tests and failed 10 cases because the Tool description and refusal result lacked safe guidance, field, reason, and bounded field mapping. The minimal remember adapter/definition implementation then passed all 151 remember/policy/service tests in 0.64 seconds, including nested field projection, benign `0.1.0` classification, unchanged pre-storage refusal, minimized results, and unchanged content-free logs. `git diff --check` passed.
- S4 TDD evidence: the focused red run collected 48 revision tests and failed 7 cases because revision discovery and refusal results lacked safe guidance, flat field mapping, reason, and the shared message. The minimal revision adapter/definition implementation then passed all 199 revise/remember/policy/service tests in 0.39 seconds. All 16 import-boundary tests also passed, and `git diff --check` passed.
- S5 version TDD evidence: after version assertions moved to `0.1.3`, the focused red run produced 15 expected failures with 51 passes because package/server metadata still reported `0.1.2`. Synchronizing `mnemosyne/settings.py` and `pyproject.toml` made all 66 version/registry/startup tests pass in 5.93 seconds.
- S5 automated evidence: all 281 Track-focused policy/service/import/remember/revise/version/registry/startup tests passed in 6.22 seconds; the complete 747-test suite passed in 6.95 seconds; and `git diff --check` passed.
- S5 isolated direct MCP evidence: a temporary server at `127.0.0.1:8773` with remember and revise enabled reported initialize version `0.1.3`; both Tool descriptions exposed bounded refusal and anti-obfuscation guidance; synthetic remember and revise calls containing benign `0.1.0` each returned `refused`, `disallowed_content`, `field: content`, and `reason: compact_token_shape`. Policy refusal occurred before storage, no memory root was created, the server stopped, port 8773 closed, and the temporary directory was removed.

Completion notes
- DRAFT created from the observed cross-client recovery gap. No implementation, implementation-driving test, version change, or public behavior change has begun.
- S1 completed on 2026-07-20: Track 022 moved to ACTIVE with synchronized folder, filename, title, and current path. Implementation may now begin with S2 through focused TDD.
- S2 completed on 2026-07-20 through focused TDD. The shared domain now preserves only canonical source field and broad first-match reason metadata on content refusal, retains no rejected value or match object, and leaves service ordering and storage boundaries unchanged. Public MCP refusal projection remains unchanged pending S3 and S4.
- S3 completed on 2026-07-20 through focused TDD. `memory_remember` now exposes bounded field/reason refusal metadata and self-contained safe retry guidance without echoing rejected values or adding diagnostic data to logs. Revision projection remains unchanged pending S4.
- S4 completed on 2026-07-20 through focused TDD. `memory_revise` now maps canonical refusal fields to its flat public replacement names and exposes the same bounded reason and remediation message as remember. A private capability-free MCP helper owns the shared message; refusal logs remain minimized and unchanged.
- S5 completed on 2026-07-20. Public documentation and Tool guidance now make refusal recovery self-contained without exposing rejected content; compatibility build `0.1.3`, focused/full automated validation, whitespace checks, and isolated direct MCP checks all passed with complete temporary-data cleanup.
- S6 completed on 2026-07-20: all acceptance criteria, milestones, questions, and execution steps are checked; Track 022 moved to COMPLETED with synchronized folder, filename, title, and current path. The delivered outcome is a portable remember/revise refusal contract with bounded first-match field and reason metadata, stable anti-obfuscation guidance, no rejected-content exposure, compatibility build `0.1.3`, and complete automated/direct validation evidence.

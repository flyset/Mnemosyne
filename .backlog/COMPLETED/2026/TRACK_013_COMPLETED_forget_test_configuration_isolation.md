# TRACK 013 [COMPLETED]: forget test configuration isolation

Track
- ID: TRACK_013
- Repository: Mnemosyne
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_013_COMPLETED_forget_test_configuration_isolation.md

Problems (PORE)
- P1: As a contributor with forget enabled in my real local configuration, the automated suite fails, because one Tool-unit test imports the immutable startup registry and assumes ambient forget configuration is disabled.

Objective
- Make forget Tool tests independent of the operator's real settings while preserving isolated default-off and startup-selection coverage.

Non-negotiables
- Follow TDD using the reproduced failing full-suite test as the focused regression.
- Do not alter production forget availability or operator configuration.
- Preserve fresh-process default-off, file/environment enablement, discovery, dispatch, and restart coverage.
- No commit or push unless explicitly requested.

Acceptance criteria
- [x] A1) [P1] `tests/mcp/test_memory_forget.py` does not assert against the ambient immutable startup registry.
- [x] A2) [P1] Isolated registry/startup tests continue to prove default omission and enabled exposure.
- [x] A3) [P1] Focused and full suites pass with the user's real `forget_enabled = true` setting.

Why now / impact
- Enabling the completed forget capability exposed a test-isolation defect immediately; leaving it would make valid operator configuration break development validation.

Scope
- In scope:
  - Remove the redundant ambient-registry assertion.
  - Run focused and full automated validation plus whitespace checks.
- Out of scope:
  - Production behavior, settings parsing, registry behavior, documentation, or user configuration changes.

Milestones
- [x] M1) The isolated regression is fixed without reducing intentional startup coverage.
- [x] M2) Validation passes and the Track is completed.

Risks / decisions
- Decision: Remove rather than monkeypatch the imported global registry because dedicated synthetic registry tests and fresh-process startup probes already cover this behavior deterministically.

Open questions
- [x] Q1) Is the failing assertion redundant with isolated coverage? Yes: `tests/mcp/test_registry.py` and `tests/mcp/test_startup_settings.py` prove default omission and explicit exposure without using real operator settings.

Decision log
- Decision (2026-07-19): Treat ambient startup registry selection as integration state, not a Tool-unit invariant.

Plan (execution steps)
- [x] S1) Create and move Track 013 directly to ACTIVE after reproducing the single failure and approving the exact fix.
- [x] S2) Remove the ambient-config-dependent assertion from `tests/mcp/test_memory_forget.py`.
- [x] S3) Run focused/full validation and `git diff --check`, record evidence, and move the Track to COMPLETED.

Current inventory
- Reproduction with real `~/.mnemosyne/config.toml` containing `forget_enabled = true`: `1 failed, 522 passed`; only `test_memory_forget_default_registry_has_no_startup_exposure` failed.
- The failing test imports `REGISTRY`, whose startup-fixed contents correctly reflect the real enabled setting.
- `test_registry_omits_disabled_forget_from_discovery_and_dispatch` and fresh-process startup tests already provide deterministic default-off coverage.

Artifacts
- Parent capability: `.backlog/COMPLETED/2026/TRACK_012_COMPLETED_consent_gated_physical_memory_deletion.md`.

Completion notes
- Completed on 2026-07-19. Removed only the redundant ambient startup-registry assertion; production behavior and operator configuration were unchanged. Focused forget/registry/startup validation passed `71 passed in 4.82s`, the full suite passed `522 passed in 5.31s` with real `forget_enabled = true`, and `git diff --check` passed with no output. No commit or push was performed.

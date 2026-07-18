# TRACK 008 [COMPLETED]: first-run memory root initialization

Track
- ID: TRACK_008
- Repository: Mnemosyne
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_008_COMPLETED_first_run_memory_root_initialization.md

Problems (PORE)
- P1: As a user enabling `memory_remember` for the first time, I receive `memory_source_unavailable` instead of a stored memory when the default `~/.mnemosyne` application directory does not already exist, because the filesystem store attempts to create `~/.mnemosyne/memory` without first creating its missing parent.
- P2: As an operator, I need first-run initialization to preserve Mnemosyne's least-privilege storage boundary, because automatically creating missing directories must not weaken private permissions, follow unsafe new path components, or make disabled/refused calls mutate the filesystem.

Objective
- Make the first approved enabled remember call lazily initialize a missing memory-root directory chain with private permissions while preserving all default-off, refusal, path-safety, and bounded-error behavior.

Non-negotiables
- This Track remains planning-only while DRAFT; no implementation or implementation-driving tests begin until the Track is moved to ACTIVE and its Move-to-ACTIVE step is checked.
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Directory initialization remains owned by `mnemosyne/memory/`; settings resolution and the MCP handler remain free of filesystem initialization side effects.
- Disabled remember, invalid input, and content-policy refusal must not create the memory root or any parent directory.
- Newly created Mnemosyne-owned directories use private mode `0700` on POSIX; memory files retain mode `0600`.
- Existing directories are not chmodded, rewritten, or otherwise mutated.
- Symlinks and non-directory path components remain rejected through bounded existing errors; no client-supplied path is introduced.
- Automated and direct checks use isolated temporary homes/roots and remove all resulting data.
- No commit or push occurs unless explicitly requested.

Acceptance criteria
- [x] A1) [P1] With no `MNEMOSYNE_MEMORY_ROOT` override and an existing temporary home whose `.mnemosyne` child is absent, one valid enabled remember call returns `remembered` and creates exactly one canonical version-2 record beneath `<home>/.mnemosyne/memory`.
- [x] A2) [P1, P2] The filesystem store creates each missing Mnemosyne-owned directory from the nearest existing ancestor through the record parent before atomic publication; on POSIX every newly created directory is mode `0700` and the record remains mode `0600`.
- [x] A3) [P2] Disabled remember, invalid input, and content-policy refusal continue to create no memory or application directory.
- [x] A4) [P2] Existing directory, symlink, non-directory, atomic-write, and bounded storage-error behavior remains compatible; existing ancestors are not chmodded.
- [x] A5) [P1, P2] Focused automated tests, the full suite, whitespace validation, and an isolated direct MCP first-run check pass, and all temporary memory data is removed.
- [x] A6) [P1, P2] `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` describe lazy private first-run memory-root initialization and its no-write boundaries.

Why now / impact
- Track 007 exposed consent-gated durable creation, but a clean installation can fail on its first approved remember call until the operator manually creates `~/.mnemosyne`. Fixing that defect removes undocumented setup while preserving the existing local-first and least-privilege contract.

Scope
- In scope:
  - Lazy filesystem initialization during canonical record creation only.
  - Missing ancestor creation from the nearest existing directory through the memory root and deterministic record parent.
  - Private modes for newly created directories and unchanged atomic file publication.
  - Store-level and enabled MCP-handler regression coverage for a genuinely absent default application directory.
  - Regression coverage for no-write and path-safety boundaries.
  - Public filesystem-behavior documentation and isolated direct MCP validation.
- Out of scope:
  - Startup-time directory creation or initialization during recall.
  - Changing the default memory-root location or environment variables.
  - Chmodding existing directories, ownership repair, migration, cleanup, or permission auditing.
  - New MCP Tools, schemas, result envelopes, enablement gates, or client permission rules.
  - Support for client-supplied paths, remote storage, multi-user storage, or encryption.

Milestones
- [x] M1) First-run behavior, private-directory semantics, compatibility boundaries, and validation plan are resolved and the Track is eligible for ACTIVE.
- [x] M2) The focused TDD chunk passes at store and enabled MCP-handler boundaries without changing default-off behavior.
- [x] M3) Documentation, full validation, isolated direct MCP evidence, cleanup, and completion transition are recorded.

Risks / decisions
- Risk: `Path.mkdir(parents=True, mode=0o700)` does not reliably apply the requested mode to intermediate parents, so it is insufficient for the private-directory contract.
- Risk: Broadly initializing storage in settings or at server startup would create directories even when mutation is disabled.
- Risk: Automatically chmodding an existing operator-owned ancestor could unexpectedly alter unrelated access policy.
- Risk: New parent-creation logic can introduce symlink traversal or race behavior if it bypasses the store's current component checks.
- Decision: The store will create missing directories individually in parent-to-child order with mode `0700`, while leaving existing directories unchanged.
- Decision: Initialization occurs only on the existing atomic create path after draft validation, content-policy validation, and duplicate discovery.
- Decision: The public Tool schema and remember result/error envelopes remain unchanged.

Open questions
- [x] Q1) What exact helper structure will create a missing ancestor chain while retaining the current `UnsafeMemoryPath` versus `MemorySourceUnavailable` mapping under races, symlinks, and non-directory components?
- [x] Q2) Which focused regression cases are sufficient to prove default-root first-run success, private modes, no-write boundaries, and unchanged existing-ancestor behavior without expanding this Track into general path hardening?
- [x] Q3) What isolated direct MCP sequence will prove default-root initialization without touching the user's real home or retaining synthetic memory?

Decision log
- Decision (observed after Track 007): A first enabled remember call returned `memory_source_unavailable` when the default memory root's parent was absent; manually creating the parent with mode `0700` allowed the call to succeed.
- Decision (initial inspection): `FilesystemMemoryStore._ensure_private_directories()` begins creation at `memory_root` with non-recursive `mkdir`, while its existing mutation test uses `tmp_path / "memory"` whose parent already exists; this explains the uncovered first-run failure.
- Decision (Q1): The store will first validate that the deterministic record parent is beneath `memory_root`. It will collect missing ancestors above `memory_root` only until the nearest existing parent, then create that collected chain and the existing root-to-record chain individually in parent-to-child order with `mkdir(mode=0o700)`. Every component owned by the planned chain is checked for symlink/non-directory conflicts before use and again after `FileExistsError`; dangling symlinks map to `UnsafeMemoryPath`, while ordinary creation and source failures map to `MemorySourceUnavailable`. Existing directories, including the nearest existing ancestor, are accepted without chmod or other mutation. Existing no-overwrite publication, temporary-file cleanup, and post-create reload remain unchanged.
- Decision (Q2): The focused store test will use an existing temporary home with a deliberately absent `.mnemosyne/memory` chain, retain a non-default mode on that existing home, and assert successful canonical creation, unchanged home mode, mode `0700` on every newly created directory, mode `0600` on the record, and no temporary file. The enabled MCP-handler test will unset `MNEMOSYNE_MEMORY_ROOT`, substitute the isolated home through `Path.home()`, and prove a normal `remembered` result plus one default-location record. Existing disabled/refused tests will be tightened to use an absent nested root and prove no root creation; existing symlink, non-directory, conflict, cleanup, and storage-error tests remain the compatibility regression set.
- Decision (Q3): The direct check will start a fresh isolated server with `HOME` set to a temporary existing home, `MNEMOSYNE_MEMORY_ROOT` absent, and exact remember enablement true; call `memory_remember` once with benign synthetic project content through MCP; verify the minimal `remembered` result, one canonical file under `<temporary-home>/.mnemosyne/memory`, directory modes `0700`, and file mode `0600`; then stop the server, physically remove the containing temporary directory and log, and verify cleanup. It will not use the user's real home or an ad-hoc MCP script.

Plan (execution steps)
- [x] S1) Resolve Q1-Q3 and record the exact safe creation algorithm, focused tests, and isolated direct-check procedure.
- [x] S2) Move Track 008 to ACTIVE (folder, filename, title, and current path status) and check this step before implementation begins.
- [x] S3) Execute one TDD chunk: add focused failing store and enabled MCP-handler tests for an absent default parent chain; implement the smallest shared-store directory-initialization change; refactor and run focused validation.
- [x] S4) Update `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md`; run the full suite and `git diff --check`; perform and clean up one isolated direct MCP first-run check; record evidence.
- [x] S5) Confirm acceptance and milestones, move Track 008 to COMPLETED with synchronized status, and record final outcomes.

Current inventory
- `mnemosyne/settings.py:get_memory_root()` returns `Path.home() / ".mnemosyne" / "memory"` when no override is supplied and performs no filesystem mutation.
- `mnemosyne/memory/store.py:FilesystemMemoryStore._ensure_private_directories()` validates that a target record directory is beneath `memory_root`, collects missing ancestors back to the nearest existing parent, and creates that chain plus each root-to-record descendant individually in parent-to-child order with mode `0700`. Existing directories are not chmodded, and component conflicts retain bounded path/storage errors.
- `FilesystemMemoryStore.create()` serializes first, then under the mutation lock ensures directories, rejects unsafe components, writes a mode-`0600` temporary file, publishes without overwrite, syncs the directory, and reloads the canonical record.
- `MemoryService.remember()` checks mutation enablement and content policy before duplicate discovery and `store.create()`, preserving no-directory behavior for disabled and refused calls.
- `mnemosyne/mcp/tools/memory_remember/handler.py` resolves the memory root only for enabled valid calls and maps storage/path failures to bounded `memory_source_unavailable` Tool errors.
- `tests/memory/test_store_mutations.py:test_store_atomically_creates_private_directories_and_file` now starts from an existing mode-`0750` temporary home with an absent `.mnemosyne/memory` chain and proves the existing home is unchanged, every created directory is mode `0700`, the canonical file is mode `0600`, and no temporary file remains.
- `tests/mcp/test_memory_remember.py:test_memory_remember_initializes_an_absent_default_memory_root` unsets the root override, substitutes an isolated `Path.home()`, and proves an enabled call returns `remembered` with one default-location record. The disabled and refused tests now use absent nested roots and prove no parent creation.
- `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` now state that no manual first-run setup is required; canonical create lazily initializes missing private directories, existing directories remain unchanged, and startup/recall/disabled/invalid/refused operations do not initialize storage.
- The working tree was clean on `main` synchronized with `origin/main` before this planning-only Track was added.

Artifacts
- Prerequisite implementation record: `.backlog/COMPLETED/2026/TRACK_007_COMPLETED_consent_gated_memory_remember.md`.
- Governing filesystem and remember contracts: `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md`.
- S3 TDD evidence: the effective focused red run collected four tests and failed the two first-run cases with `MemorySourceUnavailable`/`storage_error`, while the disabled and refused no-write cases passed. After the minimal store change, all four passed in 0.20 seconds. The complete store-mutation and remember-handler files then passed 56 tests in 0.25 seconds, and `git diff --check` passed.
- S4 automated evidence: the full suite passed 290 tests in 0.79 seconds with `PYTHONPATH=.` under the available Python 3.11 pytest runner, and `git diff --check` passed after documentation updates.
- S4 direct MCP evidence: an isolated server on port 8767 ran with exact remember enablement, a temporary existing `HOME`, and no `MNEMOSYNE_MEMORY_ROOT`. One benign project-memory call returned `remembered` with active revision 1 and created exactly one canonical schema-version-2 file with `recorded_via: memory_remember`; `.mnemosyne`, the memory root, and every record-parent directory were mode `0700`, and the file was mode `0600`. The server stopped, port 8767 ceased answering, and the complete temporary home/root/log directory was physically removed and verified absent.
- S4 direct-check cleanup note: an initial command successfully reached the same isolated write but stopped during shell-side evidence extraction because zsh reserves the variable name `status`; its server shut down and its temporary directory was explicitly removed before the clean passing rerun. No synthetic memory or log remains from either attempt.

Completion notes
- DRAFT created on 2026-07-18 after read-only inspection identified the non-recursive memory-root creation gap. No implementation or implementation-driving test was added.
- S1 planning completed on 2026-07-18: Q1-Q3 now define the parent-to-child private creation algorithm, focused regression coverage, and isolated direct MCP procedure.
- S2 completed on 2026-07-18: Track 008 moved to ACTIVE with synchronized folder, filename, title, and current path. The next unchecked step is S3; no implementation or implementation-driving test was included in this transition.
- S3 completed on 2026-07-18 through focused TDD. The store now lazily creates a missing private parent chain only during canonical creation; store and enabled-handler regressions prove default-root first-run success, private modes, unchanged existing-home permissions, and disabled/refused no-write behavior. A1-A4 and M2 are checked; documentation, the full suite, and direct MCP validation remain in S4.
- S4 completed on 2026-07-18: public filesystem documentation, all 290 automated tests, whitespace validation, isolated default-root MCP creation, permission checks, server shutdown, and physical cleanup passed. A5-A6 and S4 are checked; S5 is the only remaining step.
- S5 completed on 2026-07-18: all acceptance criteria, milestones, questions, and execution steps are checked; Track 008 moved to COMPLETED with synchronized folder, filename, title, and current path. A clean installation now needs no manual memory-directory initialization: the first enabled, valid, policy-accepted canonical create builds only its missing private directory chain, preserves existing directories and all no-write boundaries, and retains atomic mode-`0600` record publication.

# TRACK 009 [DRAFT]: local settings file

Track
- ID: TRACK_009
- Repository: Mnemosyne
- Branch: main
- Current path: .backlog/DRAFT/2026/TRACK_009_DRAFT_local_settings_file.md

Problems (PORE)
- P1: As a local operator, I must prefix every normal server launch with `MNEMOSYNE_MEMORY_REMEMBER_ENABLED=true` to retain my chosen remember-Tool availability, because Mnemosyne has no persistent local operator-settings file.
- P2: As a user relying on explicit mutation boundaries, I need persistent configuration to remain fail-closed and distinct from consent, because a convenient local setting must not silently broaden Tool availability, accept ambiguous values, or replace per-call MCP-client approval.
- P3: As an operator troubleshooting startup, I need deterministic source precedence and bounded configuration errors, because environment and file settings can otherwise conflict or disclose untrusted configuration content.

Objective
- Add one fixed, local, read-only-at-startup TOML settings file that can persist the remember-only operator gate while preserving default-off behavior, strict environment overrides, startup-fixed Tool registration, and mandatory per-call client consent.

Non-negotiables
- This Track remains planning-only while DRAFT; no implementation or implementation-driving tests begin until all blocking questions are resolved and the Track is moved to ACTIVE with its Move-to-ACTIVE step checked.
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- The settings file is operator configuration, not memory, consent evidence, an audit log, or a secret store.
- The fixed proposed path is `~/.mnemosyne/config.toml`; no MCP request may select or read an arbitrary configuration path.
- Missing configuration must preserve the current default-off remember behavior and must not create `~/.mnemosyne`, the settings file, or the memory root.
- Configuration may enable only the existing `memory_remember` server gate; it does not approve any Tool call and does not weaken OpenCode's exact per-call `ask` requirement.
- The existing `MNEMOSYNE_MEMORY_REMEMBER_ENABLED` environment variable remains supported for explicit process-level control.
- Invalid, unreadable, or unsafe configuration fails startup closed with bounded errors that do not echo supplied values or file contents.
- Parsing uses Python's standard library unless planning identifies a requirement it cannot safely satisfy.
- No commit or push occurs unless explicitly requested.

Acceptance criteria
- [ ] A1) [P1] With no enablement environment variable and `~/.mnemosyne/config.toml` containing the accepted true setting, startup discovery and dispatch expose `memory_remember`, and `mnemosyne`/`mnemosyne-dev` require no prefixed enablement command.
- [ ] A2) [P2] With the file absent, the relevant key absent, or an accepted false setting, startup remains default-off and creates no settings/application/memory path.
- [ ] A3) [P2, P3] A supplied environment value has explicitly documented deterministic precedence over the file; exact true/false behavior remains compatible, and an invalid supplied environment value fails closed rather than falling back to the file.
- [ ] A4) [P2, P3] Malformed TOML, invalid types/values, disallowed structure, unsafe file shape, and unreadable-source behavior produce stable bounded startup failures without exposing configuration contents or enabling remember.
- [ ] A5) [P2] Enabling remember through the file changes only startup Tool discovery/dispatch; it does not create memory, establish consent, alter Tool schemas/results, or weaken client per-call approval rules.
- [ ] A6) [P1, P2, P3] Focused automated tests, the full suite, whitespace validation, and isolated startup/direct discovery checks pass without touching the user's real home or retaining temporary configuration/memory.
- [ ] A7) [P1, P2, P3] `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` document the exact path, schema, precedence, default/failure behavior, restart requirement, and separation from consent.

Why now / impact
- Track 007 made remember safely available behind an environment-only operator gate, and Track 008 removed manual first-write directory setup. A persistent local setting is now the smallest usability improvement that lets an operator run `mnemosyne` or `mnemosyne-dev` normally without weakening the two-part operator-enable plus per-call-consent model.

Scope
- In scope:
  - One fixed local settings file at `~/.mnemosyne/config.toml`.
  - A minimal TOML schema for the existing remember-only enablement gate.
  - Standard-library TOML parsing and strict validation in the settings layer.
  - Deterministic environment/file/default precedence.
  - Bounded fail-closed handling for malformed, invalid, unsafe, or unreadable configuration.
  - Startup registry integration through the existing `get_memory_remember_enabled()` seam.
  - Focused settings and startup-discovery/dispatch tests using isolated temporary homes.
  - User-facing setup, restart, precedence, consent-boundary, and troubleshooting documentation.
- Out of scope:
  - Automatically creating, editing, migrating, watching, or hot-reloading the settings file.
  - MCP Tools or HTTP endpoints for reading or changing operator configuration.
  - Moving memory records into the settings file or changing `MNEMOSYNE_MEMORY_ROOT` behavior.
  - Enabling future mutation Tools, bulk enablement, wildcard permissions, or client auto-approval.
  - Secrets, credentials, per-user profiles, remote configuration, encryption, or multi-user policy.
  - Changing `memory_remember` arguments, results, persistence, content policy, or logging.

Milestones
- [ ] M1) File schema, precedence, strictness, path-safety, error, and validation decisions are complete and the Track is eligible for ACTIVE.
- [ ] M2) Focused TDD proves settings resolution and startup registry behavior without changing consent or default-off semantics.
- [ ] M3) Documentation, full validation, isolated startup checks, cleanup, and completion transition are recorded.

Risks / decisions
- Risk: Treating any truthy TOML value as enabled would weaken the exact boolean contract.
- Risk: Silently ignoring malformed or unknown security-relevant configuration can leave the operator with a mistaken belief about Tool availability.
- Risk: Falling back to a file after an invalid environment override would violate the existing fail-closed process-level contract.
- Risk: Reading arbitrary or client-selected paths would broaden filesystem access beyond the local operator boundary.
- Risk: Automatically creating the file or parent at startup would add an unexpected write to an otherwise read-only/default-off launch.
- Risk: A settings file can be mistaken for consent even though client approval remains a separate runtime boundary.
- Decision: The proposed path is fixed at `Path.home() / ".mnemosyne" / "config.toml"` and is resolved only by the settings layer.
- Decision: The proposed minimal schema is `[memory] remember_enabled = <TOML boolean>`; strings such as `"true"` are not booleans.
- Decision: A supplied environment variable has highest precedence, the file is consulted only when the variable is absent, and the final default is false.
- Decision: File enablement is read once during startup registry construction, matching the existing restart-required availability model.
- Decision: No directory or file is created by settings resolution.

Open questions
- [ ] Q1) Is the accepted TOML document exactly one `[memory]` table with exactly one optional `remember_enabled` boolean, or may unrelated future top-level sections/keys be ignored safely?
- [ ] Q2) Does an absent `remember_enabled` key mean false, and are an empty document and an empty `[memory]` table accepted as disabled?
- [ ] Q3) What exact bounded exception type/message distinguishes malformed TOML, invalid schema/type, unreadable file, non-regular file, and unsafe symlink without exposing contents or unnecessary absolute paths?
- [ ] Q4) Are symlinked `config.toml` files rejected, and what regular-file size/encoding limits prevent special-file or unbounded reads while keeping local setup simple?
- [ ] Q5) Should POSIX file/directory modes be enforced, warned about, or documented only, given the file contains no secrets but controls mutation-Tool availability?
- [ ] Q6) What exact precedence matrix covers absent, valid, and invalid environment values against absent, valid, and invalid files while proving that a present environment value prevents file access?
- [ ] Q7) Which isolated startup checks prove `mnemosyne`/`mnemosyne-dev` discovery behavior, restart requirements, no-write startup, environment override, and complete cleanup without creating real user configuration?

Decision log
- Decision (prior Track 007): Remember is absent from discovery and dispatch by default; exact lowercase environment `true` enables it, exact lowercase `false` disables it, every other supplied environment value fails startup closed, and availability is fixed at startup.
- Decision (prior Track 007): Server-side enablement is not consent; OpenCode must display exact arguments and require `once` approval for every remember call, while `always` and auto-approval remain unsupported.
- Decision (prior Track 008): Settings resolution and server startup do not initialize `~/.mnemosyne` or the memory root; only canonical create lazily initializes storage.
- Decision (initial inspection): `mnemosyne/settings.py:get_memory_remember_enabled()` currently reads only the environment, and `mnemosyne/mcp/tools/registry.py` calls it once while constructing the module-level startup registry. The CLI imports the app through Uvicorn, so settings failure naturally occurs during process startup without requiring CLI-owned configuration logic.

Plan (execution steps)
- [ ] S1) Resolve Q1-Q7 and record the exact TOML schema, precedence matrix, path/file limits, bounded errors, consent separation, and isolated validation procedure.
- [ ] S2) Move Track 009 to ACTIVE (folder, filename, title, and current path status) and check this step before implementation begins.
- [ ] S3) Execute one TDD chunk for fixed-path TOML loading, bounded strict validation, environment/file/default precedence, and no-write behavior in `mnemosyne/settings.py`.
- [ ] S4) Execute one TDD chunk connecting file-derived enablement to startup discovery/dispatch and validating isolated CLI/startup behavior without changing the registry or Tool contract.
- [ ] S5) Update `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md`; run focused and full automated validation plus `git diff --check`; perform isolated startup/discovery checks and cleanup; record evidence.
- [ ] S6) Confirm acceptance and milestones, move Track 009 to COMPLETED with synchronized status, and record final outcomes.

Current inventory
- `mnemosyne/settings.py` owns server constants, dynamic memory-root resolution, and strict environment-only remember enablement. `get_memory_remember_enabled()` returns false for an absent value or exact `false`, true for exact `true`, and otherwise raises a non-echoing `ValueError`.
- `mnemosyne/mcp/tools/registry.py` calls `get_memory_remember_enabled()` once at module import to construct an immutable startup registry; that same selection drives `tools/list`, `list_tools`, and dispatch.
- `mnemosyne/cli.py` starts Uvicorn with `mnemosyne.app:app`; it should remain free of Tool-selection and TOML parsing semantics.
- Python requires version 3.11 or newer, so standard-library `tomllib` is available without adding a dependency.
- `tests/test_settings.py` covers accepted and invalid environment values but has no isolated-home file cases or precedence matrix.
- `tests/mcp/test_registry.py` independently tests enabled/disabled registry construction and real remember dispatch; startup import behavior currently depends on the environment-only settings seam.
- `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` currently describe `MNEMOSYNE_MEMORY_REMEMBER_ENABLED` as the only remember gate and require documentation changes if a file source is accepted.
- Track 008 is completed in the current uncommitted working tree. Its full suite passed 290 tests, `git diff --check` passed, and isolated direct MCP data was removed before this planning-only Track was added.

Artifacts
- Remember-gate prerequisite: `.backlog/COMPLETED/2026/TRACK_007_COMPLETED_consent_gated_memory_remember.md`.
- First-run filesystem prerequisite: `.backlog/COMPLETED/2026/TRACK_008_COMPLETED_first_run_memory_root_initialization.md`.
- Current public configuration and consent contracts: `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md`.

Completion notes
- DRAFT created on 2026-07-18 after read-only inspection of settings, CLI, and startup registry flow. No implementation or implementation-driving test was added.

# TRACK 009 [COMPLETED]: local settings file

Track
- ID: TRACK_009
- Repository: Mnemosyne
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_009_COMPLETED_local_settings_file.md

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
- [x] A1) [P1] With no enablement environment variable and `~/.mnemosyne/config.toml` containing the accepted true setting, startup discovery and dispatch expose `memory_remember`, and `mnemosyne`/`mnemosyne-dev` require no prefixed enablement command.
- [x] A2) [P2] With the file absent, the relevant key absent, or an accepted false setting, startup remains default-off and creates no settings/application/memory path.
- [x] A3) [P2, P3] A supplied environment value has explicitly documented deterministic precedence over the file; exact true/false behavior remains compatible, and an invalid supplied environment value fails closed rather than falling back to the file.
- [x] A4) [P2, P3] Malformed TOML, invalid types/values, disallowed structure, unsafe file shape, and unreadable-source behavior produce stable bounded startup failures without exposing configuration contents or enabling remember.
- [x] A5) [P2] Enabling remember through the file changes only startup Tool discovery/dispatch; it does not create memory, establish consent, alter Tool schemas/results, or weaken client per-call approval rules.
- [x] A6) [P1, P2, P3] Focused automated tests, the full suite, whitespace validation, and isolated startup/direct discovery checks pass without touching the user's real home or retaining temporary configuration/memory.
- [x] A7) [P1, P2, P3] `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` document the exact path, schema, precedence, default/failure behavior, restart requirement, and separation from consent.

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
- [x] M1) File schema, precedence, strictness, path-safety, error, and validation decisions are complete and the Track is eligible for ACTIVE.
- [x] M2) Focused TDD proves settings resolution and startup registry behavior without changing consent or default-off semantics.
- [x] M3) Documentation, full validation, isolated startup checks, cleanup, and completion transition are recorded.

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
- [x] Q1) Is the accepted TOML document exactly one `[memory]` table with exactly one optional `remember_enabled` boolean, or may unrelated future top-level sections/keys be ignored safely?
- [x] Q2) Does an absent `remember_enabled` key mean false, and are an empty document and an empty `[memory]` table accepted as disabled?
- [x] Q3) What exact bounded exception type/message distinguishes malformed TOML, invalid schema/type, unreadable file, non-regular file, and unsafe symlink without exposing contents or unnecessary absolute paths?
- [x] Q4) Are symlinked `config.toml` files rejected, and what regular-file size/encoding limits prevent special-file or unbounded reads while keeping local setup simple?
- [x] Q5) Should POSIX file/directory modes be enforced, warned about, or documented only, given the file contains no secrets but controls mutation-Tool availability?
- [x] Q6) What exact precedence matrix covers absent, valid, and invalid environment values against absent, valid, and invalid files while proving that a present environment value prevents file access?
- [x] Q7) Which isolated startup checks prove `mnemosyne`/`mnemosyne-dev` discovery behavior, restart requirements, no-write startup, environment override, and complete cleanup without creating real user configuration?

Decision log
- Decision (prior Track 007): Remember is absent from discovery and dispatch by default; exact lowercase environment `true` enables it, exact lowercase `false` disables it, every other supplied environment value fails startup closed, and availability is fixed at startup.
- Decision (prior Track 007): Server-side enablement is not consent; OpenCode must display exact arguments and require `once` approval for every remember call, while `always` and auto-approval remain unsupported.
- Decision (prior Track 008): Settings resolution and server startup do not initialize `~/.mnemosyne` or the memory root; only canonical create lazily initializes storage.
- Decision (initial inspection): `mnemosyne/settings.py:get_memory_remember_enabled()` currently reads only the environment, and `mnemosyne/mcp/tools/registry.py` calls it once while constructing the module-level startup registry. The CLI imports the app through Uvicorn, so settings failure naturally occurs during process startup without requiring CLI-owned configuration logic.
- Decision (Q1): The complete accepted TOML schema is an otherwise empty document with one optional top-level `memory` table. That table may contain only the optional `remember_enabled` key, and its value must be a TOML boolean. Unknown top-level keys or tables, unknown `memory` keys, a non-table `memory` value, and every non-boolean enablement value fail closed as invalid schema rather than being ignored for possible future use.
- Decision (Q2): A missing file, empty document, absent `memory` table, empty `[memory]` table, absent `remember_enabled` key, and explicit `remember_enabled = false` all resolve to disabled. Only the TOML boolean `remember_enabled = true` enables remember. Resolution never creates the application directory, settings file, memory root, or any other path.
- Decision (Q3): File-source failures use one bounded `SettingsError`, a `ValueError` subclass with a stable non-content-bearing code and fixed message. The exact code/message pairs are `invalid_toml` / `Mnemosyne settings file is not valid TOML`; `invalid_schema` / `Mnemosyne settings file has an invalid schema`; `unreadable` / `Mnemosyne settings file could not be read`; `not_regular` / `Mnemosyne settings source is not a regular file`; `unsafe_path` / `Mnemosyne settings file path is unsafe`; `too_large` / `Mnemosyne settings file exceeds 16384 bytes`; and `unsafe_permissions` / `Mnemosyne settings source permissions are unsafe`. Invalid environment values retain the existing `ValueError` and exact non-echoing `MNEMOSYNE_MEMORY_REMEMBER_ENABLED must be 'true' or 'false'` message. No error includes an absolute path, supplied value, file content, parser detail, or underlying exception text.
- Decision (Q4): The settings layer derives only `Path.home() / ".mnemosyne" / "config.toml"`. A symlinked `.mnemosyne` component or `config.toml`, a non-directory application component, and a non-regular settings source are rejected before parsing. The implementation will use a no-follow open where the platform provides it, verify the opened descriptor is still a regular file, and bound the complete source to 16 KiB before strict UTF-8 decoding and standard-library `tomllib` parsing. Invalid UTF-8 is reported as `invalid_toml`; source races and operating-system read failures remain bounded without fallback or content disclosure.
- Decision (Q5): On POSIX, an existing `.mnemosyne` directory or `config.toml` with group- or world-writable mode bits is rejected as `unsafe_permissions`, because another local account could otherwise alter mutation-Tool availability. Exact modes are not required: non-writable `0755`/`0644` sources remain accepted because the file is not a secret store, while documentation recommends `0700` for `.mnemosyne` and `0600` for `config.toml`. Non-POSIX platforms retain the structural, symlink, regular-file, size, and readability checks without pretending POSIX mode bits are portable.
- Decision (Q6): A supplied environment value is evaluated first. Exact `true` returns enabled and exact `false` returns disabled without resolving home, inspecting metadata, or opening the file, even when the file is missing, valid, or invalid. Any other supplied value fails with the existing bounded environment error and likewise performs no file access or fallback. Only an absent environment value consults the file: a missing/empty/key-absent/false source disables, true enables, and every malformed, invalid, unsafe, excessive, or unreadable source fails startup closed. If both sources are absent, the final default is false.
- Decision (Q7): Focused settings tests will substitute `Path.home()` with an isolated temporary home and cover the accepted schema states, rejected unknown/type/TOML/UTF-8 cases, 16-KiB boundary, symlink/non-regular/permission cases where supported, complete precedence matrix, no-access environment short circuit, and before/after no-write snapshots. Startup tests will use fresh subprocess imports with isolated `HOME`, an absent root override, and controlled enablement sources to prove the startup-fixed registry selection, invalid-source process failure, and unchanged CLI-to-Uvicorn app import seam. Final direct validation will start the existing app on an isolated local port with only a temporary-home file enabling remember, check both discovery surfaces and dispatch, modify the temporary file while the process runs to prove no hot reload, restart to observe the new value, exercise valid and invalid environment overrides, verify no settings or memory path was created by startup/discovery, then stop the server and remove the complete temporary home/log directory. This common app-import path is used by both `mnemosyne` and `mnemosyne-dev`, so neither command requires a prefixed enablement variable once the file is valid and true; no ad-hoc MCP script or real home is used.

Plan (execution steps)
- [x] S1) Resolve Q1-Q7 and record the exact TOML schema, precedence matrix, path/file limits, bounded errors, consent separation, and isolated validation procedure.
- [x] S2) Move Track 009 to ACTIVE (folder, filename, title, and current path status) and check this step before implementation begins.
- [x] S3) Execute one TDD chunk for fixed-path TOML loading, bounded strict validation, environment/file/default precedence, and no-write behavior in `mnemosyne/settings.py`.
- [x] S4) Execute one focused integration-validation chunk proving that the existing registry seam connects file-derived enablement to startup discovery/dispatch and that isolated CLI/startup behavior requires no registry or Tool-contract change.
- [x] S5) Update `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md`; run focused and full automated validation plus `git diff --check`; perform isolated startup/discovery checks and cleanup; record evidence.
- [x] S6) Confirm acceptance and milestones, move Track 009 to COMPLETED with synchronized status, and record final outcomes.

Current inventory
- `mnemosyne/settings.py` owns server constants, dynamic memory-root resolution, and environment-first remember enablement. Exact environment `true`/`false` returns before home resolution; an invalid supplied value retains the existing bounded `ValueError`; only an absent value consults the fixed local file.
- The settings layer now derives only `~/.mnemosyne/config.toml`, accepts the strict optional `[memory]`/optional boolean `remember_enabled` schema, defaults missing/empty/key-absent/false states to disabled, and uses standard-library `tomllib` after a bounded 16-KiB UTF-8 read.
- `SettingsError` exposes only the decided stable code/message pairs. Descriptor-based reading rejects symlinked/non-directory application paths, symlinked/non-regular files, unsafe POSIX write modes, excessive sources, file replacement between metadata check and open, and unreadable sources; no source content, supplied value, parser detail, underlying exception, or absolute path enters its messages.
- Settings resolution creates and modifies no path. It anchors the settings-file open to the validated application-directory descriptor when supported, applies no-follow flags where available, verifies opened identities and metadata, and closes descriptors on every result.
- `mnemosyne/mcp/tools/registry.py` calls `get_memory_remember_enabled()` once at module import to construct an immutable startup registry; that same selection drives `tools/list`, `list_tools`, and dispatch.
- `mnemosyne/cli.py` remains free of Tool-selection and TOML parsing semantics. Focused CLI tests now lock both `mnemosyne` and `mnemosyne-dev` to the shared `mnemosyne.app:app` import, with reload enabled only for the development entrypoint.
- Python requires version 3.11 or newer, so standard-library `tomllib` is available without adding a dependency.
- `tests/test_settings.py` now contains 36 isolated cases covering existing strict environment syntax, environment no-access precedence, every accepted disabled/enabled file state, strict schema and TOML/UTF-8 rejection, exact size boundary, application/file symlinks and shapes, POSIX write-mode rejection and accepted non-writable modes, bounded unreadable behavior, unchanged source content/mode, and absent-path no-write behavior.
- `tests/mcp/test_registry.py` independently tests enabled/disabled registry construction and real remember dispatch. `tests/mcp/test_startup_settings.py` adds eight fresh-process tests using isolated temporary homes: file-derived enabled/disabled discovery through both surfaces, known/unknown dispatch without persistence, environment precedence, bounded invalid-file/environment startup failure, startup-fixed selection, fresh-restart changes, no real-home access, and complete temporary-path containment.
- `README.md` now documents the fixed path and strict TOML example, all disabled states, environment/file/default precedence, no-fallback invalid override, startup/reconnect requirements, consent separation, 16-KiB UTF-8 and source-shape boundaries, accepted/recommended POSIX modes, bounded failures, and no-write startup behavior.
- `docs/ARCHITECTURE.md` now assigns the fixed schema, descriptor-based bounded read, source validation, stable errors, and environment-first selection to `mnemosyne/settings.py` while preserving startup registry, CLI, MCP, and route boundaries. `docs/GLOSSARY.md` defines remember enablement across both sources and the disabled default without conflating it with consent.
- Track 008 is committed and completed on `main`; its full suite passed 290 tests, `git diff --check` passed, and isolated direct MCP data was removed before this Track was added. S3 changes remain limited to the settings resolver, focused tests, and this Track record; the registry, CLI, Tool schema/results, consent policy, memory root, and persistence behavior are unchanged.

Artifacts
- Remember-gate prerequisite: `.backlog/COMPLETED/2026/TRACK_007_COMPLETED_consent_gated_memory_remember.md`.
- First-run filesystem prerequisite: `.backlog/COMPLETED/2026/TRACK_008_COMPLETED_first_run_memory_root_initialization.md`.
- Current public configuration and consent contracts: `README.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md`.
- S3 TDD evidence: the focused red run failed during collection because `SETTINGS_MAX_BYTES` and the new settings-file contract did not exist. After the minimal implementation and test refactor, all 36 focused settings tests passed in 0.28 seconds. The full suite ran with exact environment `false` to prevent global registry import from consulting the operator's real home and passed 315 tests in 0.71 seconds; `git diff --check` passed.
- S4 integration evidence: all eight fresh-process startup tests and three CLI tests passed on their first focused run in 2.74 seconds, proving that S3's resolver was already connected through the existing startup registry seam; no production registry, CLI, MCP, route, Tool schema/result, consent, or persistence change was warranted. The full isolated suite passed 325 tests in 3.15 seconds with exact environment `false`, and `git diff --check` passed.
- S5 automated evidence: after public documentation updates, 47 focused settings/startup/CLI tests passed in 2.76 seconds; the full isolated suite passed 325 tests in 3.23 seconds with exact environment `false`; and `git diff --check` passed.
- S5 direct MCP evidence: an isolated Uvicorn server on port 8768 ran with a temporary `HOME`, no root override, no enablement environment value, and a mode-`0600` temporary `~/.mnemosyne/config.toml` containing boolean true. MCP `tools/list` and the `list_tools` Tool exposed `memory_remember`; an empty remember dispatch reached the known Tool and returned bounded `invalid_origin` without creating memory. Changing the file to false while the process ran left discovery enabled; after restart, discovery omitted remember and direct dispatch returned unknown Tool. Exact environment true overrode the false file and exposed remember. An invalid environment import failed closed with only the fixed allowed-value message and did not echo the invalid value.
- S5 cleanup evidence: the enabled, restarted-disabled, and override-enabled servers all stopped; port 8768 had no listener; the temporary application directory contained only the operator-created settings file and no memory directory before cleanup; and the complete temporary home, settings, logs, and containing directory were physically removed and verified absent. The first override-enabled launch command placed BSD `env -u` after an assignment and exited immediately with `env: -u: No such file or directory`; it started no server and created no memory, and the corrected option order passed before cleanup.

Completion notes
- DRAFT created on 2026-07-18 after read-only inspection of settings, CLI, and startup registry flow. No implementation or implementation-driving test was added.
- S1 planning completed on 2026-07-18: Q1-Q7 now define the strict minimal schema, disabled states, environment/file/default precedence, fixed safe source and 16-KiB UTF-8 limit, bounded error contract, POSIX write-permission boundary, startup-fixed consent separation, and isolated validation procedure. M1 and S1 are checked; the Track remains DRAFT and no implementation or implementation-driving test has begun.
- S2 completed on 2026-07-18: Track 009 moved to ACTIVE with synchronized folder, filename, title, and current path. The next unchecked step is S3; no implementation or implementation-driving test was included in this transition.
- S3 completed on 2026-07-18 through focused TDD. Environment precedence remains exact and fail-closed; an absent override now reads only the fixed, bounded, structurally safe local TOML source; all missing/disabled states remain no-write and default-off; and failures expose only stable bounded settings errors. Focused and full automated validation plus whitespace validation passed. The next unchecked step is S4 for fresh-process startup registry and CLI/app integration behavior.
- S4 completed on 2026-07-18 as focused integration validation. Fresh isolated processes prove that the file drives both discovery surfaces and dispatch together, environment overrides short-circuit file access, failures remain bounded, the selected registry does not change until restart, and startup/discovery create no settings or memory path. The existing registry and shared CLI app-import seams required no production change. A1-A5, M2, and S4 are checked; S5 documentation, consolidated validation, and isolated direct MCP checks remain next.
- S5 completed on 2026-07-18: public documentation now covers the complete local-settings and consent contract; focused and full automated suites plus whitespace validation passed; isolated direct MCP checks proved file enablement, both discovery surfaces, known non-writing dispatch, startup-fixed behavior, restart, valid override, invalid-override failure, and no memory creation; and all temporary processes/data were removed. A6, A7, and S5 are checked. S6 completion review and transition are the only remaining work.
- S6 completed on 2026-07-18: all acceptance criteria, milestones, questions, and execution steps are checked; Track 009 moved to COMPLETED with synchronized folder, filename, title, and current path. Mnemosyne now supports one strict fixed local settings file for persistent remember-only operator enablement while preserving environment precedence, startup-fixed discovery/dispatch, default-off and fail-closed behavior, no-write startup, bounded source handling, unchanged MCP contracts, and mandatory per-call client consent.

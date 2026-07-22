# TRACK 023 [COMPLETED]: MyMCP project identity

Track
- ID: TRACK_023
- Repository: Mnemosyne (transitioning host identity to MyMCP)
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_023_COMPLETED_mymcp_project_identity.md

Problems (PORE)
- P1: As a maintainer separating a generic MCP host from the Mnemosyne memory domain, I experience ambiguous package ownership, because the top-level project and Python package are named `mnemosyne` even though they will become the MyMCP host substrate.
- P2: As an existing Mnemosyne user, I risk configuration or data breakage during that separation, because package identity and persistent memory-domain identity currently use the same word in different roles.

Objective
- Establish `mymcp` as the repository's top-level host project and Python package identity while preserving Mnemosyne's public memory-domain identity, configuration, and existing local storage compatibility.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Preserve local-first, single-user, least-privilege, and explicit-tool boundaries.
- Preserve all current MCP tool names, schemas, results, errors, HTTP endpoints, and safety behavior.
- Preserve existing Mnemosyne memory data without migration or rewriting.
- Keep HTTP transport thin and MCP semantics under the host's `mcp/` package.

Acceptance criteria
- [x] A1) [P1] Project metadata identifies the distribution as `mymcp`.
- [x] A2) [P1] The importable top-level package is `mymcp`, and repository source and tests use `mymcp.` module paths.
- [x] A3) [P1] Console scripts are `mymcp`, `mymcp-dev`, and `mymcp-test`, and resolve through `mymcp.cli`.
- [x] A4) [P2] Mnemosyne remains the memory-domain/server identity: `SERVER_NAME`, `MNEMOSYNE_*` settings, memory namespace test data, and memory-specific HMAC domains are unchanged.
- [x] A5) [P2] The default application and memory paths remain `~/.mnemosyne` and `~/.mnemosyne/memory`, with focused automated compatibility coverage.
- [x] A6) [P1, P2] Package-boundary documentation describes the MyMCP host identity and the retained Mnemosyne memory domain without claiming that plugin extraction is already implemented.
- [x] A7) [P1, P2] Focused and full automated validation pass after the rename.

Why now / impact
- This is the first concrete, compatibility-preserving step toward separating reusable MCP-host mechanisms from Mnemosyne's memory policy without a replacement project or wholesale rewrite.

Scope
- In scope:
  - Change `[project].name` from `mnemosyne` to `mymcp`.
  - Change the three console scripts to `mymcp`, `mymcp-dev`, and `mymcp-test`, targeting `mymcp.cli`.
  - Rename the top-level Python package directory from `mnemosyne/` to `mymcp/`.
  - Replace Python module-path imports beginning with `mnemosyne.` across source and tests with `mymcp.`.
  - Replace the bare `from mnemosyne import cli` test import with `from mymcp import cli`.
  - Update package-boundary and operator documentation affected by the identity change.
  - Add focused tests for the new host identity and retained storage compatibility.
- Out of scope:
  - Extracting Mnemosyne into an independently packaged plugin.
  - Implementing plugin discovery, installation, isolation, manifests, namespacing, or aggregation.
  - Extracting the generic tool registry, settings composition, approval service, or generic storage service.
  - Renaming `SERVER_NAME = "mnemosyne"` or any public `memory_*` Tool.
  - Renaming `MNEMOSYNE_*` environment variables.
  - Renaming `~/.mnemosyne`, `.mnemosyne`, existing memory paths, memory namespace data, or memory-specific HMAC domain strings.
  - Migrating or rewriting stored records.
  - Changing the Git repository or remote.

Milestones
- [x] M1) Host package and distribution identity are MyMCP.
- [x] M2) Mnemosyne storage and domain compatibility are explicitly protected.
- [x] M3) Documentation and full validation describe and verify the transitional architecture.

Risks / decisions
- Risk: A broad textual rename could alter persistent identifiers, configuration names, Tool identities, or live storage paths.
- Mitigation: Rename only Python module paths and declared host package/script identity; protect retained Mnemosyne identifiers with focused tests and review exact diffs.
- Risk: Renaming the package can leave stale imports or entrypoint targets that focused tests do not exercise.
- Mitigation: search source and tests for remaining `mnemosyne.` module paths and run the full test suite.
- Decision: Evolve the current repository incrementally rather than creating a replacement implementation.
- Decision: The repository/package becomes the MyMCP host first; `mnemosyne` remains the memory domain and future plugin identity.
- Decision: This Track changes identity and package boundaries only; it does not claim or implement plugin separation.

Open questions
- [x] Q1) Should current memory-domain identifiers be renamed with the package? No.
- [x] Q2) Should plugin extraction be combined with this Track? No.

Decision log
- Decision (Q1): Preserve server name, environment variables, storage directories, HMAC domains, Tool names, and memory namespace data as Mnemosyne compatibility contracts.
- Decision (Q2): Limit TRACK_023 to the host identity rename and its compatibility/documentation tests; later separation requires its own Track.

Plan (execution steps)
- [x] S1) Move TRACK_023 to ACTIVE (folder, filename, title, and current path) and check this step before implementation.
- [x] S2) Execute the project-identity TDD chunk: add a focused failing test for the `mymcp` distribution/import/console-script contract; make it pass with the smallest package, metadata, entrypoint, and module-path rename; refactor remaining module paths; update affected package-boundary documentation; run focused validation and module-path searches; then update this Track with inventory and evidence.
- [x] S3) Execute the storage-compatibility TDD chunk: add or strengthen a focused test proving the default remains `~/.mnemosyne/memory` after the package rename; make the smallest correction if needed; run focused validation and retained-identifier searches; then update this Track with evidence.
- [x] S4) Run the complete automated test suite and whitespace validation, review the final diff against all acceptance criteria, and record evidence.
- [x] S5) Move TRACK_023 to COMPLETED (folder, filename, title, and current path), check this transition, and record completion outcomes.

Current inventory
- `pyproject.toml` declares distribution `mymcp` and scripts `mymcp`, `mymcp-dev`, and `mymcp-test`, all targeting `mymcp.cli`.
- `mymcp/` is the importable top-level Python host package and contains app assembly, CLI, settings, routes, MCP protocol/tool code, and the in-process Mnemosyne memory domain.
- `tests/test_project_identity.py` protects the distribution/import/console-script contract; `tests/test_cli.py` imports `mymcp.cli` and protects Uvicorn target `mymcp.app:app`.
- `tests/test_settings.py` directly protects the read-only default root resolution as `<home>/.mnemosyne/memory`, proves that resolution creates no path, and rejects an accidental `.mymcp` default; the existing remember integration test protects lazy creation under the same retained root.
- Source and tests use `mymcp.` Python module paths; focused searches found no stale `mnemosyne.` imports or host module references under `mymcp/` or `tests/`.
- `mymcp/settings.py` still owns retained server identity, `MNEMOSYNE_*` configuration, and the default `.mnemosyne` application/memory paths.
- `mymcp/memory/` remains a tool-independent, semantically Mnemosyne-specific memory-domain boundary; plugin extraction is not implemented.
- `README.md`, `docs/ARCHITECTURE.md`, `docs/GLOSSARY.md`, root/scoped `AGENTS.md`, and test operator guidance describe the MyMCP host package and retained Mnemosyne domain.
- Baseline: the repository was clean on `main` before Track creation.

Artifacts
- Project-memory plan: `First refactor step: rename project identity mnemosyne → mymcp`.
- Related project-memory idea: `Idea: incremental host separation within Mnemosyne`.

Completion notes
- Track activated; implementation may proceed one declared TDD chunk at a time.
- S2 TDD evidence (2026-07-22): `python -m pytest -q tests/test_project_identity.py` first failed during collection with `ModuleNotFoundError: No module named 'mymcp'`; after the package, metadata, entrypoint, module-path, and documentation rename, the focused identity test passed (`1 passed`).
- S2 validation: identity, CLI, OpenCode compatibility, list-tools version, and import-boundary tests passed (`24 passed`); complete test collection succeeded (`748 tests collected`); focused source/test searches found no stale `mnemosyne.` Python host module paths; retained `SERVER_NAME`, `MNEMOSYNE_*`, `.mnemosyne`, and memory-list HMAC domains remain present; `git diff --check` passed.
- S3 compatibility evidence (2026-07-22): the new direct default-root test and existing remember default-root integration test passed (`2 passed`) without a production correction. Searches confirmed `SERVER_NAME = "mnemosyne"`, all four `MNEMOSYNE_*` mutation gates plus `MNEMOSYNE_MEMORY_ROOT`, `SETTINGS_DIRECTORY_NAME = ".mnemosyne"`, all memory-list HMAC domains, and 45 representative `namespace_id="mnemosyne"` test-data uses remain; no `.mymcp` application path or legacy distribution/console-script declaration was introduced. `git diff --check` passed.
- S4 validation and acceptance review (2026-07-22): the complete automated suite passed (`749 passed in 7.49s`); `git diff --check` and explicit trailing-whitespace checks for untracked renamed/new files passed. Final searches found no stale `mnemosyne.` Python host imports or module references under `mymcp/` or `tests/`, no current operator documentation using the retired console commands, and no legacy distribution/script declarations. Review confirmed the `mymcp` distribution/package/entrypoints and documentation while preserving Mnemosyne server, Tool, configuration, storage, namespace-data, and HMAC identities; all acceptance criteria pass.
- Completed (2026-07-22): MyMCP is now the repository distribution and top-level Python host package, while Mnemosyne remains the in-process memory domain and compatible public server, Tool, configuration, and storage identity. No plugin extraction, data migration, repository change, commit, or push was performed.

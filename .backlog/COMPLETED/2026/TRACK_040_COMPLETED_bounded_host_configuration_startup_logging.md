# TRACK 040 [COMPLETED]: Bounded host-configuration startup logging

Track
- ID: TRACK_040
- Repository: MyMCP
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_040_COMPLETED_bounded_host_configuration_startup_logging.md

Problems (PORE)
- P1: As the MyMCP operator, I cannot confirm from startup output whether host configuration was absent and defaulted or safely loaded, because successful host-configuration resolution is currently silent.
- P2: As the MyMCP operator using development reload, I cannot distinguish the expected per-process configuration loads from accidental duplicate loading, because supervisor and worker startup behavior has no bounded observable event.
- P3: As the MyMCP maintainer, I need configuration diagnostics to preserve the existing bounded-error and least-disclosure contract, because logging paths, environment values, plugin IDs, source content, or underlying exceptions would weaken the configuration boundary.

Objective
- Emit deterministic, bounded, content-free startup logs that make host-configuration loading and failure outcomes observable without changing configuration schema, startup semantics, public MCP behavior, or trust boundaries.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Do not log the selected path, `XDG_CONFIG_HOME` value, document content, plugin IDs, unapproved field values, credentials, secrets, parser/OS exception details, or tracebacks from the host logger. The validated loopback address/port and bounded counts are explicitly approved.
- Preserve strict configuration loading, bounded errors, immutable per-process snapshots, no import-time reads, no runtime watching, and restart-only changes.
- Preserve normal-process and development supervisor/worker read counts established by TRACK_039.
- Logging configuration is not added to host configuration schema 1; no `[logging]` table, log-level field, environment override, or CLI flag is introduced.
- Preserve all Mnemosyne logging, configuration, storage, Tool, consent, and compatibility identities.
- Keep routes thin and place startup logging under a host-owned boundary.
- Do not add external plugin loading, discovery, installation, lifecycle management, gateway audit, safety, or isolation claims.

Acceptance criteria
- [x] A1) [P1] A successful present source emits exactly one bounded host-configuration terminal event in each process that consumes it.
- [x] A2) [P1] An absent source emits exactly one bounded defaults terminal event without creating any path.
- [x] A3) [P1] Success/default events report only approved operational metadata sufficient to confirm schema, loopback binding, and declaration counts.
- [x] A4) [P2] Normal startup, direct-factory startup, development supervisor startup, and development worker construction retain the approved per-process read model and have deterministic non-duplicated logging coverage.
- [x] A5) [P2] Documentation explains why development mode may show one configuration event per consuming process and does not imply hot reload or runtime watching.
- [x] A6) [P3] Every `load_host_configuration()` failure emits exactly one bounded error event containing only the approved outcome and stable error code before the original bounded exception propagates unchanged; later semantic/composition failures retain their existing ownership.
- [x] A7) [P3] Focused tests prove logs omit paths, environment values, source text, plugin IDs, field values, and underlying exception details for success, absence, and failure outcomes.
- [x] A8) [P3] Ordinary imports emit no startup event and perform no configuration read; runtime requests emit no configuration event.
- [x] A9) [P3] Existing MCP request/response logs, Mnemosyne terminal logs, Uvicorn operation, endpoint routes, Tool surface, and public behavior remain unchanged.
- [x] A10) [P1] Operator and architecture documentation describe logger ownership, event vocabulary, bounded fields, levels, process behavior, and troubleshooting use.
- [x] A11) [P3] The complete version-impact decision is recorded before activation and every applicable identity, definition, parity, and capability-ledger guard passes.

Why now / impact
- TRACK_039 delivered a strict host-configuration boundary, and the first operator restart succeeded silently. One bounded terminal event per consuming process would make the new boundary operable without requiring path disclosure, verbose tracing, or configuration schema expansion.

Scope
- In scope:
  - Host-owned logger name and ownership boundary for configuration startup.
  - One terminal success/default event per configuration-consuming process.
  - One bounded terminal error event per failed load attempt, if approved during DRAFT review.
  - Fixed event levels, outcome vocabulary, and allowlisted fields.
  - Normal launcher, development supervisor/worker, and direct-factory observability.
  - Import-time logging neutrality and existing request/runtime stability.
  - Review of the current route-owned `logging.basicConfig` side effect and explicit decision whether logging setup belongs in launcher startup.
  - Focused automated tests, operator guidance, architecture documentation, and version-impact governance.
- Out of scope:
  - Host-configuration schema fields for logging or log levels.
  - Log files, rotation, retention, formatting frameworks, structured-log dependencies, telemetry, metrics, tracing, or remote export.
  - Logging configuration through CLI flags or environment variables.
  - Plugin IDs, configuration paths, source text, submitted values, secrets, or exception details in logs.
  - Changes to MCP request/response, Mnemosyne Tool/domain, or future gateway security-audit semantics.
  - External plugin startup composition or any Phase 3 implementation.

Milestones
- [x] M1) Resolve event ownership, fields, levels, process-role semantics, failure behavior, root-logging setup, and complete version impact.
- [x] M2) Implement and validate bounded configuration terminal events through coherent TDD chunks.
- [x] M3) Update documentation, run complete validation, and reconcile the living roadmap if materially affected.

Risks / decisions
- Risk: Logging from both the loader and launcher could duplicate one logical event in a process.
- Risk: Development reload legitimately has a supervisor and replaceable workers; ambiguous events could look like accidental rereads.
- Risk: Logging before a handler/level is configured could make normal and development behavior inconsistent.
- Risk: Success metadata can become identifying if paths or plugin IDs are included.
- Risk: Failure logging can leak underlying parser or operating-system details even when the raised error remains bounded.
- Decision: This Track will add no user-configurable logging setting and will not change host configuration schema 1.
- Version impact: Approved. Fixed bounded startup logs are operational behavior, not a public MCP contract or configuration-document change. Keep MyMCP distribution/package and endpoint marker `0.3.0`, MCP protocol `2024-11-05`, host plugin API 1, manifest schema 1, the absence of a worker protocol, host configuration schema 1, every plugin-owned configuration schema, Mnemosyne plugin 0.3.0, memory_recall capability 1.2.0, the other seven capability versions 1.1.0, plugin-data schemas, opaque runtime-generation semantics, policy identity, public bindings, and memory record schemas unchanged because this Track changes no endpoint, Tool definition/result/error, plugin-author contract, persisted document, runtime composition, authorization, or domain behavior. Existing definition/parity/version guards must pass without a capability-ledger entry.

Open questions
- [x] Q1) Which module owns the logger and terminal-event projection: host configuration, bootstrap, a new host logging module, or a narrow combination without duplicate events?
- [x] Q2) What exact logger name, event names, levels, and stable field order should be used?
- [x] Q3) Which success metadata is both useful and bounded: source state, schema version, loopback address/port, declaration count, enabled count, process role, runtime generation, Tool count, or plugin count?
- [x] Q4) Should loopback address and port be logged directly, or should binding remain solely in Uvicorn's own output?
- [x] Q5) How should development supervisor and worker events be distinguished without adding mutable process state or claiming Uvicorn lifecycle ownership?
- [x] Q6) Should the host emit a bounded error event before propagating `HostConfigurationError`, and which code/outcome fields are allowed?
- [x] Q7) Should the import-time `logging.basicConfig(level=logging.INFO)` call in `mymcp/routes/mcp.py` move to explicit launcher startup, and how should direct factory users retain useful defaults without import-time side effects?
- [x] Q8) How will tests prove exactly one terminal event per consuming process while avoiding an end-to-end Uvicorn reload subprocess test unless needed?
- [x] Q9) Which documentation files require updates, and does the glossary need a dedicated host startup-log term?
- [x] Q10) What is the complete version impact across every identity/version dimension?

Decision log
- Decision (scope): Add fixed bounded startup observability only; do not add configurable logging or change host configuration schema 1.
- Decision (Q1): `mymcp.host.configuration` owns one terminal event for each public `load_host_configuration()` attempt. Bootstrap, application assembly, and routes emit no duplicate configuration event.
- Decision (Q2): Use logger `mymcp.host.configuration`. INFO success/default messages use stable field order `host_configuration outcome=<loaded|absent_defaults> schema_version=<n> address=<literal> port=<n> declarations=<n> enabled=<n>`. ERROR uses `host_configuration outcome=error code=<stable_code>`.
- Decision (Q3/Q4): Allow only source outcome, schema version, validated literal loopback address, validated port, declaration count, and enabled count. Do not log process role, PID, runtime generation, Tool count, plugin count, plugin IDs, path, or source values.
- Decision (Q5): Do not invent process-role state. Normal startup emits once; development emits once in the supervisor and once in each worker because each is a distinct consuming process. Existing process-aware runner formatting may distinguish them; documentation explains this behavior without claiming lifecycle ownership.
- Decision (Q6): The loader catches `HostConfigurationError`, emits one ERROR event containing only its stable code, and re-raises the same exception unchanged. Semantic and later composition failures remain outside this loader event.
- Decision (Q7): Move `logging.basicConfig(level=logging.INFO)` from route import time to explicit `mymcp` and `mymcp-dev` launcher startup before loading. Uvicorn owns logging setup for direct factory use; programmatic factory callers use standard Python logging configuration. No import configures logging or emits an event.
- Decision (Q8): Use focused caplog tests at the loader and mocked launcher/factory boundaries; prove exact event counts and read counts without launching an OS-level reload supervisor.
- Decision (Q9): Update `README.md`, `docs/CONFIGURATION.md`, and `docs/ARCHITECTURE.md`. No new glossary term is needed for this narrow operational event.
- Decision (Q10): Apply the complete approved unchanged-version decision recorded above.

Plan (execution steps)
- [x] S1) Complete DRAFT review: resolve Q1-Q10, refine acceptance traceability, record the complete version-impact decision, and identify coherent TDD chunks.
- [x] S2) Move Track 040 to ACTIVE (folder, filename, and title status) and check this explicit Move-to-ACTIVE step before implementation or implementation-driving tests.
- [x] S3) Execute the approved focused TDD chunk for one host-owned success/default terminal event per configuration-consuming process; update this Track immediately with evidence.
- [x] S4) Execute the approved focused TDD chunk for normal/direct-factory and development supervisor/worker observability without duplicate reads or events; update this Track immediately with evidence.
- [x] S5) Execute the approved focused TDD chunk for bounded failure events and logging-bootstrap ownership if approved by DRAFT decisions; update this Track immediately with evidence.
- [x] S6) Update approved operator/architecture documentation, run focused and full validation plus `git diff --check`, reconcile the roadmap if required, and complete the Track only if every acceptance criterion passes.

Current inventory
- TRACK_039 delivered MyMCP 0.3.0 host configuration schema 1 in pushed commit `7e1e82c`.
- `mymcp/host/configuration.py` owns path resolution, strict loading/parsing, immutable snapshots, semantic validation, bounded exceptions, logger `mymcp.host.configuration`, and one ordered INFO event for each successful present/default load.
- `mymcp/cli.py` loads once in normal and development-supervisor startup; `mymcp/app.py` loads once for a direct factory/reload worker when no snapshot is injected.
- `mymcp/host/bootstrap.py` validates the injected snapshot before manifest/parity/runtime construction and emits no startup log.
- `mymcp/cli.py` now configures standard INFO logging explicitly before normal/development loading. `mymcp/routes/mcp.py` retains bounded MCP request/response logging under logger `mcp` but no longer configures global logging at import time.
- Mnemosyne handlers and memory storage already use bounded logger-specific conventions that must remain unchanged.
- `tests/test_cli.py`, `tests/test_app.py`, `tests/host/test_configuration_loading.py`, `tests/host/test_bootstrap.py`, `tests/routes/test_mcp.py`, and `tests/memory/test_import_boundaries.py` contain the primary startup, logging, and boundary coverage.
- TRACK_040 is COMPLETED; every acceptance criterion, milestone, and plan step passed.

Artifacts
- User observation: after creating `~/.config/mymcp/config.toml` and restarting successfully, startup produced no explicit confirmation that configuration was loaded.
- Delivered foundation: `.backlog/COMPLETED/2026/TRACK_039_COMPLETED_mymcp_host_configuration_foundation.md` and `docs/CONFIGURATION.md`.
- Living roadmap: `project/mymcp/roadmaps`; Phase 3 startup composition remains NEXT and this operational logging Track is not currently roadmap-derived.
- Governance: `docs/AI_WORKFLOW.md`, `.backlog/README.md`, `.backlog/PORE.md`, root/scoped `AGENTS.md`.

Completion notes
- DRAFT created from the operator's request for successful host-configuration startup visibility.
- DRAFT review resolved Q1-Q10, approved the unchanged version impact, and moved TRACK_040 to ACTIVE before implementation or implementation-driving tests.
- S3 TDD evidence: two focused tests first failed because present and absent loads emitted no event. The minimal loader-owned implementation made both pass with exact ordered allowlisted fields and no path creation. Full configuration-loading validation passed `39` tests with `3` native-Windows-only skips.
- S4 evidence: focused normal launcher, development supervisor, and direct-factory tests each observed exactly one configuration event; subsequent runtime requests emitted none. All `3` focused process-boundary tests passed without changing the TRACK_039 read model or adding process-role state.
- S5 TDD evidence: `16` focused checks first failed for all twelve loader error codes, launcher logging order, and route import-time logging ownership. The minimal wrapper now emits one code-only ERROR and re-raises the same exception; both launchers configure INFO before loading; route imports no longer call `basicConfig`. All `16` focused checks pass, including omission of path, environment, source, plugin, and exception markers.
- S6 final evidence: README, the canonical configuration guide, and architecture documentation now define logger ownership, exact event vocabulary/levels/fields, per-consuming-process behavior, omissions, standard logging ownership, and troubleshooting. Focused implementation/boundary validation passed `120` tests with `3` native-Windows-only skips; independent final acceptance validation passed `432` focused tests with the same `3` skips; the full suite passed `1288` tests with `3` skips; `git diff --check` passed. Independent review marked A1-A11 PASS after narrowing architecture wording to avoid a Uvicorn worker-lifecycle claim.
- Roadmap reconciliation: TRACK_040 is a bounded operational follow-up, not roadmap-derived, and does not change the delivered baseline, phase sequencing, dependencies, intended outcomes, or NEXT direction. The living roadmap remains current with Phase 3 startup composition NEXT; no roadmap memory mutation was required.
- Final outcome: each public host-configuration load attempt now emits exactly one bounded `mymcp.host.configuration` terminal event for loaded, absent-default, or loader-error outcomes. Launchers configure INFO logging explicitly, route imports no longer configure global logging, and all startup/read/public compatibility boundaries remain unchanged.

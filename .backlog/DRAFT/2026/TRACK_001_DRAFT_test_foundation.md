# TRACK 001 [DRAFT]: test foundation

Track
- ID: TRACK_001
- Repository: Mnemosyne
- Branch: <current branch>
- Current path: .backlog/DRAFT/2026/TRACK_001_DRAFT_test_foundation.md

Problems (PORE)
- P1: As a Mnemosyne maintainer, I cannot safely evolve MCP behavior, because the repository has no automated test foundation or repeatable protocol-contract coverage.
- P2: As a Mnemosyne maintainer, I need to retire the placeholder `hello` tool, because it is not an intended durable part of Mnemosyne's public MCP surface.

Objective
- Establish a focused pytest foundation that makes current and future MCP behavior safe to change through test-first development.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Tests must preserve the local-first, least-privilege, and small explicit-tool model.
- Direct MCP protocol checks supplement automated tests; they do not replace them.

Acceptance criteria
- [ ] A1) [P1] `pytest` discovers and executes a repository test suite with a documented command.
- [ ] A2) [P1] Unit coverage verifies MCP message parsing, JSON-RPC helpers, method dispatch, and tool registry behavior.
- [ ] A3) [P1] Route coverage verifies health, version, and MCP HTTP transport through FastAPI `TestClient`.
- [ ] A4) [P1] Contract coverage verifies initialize, tools/list, tools/call, malformed requests, and unknown methods or tools.
- [ ] A5) [P1] Test layout and conventions are documented in `tests/README.md`.
- [ ] A6) [P2] The `hello` tool is removed from the registry and package layout; tools/list no longer exposes it and calls to `hello` return the documented unknown-tool response.

Why now / impact
- TDD is now a project non-negotiable; the absence of a test suite blocks compliant implementation and leaves the MCP contract exposed to regressions.

Scope
- In scope:
  - Pytest configuration and test-only dependencies.
  - A root `tests/` package mirroring route and MCP domains.
  - Minimal shared fixtures and current public-contract coverage.
  - Test conventions and execution documentation.
  - TDD-driven retirement of the placeholder `hello` tool, including its public-contract coverage.
- Out of scope:
  - New MCP tools or behavior changes beyond testability fixes discovered during the work.
  - CI, coverage thresholds, mutation testing, or end-to-end tests against a networked server.

Milestones
- [ ] M1) Define the test runner, layout, and conventions.
- [ ] M2) Cover MCP units and HTTP surface, including retirement of `hello`.
- [ ] M3) Run the suite and capture validation evidence.

Risks / decisions
- Risk: FastAPI `TestClient` requires a compatible `httpx` test dependency.
- Risk: Removing `hello` is a breaking public-tool change for any existing caller.
- Decision: Use pytest with `--import-mode=importlib`, mirroring Prometheus's backend test configuration.
- Decision: Keep shared fixtures in `tests/conftest.py` only when broadly reused; otherwise keep fixtures local to the domain suite.

Open questions
- [x] Q1) Which test dependency grouping best fits the project packaging policy: a `test` optional dependency extra or a dedicated development requirements file?
- [x] Q2) What JSON-RPC response contract should apply to invalid top-level request payloads and malformed parameters, including error code, message, and request ID behavior?
- [x] Q3) Are the package-based `mnemosyne/mcp/tools/hello/` and `list_tools/` modules the intended baseline that this Track must cover?
- [x] Q4) Should `hello` be removed immediately in this Track, or first be deprecated for a defined compatibility period?

Decision log
- Decision (Q1): Use a `test` optional dependency extra in `pyproject.toml`, containing `pytest` and `httpx`; install it with `pip install -e ".[test]"`.
- Decision (Q2): Invalid request envelopes return JSON-RPC `-32600` with `id: null`; non-object `params` return `-32602` while preserving a valid request ID.
- Decision (Q3): The package-based `hello/` and `list_tools/` modules are the current source layout. `list_tools` remains part of the intended baseline; `hello` is covered only as needed to verify and complete its retirement.
- Decision (Q4): Remove `hello` immediately. Mnemosyne is an early skeleton with no compatibility period required for this placeholder tool.

Plan (execution steps)
- [x] S1) Resolve Q1 and define the test execution contract: `pip install -e ".[test]"`, then `python -m pytest tests`.
- [x] S2) Resolve Q4, then freeze the initial request/error, module-layout, and `hello` retirement test matrix: parsing and JSON-RPC response helpers; dispatch and registry; `list_tools` package handler; health/version/MCP routes; initialize, tools/list, tools/call, unknown method/tool, invalid envelope, invalid params, and post-removal `hello` contracts.
- [ ] S3) Move Track 001 to ACTIVE (folder, filename, and title status).
- [ ] S4) Add the approved test dependency extra and pytest configuration; validate test discovery.
- [ ] S5) Build out unit and route coverage in focused TDD chunks.
- [ ] S6) Retire `hello` in a focused TDD chunk and update public-contract documentation.
- [ ] S7) Run the full suite, document test conventions, and record validation evidence.
- [ ] S8) Move Track 001 to COMPLETED and capture completion notes.

Current inventory
- `pyproject.toml`: runtime dependencies only; no pytest configuration or test dependencies.
- `mnemosyne/routes/`: HTTP routes for MCP, health, and version.
- `mnemosyne/mcp/`: message parsing, JSON-RPC helpers, method dispatch, tool registry, and the `hello` and `list_tools` handlers.
- No `tests/` directory or automated tests currently exists.
- The package-based `mnemosyne/mcp/tools/hello/` and `list_tools/` modules replace the former single-file modules; `hello` is explicitly in scope for retirement.

Artifacts
- Prometheus reference: `/Users/kosta/Sources/Sennheiser/prometheus/backend/tests/README.md`.
- Prometheus reference: `/Users/kosta/Sources/Sennheiser/prometheus/pytest.ini`.

Completion notes
- Pending.

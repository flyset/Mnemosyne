# TRACK 001 [COMPLETED]: test foundation

Track
- ID: TRACK_001
- Repository: Mnemosyne
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_001_COMPLETED_test_foundation.md

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
- [x] A1) [P1] `pytest` discovers and executes a repository test suite with a documented command.
- [x] A2) [P1] Unit coverage verifies MCP message parsing, JSON-RPC helpers, method dispatch, and tool registry behavior.
- [x] A3) [P1] Route coverage verifies health, version, and MCP HTTP transport through FastAPI `TestClient`.
- [x] A4) [P1] Contract coverage verifies initialize, tools/list, tools/call, malformed requests, and unknown methods or tools.
- [x] A5) [P1] Test layout and conventions are documented in `tests/README.md`.
- [x] A6) [P2] The `hello` tool is removed from the registry and package layout; tools/list no longer exposes it and calls to `hello` return the documented unknown-tool response.

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
- [x] M1) Define the test runner, layout, and conventions.
- [x] M2) Cover MCP units and HTTP surface, including retirement of `hello`.
- [x] M3) Run the suite and capture validation evidence.

Risks / decisions
- Risk: FastAPI `TestClient` requires a compatible `httpx2` test dependency.
- Risk: Removing `hello` is a breaking public-tool change for any existing caller.
- Decision: Use pytest with `--import-mode=importlib`, mirroring Prometheus's backend test configuration.
- Decision: Keep shared fixtures in `tests/conftest.py` only when broadly reused; otherwise keep fixtures local to the domain suite.

Open questions
- [x] Q1) Which test dependency grouping best fits the project packaging policy: a `test` optional dependency extra or a dedicated development requirements file?
- [x] Q2) What JSON-RPC response contract should apply to invalid top-level request payloads and malformed parameters, including error code, message, and request ID behavior?
- [x] Q3) Are the package-based `mnemosyne/mcp/tools/hello/` and `list_tools/` modules the intended baseline that this Track must cover?
- [x] Q4) Should `hello` be removed immediately in this Track, or first be deprecated for a defined compatibility period?

Decision log
- Decision (Q1): Use a `test` optional dependency extra in `pyproject.toml`, containing `pytest` and `httpx2`; install it with `pip install -e ".[test]"`.
- Decision (Q2): Invalid request envelopes return JSON-RPC `-32600` with `id: null`; non-object `params` return `-32602` while preserving a valid request ID.
- Decision (Q3): The package-based `hello/` and `list_tools/` modules are the current source layout. `list_tools` remains part of the intended baseline; `hello` is covered only as needed to verify and complete its retirement.
- Decision (Q4): Remove `hello` immediately. Mnemosyne is an early skeleton with no compatibility period required for this placeholder tool.

Plan (execution steps)
- [x] S1) Resolve Q1 and define the test execution contract: `pip install -e ".[test]"`, then `python -m pytest tests`.
- [x] S2) Resolve Q4, then freeze the initial request/error, module-layout, and `hello` retirement test matrix: parsing and JSON-RPC response helpers; dispatch and registry; `list_tools` package handler; health/version/MCP routes; initialize, tools/list, tools/call, unknown method/tool, invalid envelope, invalid params, and post-removal `hello` contracts.
- [x] S3) Move Track 001 to ACTIVE (folder, filename, and title status).
- [x] S4) Add the approved test dependency extra and pytest configuration; validate test discovery.
- [x] S5) Build out unit and route coverage in focused TDD chunks.
- [x] S6) Retire `hello` in a focused TDD chunk and update public-contract documentation.
- [x] S7) Run the full suite, document test conventions, and record validation evidence.
- [x] S8) Move Track 001 to COMPLETED and capture completion notes.

Current inventory
- `pyproject.toml`: `test` extra provides `pytest` and `httpx2`; pytest uses importlib mode, discovers `tests/`, and provides `mnemosyne-test`.
- `mnemosyne/routes/`: HTTP routes for MCP, health, and version.
- `mnemosyne/mcp/messages.py`: preserves whether request parameters were object-valued.
- `mnemosyne/mcp/methods.py`: rejects invalid request envelopes with JSON-RPC `-32600` and non-object parameters with `-32602`, preserving valid request IDs.
- `mnemosyne/mcp/`: JSON-RPC helpers, method dispatch, tool registry, and the `list_tools` handler; the placeholder `hello` package has been retired.
- `tests/test_test_foundation.py`: focused runner-discovery test verifies the application imports under pytest.
- `tests/mcp/test_messages.py`: characterizes valid message parsing and default parameter normalization.
- `tests/mcp/test_protocol.py`: characterizes JSON-RPC result and error response shapes.
- `tests/mcp/test_methods.py`: validates invalid-envelope and non-object parameter rejection through method dispatch.
- `tests/mcp/test_registry.py`: validates unknown-tool registry behavior.
- `tests/mcp/test_list_tools.py`: validates the `list_tools` package handler.
- `tests/routes/test_operational.py`: validates health and version endpoints with FastAPI `TestClient`.
- `tests/routes/test_mcp.py`: validates initialize, tools/list/call, unknown-method, invalid-request, and post-retirement `hello` MCP HTTP contracts with FastAPI `TestClient`.
- `tests/test_cli.py`: validates that `mnemosyne-test` delegates to a subprocess pytest invocation.
- `tests/README.md`: documents installation, test execution, layout, and TDD conventions.
- The package-based `list_tools/` module replaces the former single-file module; `hello` was retired from its former package layout.

Artifacts
- Prometheus reference: `/Users/kosta/Sources/Sennheiser/prometheus/backend/tests/README.md`.
- Prometheus reference: `/Users/kosta/Sources/Sennheiser/prometheus/pytest.ini`.
- Validation (2026-07-17): before configuration, `.venv/bin/python -m pytest -p no:cacheprovider tests/test_test_foundation.py` failed with `No module named pytest`; after `pip install -e ".[test]"`, the focused test passed (1 passed). `.venv/bin/python -m pytest -p no:cacheprovider --collect-only` collected 1 test.
- Validation (2026-07-17): `tests/mcp/test_methods.py::test_handle_message_rejects_non_object_params_with_request_id` first failed because `ping` silently accepted list-valued parameters, then passed after parameter validation was added (1 passed).
- Validation (2026-07-17): `tests/mcp/test_methods.py::test_handle_message_rejects_non_object_request_envelopes` first failed with `AttributeError` for a list envelope, then passed after envelope validation was added (1 passed).
- Validation (2026-07-17): message parsing and JSON-RPC helper characterization suite passed (4 passed): `.venv/bin/python -m pytest -p no:cacheprovider tests/mcp/test_messages.py tests/mcp/test_protocol.py`.
- Validation (2026-07-17): FastAPI route coverage passed (6 passed): `.venv/bin/python -m pytest -p no:cacheprovider tests/routes`. The run emitted Starlette's installed `httpx` deprecation warning; no test failure occurred.
- Validation (2026-07-17): registry, `list_tools` handler, and `tools/list` baseline coverage passed (3 passed): `.venv/bin/python -m pytest -p no:cacheprovider tests/mcp/test_registry.py tests/mcp/test_list_tools.py tests/routes/test_mcp.py::test_mcp_tools_list_exposes_the_current_tool_baseline`.
- Validation (2026-07-17): retirement tests first failed because `hello` remained registered and callable, then passed after registry and package removal (2 passed): `.venv/bin/python -m pytest -p no:cacheprovider tests/routes/test_mcp.py::test_mcp_tools_list_excludes_the_retired_hello_tool tests/routes/test_mcp.py::test_mcp_tools_call_reports_hello_as_an_unknown_tool`.
- Validation (2026-07-17): `mnemosyne-test` passed the full suite (18 passed, no warnings) after the test dependency changed from `httpx` to `httpx2`.
- Validation (2026-07-17): direct live MCP `list_tools` check succeeded and exposed only `list_tools`.

Completion notes
- Established a pytest foundation with a documented `mnemosyne-test` command and focused TDD coverage for MCP units and FastAPI routes.
- Retired the placeholder `hello` tool from package layout, registry, documentation, and the live tool surface.
- All acceptance criteria passed; final validation was `mnemosyne-test` with 18 passing tests and no warnings.

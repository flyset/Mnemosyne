# TRACK 002 [COMPLETED]: MCP notification semantics and operator logging

Track
- ID: TRACK_002
- Repository: Mnemosyne
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_002_COMPLETED_mcp_notification_semantics_and_operator_logging.md

Problems (PORE)
- P1: As an MCP client operator, I receive a warning and JSON-RPC method-not-found error for a valid `notifications/cancelled` notification, because the server dispatches notifications as ordinary requests.
- P2: As an operator, I need default terminal logs to describe request outcomes without exposing payloads, because raw MCP arguments and results may contain sensitive user context.

Objective
- Handle supported MCP notifications without JSON-RPC responses and retain compact, payload-safe terminal logs.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Preserve the local-first, single-user, least-privilege model.
- Do not log arbitrary request parameters or result bodies at the default log level.
- Preserve stable JSON-RPC behavior for requests.

Acceptance criteria
- [x] A1) [P1] `notifications/cancelled` receives a no-content notification response rather than JSON-RPC error `-32601`.
- [x] A2) [P1] `notifications/initialized` also receives no JSON-RPC response.
- [x] A3) [P1] Notification handling has focused automated coverage for response status and empty body.
- [x] A4) [P2] Default request logs remain compact and exclude request arguments and response bodies.
- [x] A5) [P1, P2] README, architecture, and glossary document any externally observable notification behavior.

Why now / impact
- OpenCode sends cancellation notifications after completed tool calls. The current response is harmless but produces a misleading warning and is not notification-correct.

Scope
- In scope:
  - Recognize notification envelopes and return the appropriate no-content transport response.
  - Treat cancellation as a no-op until long-running work exists.
  - Keep notification output out of default terminal logs.
  - Test and document the behavior.
- Out of scope:
  - Interrupting or resource-cleaning active tool work.
  - General asynchronous job management.
  - Logging request or response payloads at any default level.

Milestones
- [x] M1) Notification behavior is protocol-correct and covered by automated tests.

Risks / decisions
- Risk: changing the current response shape may expose assumptions in clients.
- Decision: retain existing request behavior; change only notification handling, which must not produce JSON-RPC responses.

Open questions
- [ ] Q1) Should cancellation reasons be retained at DEBUG once a redaction policy exists?

Decision log
- Decision: implement cancellation as a no-op because current tool handlers complete synchronously.

Plan (execution steps)
- [x] S1) Move Track 002 to ACTIVE (folder, filename, and title status).
- [x] S2) Write focused failing tests for cancellation and initialized notification transport behavior.
- [x] S3) Implement the smallest notification-dispatch and transport change.
- [x] S4) Update public contract documentation and run automated plus direct MCP validation.
- [x] S5) Record validation evidence and move the Track to COMPLETED when all acceptance criteria pass.

Current inventory
- `mnemosyne/routes/mcp.py` logs compact request and response summaries and owns HTTP transport.
- `mnemosyne/mcp/methods.py` dispatches known MCP methods, including `notifications/initialized`.
- `mnemosyne/mcp/protocol.py` builds JSON-RPC success and error responses.
- `tests/routes/test_mcp.py` covers endpoint behavior and payload-safe log summaries.
- `mnemosyne/mcp/messages.py` identifies notifications by the absence of an `id`.
- `mnemosyne/mcp/methods.py` returns no response for notifications.
- Commit `c5c7f37` replaced raw MCP payload dumps with compact request-completion logging.

Artifacts
- MCP cancellation specification: https://modelcontextprotocol.io/specification/2025-03-26/basic/utilities/cancellation
- Focused TDD evidence: `.venv/bin/python -m pytest tests/routes/test_mcp.py` — red: 2 failed / 8 passed; green: 10 passed.
- Final automated validation: `.venv/bin/python -m pytest tests/routes/test_mcp.py` — 11 passed; `.venv/bin/python -m pytest` — 23 passed.
- Direct MCP validation: `POST /mcp` with `notifications/cancelled` returned `HTTP/1.1 202 Accepted` and `content-length: 0`.

Completion notes
- Notifications are identified by the absence of `id` and receive no JSON-RPC response body.
- `notifications/cancelled` and `notifications/initialized` are quiet no-ops until asynchronous tool work exists.
- Default MCP logs remain payload-safe; cancellation notifications log only at DEBUG.

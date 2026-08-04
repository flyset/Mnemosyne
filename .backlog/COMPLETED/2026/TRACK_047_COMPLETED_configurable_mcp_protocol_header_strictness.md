# TRACK 047 [COMPLETED]: configurable MCP protocol-header strictness

Track
- ID: TRACK_047
- Repository: MyMCP
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_047_COMPLETED_configurable_mcp_protocol_header_strictness.md

Problems (PORE)
- P1: As a MyMCP operator using Claude Desktop through `mcp-remote 0.1.37`, I cannot use an otherwise valid authenticated registered session because the bridge returns the bearer and `MCP-Session-Id` but omits `MCP-Protocol-Version` on post-initialize requests, which MyMCP rejects with HTTP 400.
- P2: As a MyMCP operator, I need to choose strict protocol-header enforcement or a bounded standards-compatible session-derived fallback, because clients differ in whether they repeat negotiated protocol context despite presenting a valid host-issued session.

Objective
- Add schema-6 immutable startup configuration that explicitly selects strict post-initialize MCP protocol-header enforcement or validated-session protocol fallback without weakening Authentication, session ownership, or supplied-header validation.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Reauthenticate every `/mcp` request before session lookup; sessions never replace Authentication evidence.
- Preserve opaque process-local sessions, principal/runtime binding, expiry, termination, and the existing session-header grammar.
- In compatibility mode, only an absent protocol-version header on an already validated registered session may use that session's immutable negotiated version. Duplicate, empty, non-ASCII, malformed, unsupported, or conflicting supplied headers remain body-free HTTP 400.
- Missing, malformed, unknown, expired, terminated, principal-mismatched, or stale-generation session IDs retain their existing body-free outcomes; no clientInfo, user agent, token shape, connection, or request body is used as a fallback identity or version source.
- Anonymous behavior is explicitly decided and tested; this Track must not silently relax it.
- Preserve local-first, single-user, least-privilege operation and all Mnemosyne identities, Tool contracts, consent, storage, and record semantics.

Acceptance criteria
- [x] A1) [P1] A captured Claude-compatible registered sequence—valid bearer and returned session ID but no post-initialize `MCP-Protocol-Version`—succeeds only when the explicit compatibility setting is selected.
- [x] A2) [P2] Strict mode preserves current missing-header HTTP 400 behavior for registered POST, GET, and DELETE session traffic.
- [x] A3) [P2] Compatibility mode validates bearer, exact opaque session ID, complete normalized principal, runtime generation, expiry, and the stored negotiated protocol version before dispatch, streaming, or termination.
- [x] A4) [P2] Compatibility mode rejects every supplied invalid, duplicate, malformed, unsupported, or session-conflicting protocol-version header with body-free HTTP 400.
- [x] A5) [P2] Schema 6 adds one bounded, immutable, non-secret strictness setting; schemas 1–5 and absent-file defaults retain their existing behavior exactly.
- [x] A6) [P1] Tests cover configuration parsing, application/session outcomes, thin HTTP route behavior, operator-bearer and OAuth parity, and redaction/no-dispatch boundaries.
- [x] A7) [P2] The complete public-contract version-impact decision, documentation, configuration guidance, and automated guards are updated before completion.

Why now / impact
- Track 046's valid session boundary exposed a real interoperability regression: Claude Desktop's common `mcp-remote 0.1.37` bridge preserves bearer authentication and MyMCP's session ID but not the negotiated protocol header. The current MCP specification permits a server to identify the negotiated version by another reliable mechanism, such as a validated session. An explicit operator choice preserves strict deployments while restoring client-neutral local usability.

Scope
- In scope:
  - Host configuration schema 6 and one exact immutable strictness setting.
  - Host application/session validation changes required for the selected mode.
  - Thin route plumbing only as needed to pass startup-fixed behavior to the host application.
  - Focused regression coverage reproducing the observed bearer/session/header sequence.
  - Documentation and version-impact work required by the approved public contract.
- Out of scope:
  - Changes to Authentication contract v1, bearer/OAuth validation, credential formats, OAuth metadata/challenges, or adapter selection.
  - Removing MCP sessions, making sessions stateless, session persistence, session configuration beyond this one strictness decision, client allowlists, or trust in clientInfo/user agents.
  - Governance policy, tool authorization, approvals, audit, plugin behavior, Mnemosyne behavior, remote deployment, or multi-user tenancy.

Milestones
- [x] M1) Finalize exact schema-6 shape, default, anonymous behavior, session-derived fallback rules, and complete version impact.
- [x] M2) Implement and validate configuration/bootstrap propagation through focused TDD.
- [x] M3) Implement and validate application/session and route compatibility behavior through focused TDD.
- [x] M4) Complete documentation, full validation, direct protocol checks, independent review, and roadmap reconciliation.

Risks / decisions
- Risk: Making a missing header broadly acceptable could admit ambiguous or unsupported protocol traffic.
- Risk: A client-specific allowlist based on `clientInfo` or user agent would be forgeable and non-client-neutral.
- Risk: Altering session validation order could weaken reauthentication-first or disclose session state.
- Decision: The setting is behavior-based, not client-identified. Schema 6 requires `[mcp] strict_protocol_version = <native boolean>`; `true` preserves exact Track 046 behavior, while `false` permits only an absent header to resolve from an already validated registered session's immutable negotiated version.
- Decision: Schemas 1–5 and absent-file defaults remain strict; compatibility requires schema 6 and explicit `strict_protocol_version = false`. Anonymous traffic remains stateless and always requires the post-initialize protocol header. Initialize remains header-free.
- Version impact: Advance MyMCP distribution/package/server marker from `0.8.0` to `0.9.0` because this adds host configuration schema 6 and conditional public `/mcp` transport behavior. Keep MCP protocol revision `2025-11-25`, HTTP route paths/methods, supplied-header grammar and supplied-header rejection unchanged. Authentication contract v1, adapters, verifier-source format, OAuth metadata/challenge, host-plugin API, manifest schema, external-plugin contract, worker protocol, plugin/capability/data contracts, bindings, runtime-generation semantics, policy/approval/audit status, session identity/lifetime/termination, and Mnemosyne configuration/storage/record schemas remain unchanged: the host-only setting preserves reauthentication-first and resolves only the immutable validated session version.

Open questions
- [x] Q1) What exact TOML table/key and boolean default represent the strictness choice without ambiguity?
- [x] Q2) Does compatibility mode apply only to registered sessions, and what exact behavior remains for anonymous post-initialize traffic?
- [x] Q3) How does session validation safely resolve a stored protocol version when the header is absent while retaining all existing failure classes?
- [x] Q4) Does schema 6 and changed conditional HTTP behavior require a package/server version advance, while the MCP revision remains `2025-11-25`?
- [x] Q5) What focused/direct protocol evidence and documentation are required to establish Claude compatibility without relying on client identity?

Decision log
- Decision (evidence): Captured local traffic shows `mcp-remote 0.1.37` sends valid bearer Authentication and the exact returned `MCP-Session-Id` on post-initialize requests, but omits `MCP-Protocol-Version`; a fallback test client sends all three headers and succeeds. The observed failure is HTTP 400 after Authentication/session transport processing, not Authentication or session-ID failure.
- Decision (specification direction): The current MCP Streamable HTTP transport requires clients to send the negotiated protocol header, rejects invalid/unsupported supplied versions, and permits a server with another reliable version source—such as negotiated session context—to identify the version when the header is absent.
- Decision (implementation gate): No implementation or implementation-driving test is authorized until all required public-contract/version-impact decisions are resolved, this Track is ACTIVE, and its Move-to-ACTIVE step is checked.
- Decision (Q1): Schema 6 requires the exact `[mcp]` table with native Boolean `strict_protocol_version`; no default exists within schema 6. `true` is strict and `false` selects compatibility. Schemas 1–5 and absent-file default remain strict by construction.
- Decision (Q2): Compatibility applies only to registered post-initialize session traffic. Anonymous requests remain stateless and require `MCP-Protocol-Version: 2025-11-25` after initialize; session-derived fallback never applies to anonymous traffic.
- Decision (Q3): Authentication remains first, followed by bounded singleton header extraction and host session validation. In compatibility mode, only `None` resolves from the already validated session's immutable negotiated version. Supplied values must remain exactly supported and session-matching. No request body, client information, user agent, connection metadata, or token shape supplies protocol context.
- Decision (Q4): Schema 6 and the conditional transport behavior advance MyMCP/package/server to `0.9.0`; MCP revision remains `2025-11-25`.
- Decision (Q5): Automated evidence will cover the captured bearer/session/omitted-header sequence, strict and compatibility POST/GET/DELETE paths, supplied-header rejection, Authentication-first/no-dispatch boundaries, and operator-bearer/OAuth parity. Direct redacted checks reproduce the wire sequence without client identification.

Plan (execution steps)
- [x] S1) Complete DRAFT review: resolve Q1-Q5, finalize schema-6/configuration default, conditional protocol/session semantics, anonymous behavior, complete version impact, acceptance criteria, and exact TDD chunks.
- [x] S2) Move TRACK_047 to ACTIVE (folder, filename, title, and Current path status) only after explicit user approval and before implementation or implementation-driving tests.
- [x] S3) TDD chunk 1 — add focused failing configuration/bootstrap tests for schema 6, exact setting grammar/default, schemas 1–5 preservation, and immutable propagation; implement the smallest passing configuration/composition changes; refactor, validate, and update this Track.
- [x] S4) TDD chunk 2 — add focused failing host-application/session tests for strict and compatibility paths, supplied-header rejection, and no-dispatch behavior; implement the smallest passing host-owned validation change; refactor, validate, and update this Track.
- [x] S5) TDD chunk 3 — add focused route/integration tests for POST, GET, DELETE, operator bearer, OAuth, and the captured Claude-compatible sequence; implement only required thin wiring; refactor, validate, and update this Track.
- [x] S6) TDD chunk 4 — perform approved version/documentation/configuration work; run focused/full/package/import/version checks and direct redacted protocol checks; update this Track.
- [x] S7) Obtain independent acceptance review; inspect and reconcile the Phase 4 roadmap under separate user approval if needed; record evidence and transition this Track to COMPLETED only after every criterion passes.

Current inventory
- `mymcp/host/configuration.py` now supports immutable schemas 1–6. Schema 6 requires exact `[mcp].strict_protocol_version` native Boolean; schemas 1–5 and absent defaults remain strict.
- `mymcp/app.py` propagates the immutable setting into the host application; `mymcp/host/mcp_application.py` accepts the startup-fixed value but retains strict behavior pending S4.
- `mymcp/host/sessions.py` stores immutable negotiated protocol version with the validated principal/runtime session context.
- `mymcp/routes/mcp.py` extracts bounded singleton session/protocol headers after Authentication and delegates to the host application.
- `tests/host/test_mcp_application.py` and route session suites cover strict Track 046 behavior; configuration and app/bootstrap suites cover schemas 1–5.

Artifacts
- Current session contract: `.backlog/COMPLETED/2026/TRACK_046_COMPLETED_mcp_principal_session_integration.md`.
- MCP Streamable HTTP transport specification, protocol-version header section.
- Applicable roadmap: `project/mymcp/roadmaps`, index `mem_5f3b5f4871d0406995f222d48e0357b7`, Phase 4 `mem_ec6d4b50c830463383ad0d1e221910c7`.

Completion notes
- DRAFT created with user approval. No implementation, implementation-driving test, protocol behavior, configuration mutation, version change, commit, push, tag, release, or memory mutation occurred.
- 2026-08-04: User approved activation and execution. M1/Q1–Q5 and complete version-impact decision are resolved; S1/S2 are complete. Next unchecked step: S3, configuration/bootstrap propagation TDD chunk.
- 2026-08-04: S3 complete. Focused failing tests established schema-6 exact parsing, immutability, old-schema rejection, strict absent defaults, and production application propagation. Minimal implementation added immutable `HostMCPConfiguration`, schema-6 parser/invariants, and startup-fixed application propagation; host session behavior remains unchanged. Validation: `pytest tests/host/test_configuration_schema.py tests/host/test_configuration_loading.py tests/host/test_configuration_semantics.py tests/test_app.py` — 193 passed, 3 skipped; `git diff --check` passed. Next unchecked step: S4.
- 2026-08-04: S4 complete. Focused failing host-application tests established that compatibility mode admits only an authenticated registered request with a valid opaque session and absent protocol header, while supplied unsupported values, missing sessions, and anonymous missing-header traffic remain body-free 400. The same validated-session fallback applies to stream validation and authenticated termination; an already terminated session remains 404. Minimal host-only changes permit `None` only under explicit compatibility mode and compare any supplied version exactly against the immutable session context; activity refresh follows successful full validation. Validation: `pytest tests/host/test_mcp_application.py tests/host/test_sessions.py tests/host/test_configuration_schema.py tests/test_app.py` — 144 passed; `git diff --check` passed. Next unchecked step: S5.
- 2026-08-04: S5 complete. Route coverage reproduces the captured registered bearer/session sequence with no post-initialize protocol header for POST and DELETE; shared host coverage establishes the equivalent GET stream validation. Compatibility mode rejects a supplied unsupported header before body parsing or dispatch. Integration coverage confirms the same compatibility result for real operator-bearer and OAuth principals, without client identification. Routes required no behavior change: existing bounded singleton extraction preserves absent header as `None`, reauthenticates first, and delegates session semantics to the host application. Validation: `pytest tests/routes/test_mcp_sessions.py tests/routes/test_operator_bearer_route.py tests/routes/test_oauth_protected_resource.py tests/host/test_mcp_application.py tests/host/test_sessions.py` — 64 passed; `git diff --check` passed. Next unchecked step: S6.
- 2026-08-04: S6 complete. Advanced package/server marker to `0.9.0`; MCP protocol remains `2025-11-25`. Updated configuration, session/authentication, architecture, glossary, README, vision, release notes, version/package, and discovery guards. Focused version/package checks passed (5 passed). Full validation: `pytest` — 2036 passed, 3 skipped. `python -m compileall -q mymcp` and `git diff --check` passed. The focused operator-bearer and OAuth route tests are direct redacted protocol evidence for registered initialize followed by omitted-header traffic. Next unchecked step: S7 independent acceptance review and roadmap reconciliation.
- 2026-08-04: S7 complete. Independent acceptance review marked A1–A7 passed and found no security regression; it confirmed Authentication-first validation, registered-session-only fallback, and no client-identity fallback. Added explicit strict registered DELETE missing-header coverage; `pytest tests/routes/test_mcp_sessions.py tests/host/test_mcp_application.py` passed (16 passed). Under explicit user approval, inspected the complete roadmap collection and revised the delivered-baseline and Phase 4 records for TRACK_047/MyMCP 0.9.0; Phase 4 remains in progress and Track 5 policy-filtered discovery/dispatch remains next. TRACK_047 is COMPLETED. `opencode.json` is unrelated pre-existing work and excluded from this Track.
- 2026-08-04: Post-completion operator validation exposed a schema-6 regression: the parser did not retain schema-5 operator-bearer table parsing. Added a focused schema-6 operator-bearer regression test and extended the existing parser condition to schemas 4–6. The operator configuration now loads with schema 6 and `strict_protocol_version = false`. Validation: direct configuration-load assertion passed; `pytest tests/host/test_configuration_schema.py tests/host/test_configuration_loading.py tests/host/test_configuration_semantics.py` — 177 passed, 3 skipped; `git diff --check` passed.

# TRACK 049 [COMPLETED]: configurable MCP session lifetimes

Track
- ID: TRACK_049
- Repository: MyMCP
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_049_COMPLETED_configurable_mcp_session_lifetimes.md

Problems (PORE)
- P1: As a MyMCP operator using a client with incomplete Streamable HTTP session-expiry recovery, I experience a permanently stale client connection after MyMCP expires an idle session, because the current fixed inactivity limit cannot be adjusted for this interoperability boundary.
- P2: As a MyMCP operator, I cannot choose an appropriate registered-session lifetime for a local deployment, because both inactivity and absolute lifetime are hard-coded in the host session store rather than represented in startup configuration.

Objective
- Add an immutable, startup-only host configuration that lets the operator retain the current safe defaults, choose bounded inactivity and absolute session lifetimes, or explicitly disable either expiry limit while preserving host-owned session security and process-local lifecycle semantics.

Non-negotiables
- This Track began as DRAFT and was moved to ACTIVE before implementation; its Move-to-ACTIVE step is checked.
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Configuration is validated once at startup, immutable for the process, and requires restart to change; there is no runtime reload or client-controlled lifetime.
- Preserve Authentication-first validation on every request, opaque session identifiers, complete-principal and runtime-generation binding, body-free session failures, explicit DELETE termination, and the maximum of 128 active sessions.
- Sessions remain process-local, non-persistent, unavailable to MCP dispatch and plugins, and are discarded on server restart.
- Disabling expiry is an explicit operator choice; it does not make a session a credential, replace Authentication, grant Tool authority, satisfy consent, or alter Governance boundaries.
- Do not change Mnemosyne Tools, schemas, storage, records, mutation gates, or plugin behavior.
- Never store or expose credentials, tokens, session identifiers, subjects, request contents, or other sensitive data in Track evidence or logs.

Acceptance criteria
- [x] A1) [P1] A schema-7 startup document can explicitly configure registered-session inactivity and absolute lifetime behavior, including a valid disabled value, and invalid, missing, duplicate, out-of-range, or wrong-typed values fail closed with bounded configuration errors.
- [x] A2) [P2] Schemas 1–6 and absent-file defaults retain the existing strict protocol behavior and the existing 30-minute inactivity / 8-hour absolute session lifetime without configuration drift.
- [x] A3) [P1] A configured inactivity lifetime expires a registered session after the configured interval, refreshes only after valid authenticated session-bound activity, and returns the existing body-free HTTP 404 for subsequent use.
- [x] A4) [P2] A configured absolute lifetime expires a registered session at the configured limit and is never extended by activity; boundary behavior is deterministic under the existing monotonic-clock test seam.
- [x] A5) [P1] Setting either lifetime to zero disables only that limit; setting both to zero keeps sessions until explicit DELETE or process restart while retaining capacity, authentication, binding, and termination safeguards.
- [x] A6) [P2] The configured lifetime values are propagated through production bootstrap and application construction into the host-owned session store without exposing session context below the host application boundary.
- [x] A7) [P1] Operator-bearer and OAuth registered principals receive identical configured session-lifetime behavior, while their existing Authentication failure and OAuth challenge behavior remains unchanged.
- [x] A8) [P2] The current MCP protocol revision `2025-11-25`, endpoint paths, session-header grammar, initialization/termination semantics, HTTP 400/404/503 classes, anonymous stateless behavior, and protocol-header compatibility setting remain unchanged.
- [x] A9) [P2] The 128-session capacity bound remains enforced and no expired-session cleanup timer, background task, persistence, renewal API, session listing, hot reconfiguration, or eviction of active sessions is introduced.
- [x] A10) [P1] MyMCP/package/server version, host configuration schema documentation, README, Architecture, Glossary, Authentication/session guidance, Plugin Architecture identity/version tables, scoped guidance, release notes, tests, and applicable guards state the delivered configuration contract and its complete version impact.
- [x] A11) [P1] Focused TDD validation, the full automated suite, package/import/version checks, `compileall`, `git diff --check`, and direct redacted authenticated expiry/disabled-expiry protocol checks pass without changing plugin or Mnemosyne contracts.

Why now / impact
- MyMCP correctly returns HTTP 404 for expired Streamable HTTP sessions, but the currently used OpenCode client has documented stale-session recovery gaps. The fixed 30-minute inactivity limit can therefore leave a local client displayed as connected while its cached session is unusable. Operator-selected lifetimes provide a bounded compatibility choice without weakening reauthentication or allowing a stale session identifier to be renewed.
- This is one bounded host-configuration and host-session-lifecycle Track. It does not implement client reconnect logic and does not make an expired identifier valid again.

Scope
- In scope:
  - Host configuration schema 7, preserving schema 6's `strict_protocol_version` behavior and adding an exact `[mcp]` lifetime shape.
  - `session_inactivity_timeout_seconds` and `session_absolute_lifetime_seconds`, each represented as a positive bounded integer or `0` to disable that limit.
  - Immutable propagation from configuration snapshot through production app construction to `ProcessLocalSessionStore`.
  - Deterministic expiry, disabled-limit, boundary, restart-loss, capacity, and route/application integration tests.
  - Public version-impact review and updates to affected documentation, scoped guidance, release notes, and guards.
- Out of scope:
  - OpenCode or any other MCP-client implementation, reconnect/retry behavior, heartbeat, or client status reporting.
  - Session renewal, session refresh endpoints or Tools, session listing, persistent/shared sessions, cross-process state, or hot configuration reload.
  - Authentication contract v1, Authentication adapters, verifier/JWKS snapshots, OAuth metadata/challenge, or anonymous admission semantics.
  - Governance policy, Tool authorization, exact-call approval, audit, or any plugin capability.
  - Runtime-generation meaning, MCP message semantics, endpoint paths, header grammar, or protocol revision changes.
  - Mnemosyne plugin code, Tool definitions, memory configuration, storage, records, and lifecycle behavior.

Milestones
- [ ] M1) Resolve the exact schema-7 configuration shape, bounds, disabled-limit semantics, default compatibility, expiry boundaries, and complete identity/version impact; record the decisions below before activation.
- [ ] M2) Add and validate schema-7 parsing, immutable configuration values, schema compatibility, source-shape rejection, and production bootstrap propagation through focused TDD.
- [ ] M3) Add and validate parameterized host session-store expiry behavior for custom values, each disabled mode, both disabled, exact boundaries, activity refresh, restart loss, capacity, and invalid settings.
- [ ] M4) Add and validate application/route behavior for configured expiration, disabled expiration, Authentication-first ordering, body-free 404 outcomes, DELETE termination, anonymous stateless behavior, and operator-bearer/OAuth parity.
- [ ] M5) Complete documentation/version/release-note work, full validation, direct redacted protocol checks, independent review, and Track completion evidence.

Risks / decisions
- Risk: Disabling expiration can retain stale in-memory session state indefinitely and increase exposure if a local bearer principal is compromised.
- Mitigation: Keep expiration enabled by default, require explicit schema-7 values, retain reauthentication on every use, preserve principal/runtime binding, keep the 128-session cap, and retain explicit DELETE and restart invalidation.
- Risk: A disabled inactivity limit could allow an otherwise unused session to consume one bounded slot indefinitely.
- Mitigation: Keep the fixed capacity bound and fail new session creation with the existing body-free 503 when capacity is exhausted; do not evict active sessions.
- Risk: A configurable public lifecycle changes behavior beyond the prior fixed host contract.
- Mitigation: Require the complete version-impact decision and automated configuration/version guards before activation.
- Decision: Schema 7 preserves schema-6 exact `[mcp]` ownership and adds exactly `session_inactivity_timeout_seconds` and `session_absolute_lifetime_seconds`; no other keys are accepted.
- Decision: Each lifetime accepts a native TOML integer from `0` through `2,592,000` seconds (30 days). `0` disables that limit and positive values mean seconds. Booleans, floats, strings, negative values, and values above the bound are rejected. No textual disabled form is supported.
- Decision: Schema 7 requires the `[mcp]` table and both lifetime keys. Schemas 1–6 and absent-file defaults retain the current fixed values and strictness behavior.
- Decision: Internally, disabled limits are represented as `None`; the session store continues to use the injected monotonic clock and expires when an enabled limit is reached: inactivity uses the established strict `>` boundary and absolute lifetime uses `>=` at the deadline.
- Decision: Both limits may be disabled together. The session remains valid until explicit DELETE, process restart, principal/runtime invalidation, or capacity-store loss; there is no renewal or persistence.
- Version impact: This is a public `/mcp` lifecycle/configuration change. The release impact is MyMCP distribution/package/server `0.9.0` → `0.10.0`, and host configuration schema `6` → `7`.
- Version impact — unchanged MCP protocol: Remains `2025-11-25`; only host-selected lifetime values change when schema 7 is used, while negotiation and protocol-header behavior remain unchanged.
- Version impact — unchanged HTTP surface: `/mcp` methods and `/health`, `/version`, and conditional OAuth metadata paths remain unchanged; existing 400/404/503 transport outcomes and response-header grammar remain unchanged.
- Version impact — unchanged Authentication: Authentication contract v1, principal normalization, adapter identities, authentication-first ordering, bearer methods, OAuth validation, and OAuth challenge behavior remain unchanged because lifetime settings are consumed only after Authentication.
- Version impact — unchanged Authentication source formats: Operator-bearer verifier snapshots and OAuth discovery/JWKS formats remain unchanged; session lifetime is not credential or issuer configuration.
- Version impact — unchanged host/plugin API and manifest: Host plugin API 1, manifest schema 1, external-plugin author contract 1, and startup composition remain unchanged because no plugin receives session state or configuration.
- Version impact — unchanged plugin/capability/data contracts: Bundled and external plugin identities, versions, capability contracts, endpoint bindings, plugin configuration, plugin-data, and worker protocol remain unchanged.
- Version impact — unchanged runtime generation and policy: Runtime-generation identity remains per-start and opaque; policy revision, Governance, approval, and audit remain deferred and unchanged.
- Version impact — unchanged Mnemosyne: Mnemosyne plugin identity/version, memory Tool contracts, configuration, storage, record schemas, mutation gates, consent, and lifecycle remain unchanged.

Open questions
- [x] Q1) What finite maximum is appropriate for each lifetime value, and should schema 7 permit `0` only or also a textual disabled form? Answer: accept native TOML integers `0..2,592,000` only; `0` disables the limit and textual disabled forms are rejected.
- [x] Q2) Should schema 7 require both lifetime keys, or provide defaults for omitted keys while requiring the `[mcp]` table? Answer: require both lifetime keys for explicit operator intent; schemas 1–6 and absent-file defaults preserve the existing values.
- [x] Q3) What exact inactivity boundary should remain compatible with the current implementation (`>` versus `>=`), and should the Track preserve it or correct it? Answer: preserve the existing semantics: inactivity expires only when elapsed time is greater than the configured timeout, while absolute lifetime expires at `>=` its deadline.
- [x] Q4) Does the delivered behavior materially change the living roadmap, requiring a separately approved roadmap revision? Answer: no. This is not roadmap-derived and does not alter the Phase 4 sequencing or next major Governance step; the roadmap remains current.

Decision log
- Decision (planning): One Track is sufficient because the change is bounded to host configuration, immutable startup propagation, and the existing host-owned session store/application seams; no client, plugin, or Mnemosyne work is required.
- Decision (planning): Track 046 explicitly excluded configuration-driven session settings, renewal, persistence, sharing, and session APIs; this Track does not reopen those exclusions.
- Decision (planning): The MCP specification's required client response to a 404 carrying an MCP-Session-Id remains a client responsibility. This Track offers an operator compatibility control; it does not alter expired-session rejection or make OpenCode reconnect.
- Decision (planning): The existing 128-session bound remains unchanged and is the primary resource-control guard when either or both lifetime limits are disabled.
- Decision (version impact): Before activation, the Track must retain a complete approved decision for distribution/endpoint markers, MCP protocol, HTTP routes, host configuration schema, Authentication contract/adapters/source formats, host plugin API, manifest/external-plugin contract, worker protocol, plugin/capability/plugin-data contracts, runtime generation, policy revision, bindings, and all Mnemosyne configuration/storage/record dimensions, including reasons for every unchanged dimension.

Plan (execution steps)
- [x] S1) Resolve Q1–Q4, finalize the schema-7 grammar/bounds/defaults/disabled semantics, complete the version-impact decision, and record the next exact TDD chunks.
- [x] S2) Move Track 049 to ACTIVE (folder, filename, and title status), check this step, and obtain any required implementation approval before changing code or tests.
- [x] S3) TDD chunk 1 — add failing configuration/schema-7 tests for exact shape, bounds, disabled values, required keys, compatibility defaults, immutable snapshot values, and production propagation; implement the smallest passing configuration/bootstrap change; refactor, validate, and update this Track.
- [x] S4) TDD chunk 2 — add failing session-store tests for custom inactivity/absolute values, disabled limits, both disabled, boundary semantics, activity refresh, restart loss, capacity, and invalid constructor values; implement the smallest passing host-session change; refactor, validate, and update this Track.
- [x] S5) TDD chunk 3 — add failing application/route tests for configured expiry, disabled expiry, body-free 404 behavior, Authentication-first ordering, DELETE, anonymous stateless handling, and operator-bearer/OAuth parity; implement the smallest host/application integration; refactor, validate, and update this Track.
- [x] S6) Update version markers, README, `docs/CONFIGURATION.md`, `docs/AUTHENTICATION.md`, `docs/ARCHITECTURE.md`, `docs/GLOSSARY.md`, `docs/PLUGIN_ARCHITECTURE.md`, scoped guidance, release notes, and applicable guards; run focused/full/package/import/compile/version checks, `git diff --check`, and direct redacted protocol checks.
- [x] S7) Obtain independent acceptance review, inspect and reconcile the linked roadmap under separate approval if needed, capture all evidence, and move Track 049 to COMPLETED only after every acceptance criterion passes.

Current inventory
- `mymcp/host/sessions.py` owns bounded configurable inactivity/absolute lifetimes, injected monotonic-clock testing, expiry lookup, activity refresh, process-local storage, and the 128-session cap.
- `mymcp/host/configuration.py` supports host configuration schemas 1–7. `HostMCPConfiguration` retains `strict_protocol_version` and adds immutable schema-7 lifetime values; schemas 1–6/absent configuration retain fixed defaults.
- `mymcp/app.py` propagates immutable lifetime values from production configuration into `ProcessLocalSessionStore` through the host application boundary.
- `mymcp/host/mcp_application.py` owns session creation, validation, activity refresh through valid requests, termination, and body-free 400/404/503 application outcomes.
- `mymcp/routes/mcp.py` extracts bounded session/protocol headers and delegates lifecycle decisions; no route-level expiry logic should be added.
- `tests/host/test_sessions.py`, `tests/host/test_mcp_application.py`, `tests/host/test_configuration_schema.py`, `tests/routes/test_mcp_sessions.py`, `tests/routes/test_operator_bearer_route.py`, and `tests/routes/test_oauth_protected_resource.py` provide the existing focused seams.
- `mymcp/settings.py` identifies MyMCP/package/server version `0.10.0`; `PROTOCOL_VERSION` remains `2025-11-25`.
- `docs/CONFIGURATION.md`, `README.md`, `docs/AUTHENTICATION.md`, `docs/ARCHITECTURE.md`, `docs/GLOSSARY.md`, `docs/PLUGIN_ARCHITECTURE.md`, scoped guidance, and `docs/releases/0.10.0.md` document schema 7 and configurable lifetime behavior.

Artifacts
- MCP Streamable HTTP transport specification, session-management section: <https://modelcontextprotocol.io/specification/2025-11-25/basic/transports>.
- OpenCode issue #25137 documents stale Streamable HTTP session IDs and missing automatic reconnect in affected releases: <https://github.com/anomalyco/opencode/issues/25137>.
- OpenCode issue #29190 documents stale “connected” status after remote MCP transport failure: <https://github.com/anomalyco/opencode/issues/29190>.
- OpenCode issue #37626 documents remaining invalid-session recovery gaps in an SSE path: <https://github.com/anomalyco/opencode/issues/37626>.
- OpenCode PR #39247 records that legacy session-expiry HTTP 404 reconnect/retry was deferred in the SDK-v2 upgrade: <https://github.com/anomalyco/opencode/pull/39247>.
- `.backlog/COMPLETED/2026/TRACK_046_COMPLETED_mcp_principal_session_integration.md` — delivered fixed session lifecycle and explicit exclusion of configuration-driven session settings.
- `.backlog/COMPLETED/2026/TRACK_047_COMPLETED_configurable_mcp_protocol_header_strictness.md` — delivered schema 6 and the current `[mcp]` configuration seam.
- This Track is not currently roadmap-derived; roadmap reconciliation is still required at completion if the delivered baseline changes a linked roadmap statement.

Completion notes
- Track created as DRAFT on 2026-08-04. No implementation, implementation-driving tests, configuration change, version change, commit, or push was performed.
- 2026-08-04: S1 complete after explicit user approval. Resolved the schema-7 exact shape, `0..2,592,000` integer-second bounds, required lifetime keys, disabled-limit semantics, preserved expiry boundaries, complete version impact, and roadmap disposition.
- 2026-08-04: S2 complete after explicit user approval. Track moved to ACTIVE; next unchecked step is S3, configuration/schema-7 TDD.
- 2026-08-04: S3 complete. Added strict schema-7 parsing, required bounded native integer lifetime keys, zero-to-None mapping, immutable snapshot coverage, compatibility defaults, and production propagation coverage. Focused configuration/application validation passed.
- 2026-08-04: S4 complete. Added configurable session-store expiry, independent disabled limits, preserved inactivity/absolute boundaries, activity refresh, capacity, restart-loss, and constructor validation. Session-focused validation passed.
- 2026-08-04: S5 complete. Application construction now passes configured lifetimes to the host-owned session store without route-level expiry logic; existing body-free failure, Authentication-first, DELETE, anonymous, and protocol behavior remained green in the focused suites.
- 2026-08-04: S6 complete. Updated public version to `0.10.0`, host configuration schema documentation, release notes, identity/version guards, and scoped guidance. Full suite passed: 2060 passed, 3 skipped; `compileall`, import/version check, and `git diff --check` passed. Direct redacted authenticated protocol checks and independent acceptance review remain for S7.
- 2026-08-04: S7 complete. Independent review found no correctness or security regression. Focused direct route evidence passed (`69 passed`) for MCP sessions, operator bearer, OAuth protected-resource behavior, and application construction; full suite remained green (`2060 passed, 3 skipped`). Roadmap is not linked/roadmap-derived, so no roadmap mutation was required; completion is recorded here.
- 2026-08-04: Final pre-release correction: schema-7 TOML booleans are now rejected explicitly instead of being treated as integer zero by Python equality semantics. Added focused regression coverage for both lifetime fields.

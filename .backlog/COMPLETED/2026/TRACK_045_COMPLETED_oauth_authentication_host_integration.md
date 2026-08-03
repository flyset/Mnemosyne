# TRACK 045 [COMPLETED]: OAuth Authentication host integration

Track
- ID: TRACK_045
- Repository: MyMCP
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_045_COMPLETED_oauth_authentication_host_integration.md

Problems (PORE)
- P1: As a MyMCP operator, I cannot configure the TRACK_044 OAuth validator as the process Authentication method because host configuration and startup composition do not select it.
- P2: As an OAuth-capable MCP client, I cannot discover MyMCP's protected resource or receive a useful Bearer challenge because MyMCP publishes no protected-resource metadata.
- P3: As a MyMCP user, I need OAuth integration to remain upstream of MCP and separate from Governance, because identity establishment must not silently grant Tool authority.

Objective
- Integrate the completed TRACK_044 validation foundation as one startup-fixed production Authentication method, publish the minimum protected-resource discovery contract, and deliver MyMCP 0.7.0 without changing downstream MCP, plugin, Governance, or Mnemosyne semantics.

Non-negotiables
- TRACK_044 must be completed and its acceptance evidence reviewed before this Track activates.
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- MyMCP is an OAuth resource server only; the client obtains and presents access tokens.
- Exactly one external authorization server and at most one Bearer Authentication method may be configured per process.
- OAuth and `operator-bearer-v1` cannot be co-declared in one schema-5 document, including disabled declarations. Token shape never selects an adapter.
- Enabled OAuth requires `anonymous_enabled=false`; evidence-free and invalid-evidence requests never become anonymous.
- HTTP remains thin: routes extract evidence and map Authentication outcomes; OAuth validation remains in Authentication and MCP receives only a normalized principal.
- OAuth establishes identity only. Sessions, Governance, Tool authorization, scopes-to-policy mapping, approval, audit, plugin trust, and consent remain out of scope.
- The canonical resource identity derives only from validated loopback server address and port, never request Host or forwarded headers.
- OAuth on the literal loopback HTTP endpoint is an explicit local interoperability exception, not an RFC-conformant HTTPS or remote deployment.
- No provider account, token, credential, secret, key, or live network interoperability action is required.

Acceptance criteria
- [x] A1) [P1] Host configuration schema 5 expresses one bounded OAuth issuer intent, strictly validates it, preserves schemas 1-4 and absent configuration, and composes one immutable adapter before plugin runtime publication.
- [x] A2) [P1] Invalid, ambiguous, unavailable, unsafe, or incompatible OAuth startup fails closed with bounded content-free output and no partial runtime.
- [x] A3) [P1] A valid access token reaches the TRACK_044 validator and yields only `Principal.registered(configured_adapter_id, stable_subject)` through unchanged Authentication contract v1.
- [x] A4) [P1] OAuth and `operator-bearer-v1` co-declaration is rejected; either method configured alone retains the unchanged exact Authorization Bearer evidence route.
- [x] A5) [P1] Enabled OAuth requires anonymous access disabled; missing or failed evidence never falls back to anonymous.
- [x] A6) [P2] MyMCP serves exact RFC 9728-shaped protected-resource metadata only at `/.well-known/oauth-protected-resource/mcp`, with `Cache-Control: no-store`, the exact resource, one configured authorization server, `bearer_methods_supported=["header"]`, and no scopes.
- [x] A7) [P2] Every OAuth-protected `/mcp` Authentication failure occurs before streaming, request-body parsing, MCP logging, or dispatch; it remains body-free HTTP 401 and carries exactly `WWW-Authenticate: Bearer resource_metadata="<metadata URL>"`. Operator-bearer and anonymous-only configurations retain challenge-free behavior.
- [x] A8) [P2] MyMCP does not host authorization-server metadata, OpenID Provider metadata, dynamic client registration, or `/register`.
- [x] A9) [P1] [P2] Exact loopback IPv4 and IPv6 resource/audience identifiers derive from validated server configuration, not request-controlled headers.
- [x] A10) [P3] Existing MCP protocol behavior, Tool discovery/dispatch, plugin composition, runtime-generation semantics, Mnemosyne identities, and `operator-bearer-v1` remain unchanged except for approved upstream OAuth behavior.
- [x] A11) [P1] [P2] [P3] MyMCP/package/server reports 0.7.0; focused/full/import/version/package tests, direct OAuth/operator/anonymous MCP checks, and independent acceptance review pass.
- [x] A12) [P1] [P2] [P3] README, Authentication, Configuration, Architecture, Glossary, Plugin Architecture, tests guidance, release notes, scoped guidance, and this Track describe the delivered contract and exclusions.
- [x] A12a) [P1] [P2] Documentation and test examples contain no usable token, credential, private key, provider response, secret-bearing URL, or real provider/account identifier.
- [x] A13) [P1] [P2] [P3] The linked roadmap is inspected and its reconciliation outcome recorded before completion.

Why now / impact
- TRACK_044 isolates and proves the cryptographic/network validation boundary. This Track can therefore focus on the separately reviewable public configuration, startup, and HTTP contracts required to make that validator usable.

Scope
- In scope:
  - Host configuration schema 5 and exact `[authentication.oauth_jwt] issuer` intent.
  - OAuth/operator Bearer-method exclusion and mandatory disabled anonymous access.
  - Loopback resource identity derivation and startup validation-snapshot composition.
  - Production adapter registration through existing exact routing and normalized principals.
  - RFC 9728 protected-resource metadata and exact Bearer challenge.
  - MyMCP 0.7.0, tests, documentation, package validation, direct MCP checks, and roadmap reconciliation.
- Out of scope:
  - Token parsing/cryptography and metadata/JWKS loader implementation except integration corrections required by reviewed TRACK_044 contracts.
  - OAuth client behavior, authorization-server endpoints, client registration, opaque introspection, refresh, immediate revocation, scopes-to-Tools policy, sessions, Governance, approval, audit, remote deployment, TLS termination, and multi-user operation.
  - Generic adapter loading, host-managed dependencies, hot configuration, provider management, or plugin changes.

Milestones
- [x] M1) Confirm TRACK_044 completion and finalize integration-specific design/activation decisions.
- [x] M2) Deliver schema 5 and production startup composition.
- [x] M3) Deliver protected-resource metadata and Bearer challenge behavior.
- [x] M4) Complete MyMCP 0.7.0 documentation, validation, direct checks, acceptance, and roadmap reconciliation.

Risks / decisions
- Risk: Both production methods use Authorization Bearer; strict configuration exclusion must prevent probing, ordering, or token-shape inference.
- Risk: A new public route and challenge affect endpoint compatibility and client behavior.
- Risk: Request-derived host information could corrupt resource/audience identity; only validated server configuration may determine it.
- Risk: Loopback HTTP lacks OAuth's normal TLS confidentiality and must not be represented as remote-ready or standards-conformant deployment.
- Decision: Schema 5 preserves schemas 1-4 and adds exact optional `[authentication.oauth_jwt]` with only non-secret `issuer`. The table is required whenever `oauth-jwt-jwks-v1` is declared, including disabled, and prohibited otherwise.
- Decision: OAuth and `operator-bearer-v1` are alternative process configurations and cannot be co-declared in schema 5. Switching requires configuration replacement and restart.
- Decision: Enabled OAuth requires `anonymous_enabled=false`; failed submitted evidence never becomes anonymous.
- Decision: The canonical resource is `http://<IPv4>:<port>/mcp` or `http://[<compressed-IPv6>]:<port>/mcp`, derived only from validated loopback server configuration. JWT audience must contain this exact value.
- Decision: Protected-resource metadata contains exactly `resource`, one-element `authorization_servers`, and `bearer_methods_supported=["header"]`; it omits scopes and is served with `no-store` only at `/.well-known/oauth-protected-resource/mcp`.
- Decision: OAuth-selected `/mcp` failures return body-free HTTP 401 with exactly `WWW-Authenticate: Bearer resource_metadata="<derived metadata URL>"`, without token-derived error distinctions. Existing configurations remain challenge-free.
- Decision: MyMCP does not answer `/.well-known/oauth-authorization-server`, `/.well-known/openid-configuration`, or `/register` as an authorization server.
- Decision: The literal loopback HTTP endpoint is a deliberate local exception; HTTPS termination and remote deployment require a separate Track.
- Version impact: MyMCP distribution/package/server advances from 0.6.0 to 0.7.0 because this Track adds a production OAuth method, host configuration schema 5, one public metadata route, and an OAuth-specific Bearer challenge.
  - MCP protocol and negotiation: unchanged; no MCP method, message, Tool, result, or error changes.
  - Existing endpoint identity: `/mcp`, `/health`, and `/version` remain; `/version` reports 0.7.0. One GET protected-resource metadata route is added.
  - HTTP Authentication failures: body-free 401 remains; only OAuth-selected failures add the approved challenge.
  - FastAPI identity, host plugin API 1, manifest schema 1, external plugin-author contract `mymcp_plugin_v1`, absent worker protocol, Authentication contract 1, `operator-bearer-v1`, verifier-source format 1, plugin/capability/data/runtime identities, Mnemosyne configuration/storage/record schemas, and absent Governance policy remain unchanged for the reasons stated in the acceptance scope.
  - Host configuration adds schema 5; schemas 1-4 remain supported unchanged.
  - Production adapter/profile identity is `oauth-jwt-jwks-v1`, implemented by TRACK_044 and selected here.

Open questions
- [x] Q1) Split validation/loading from public host integration before activation.
- [x] Q2) Keep schema 5, resource derivation, composition, metadata route, challenge, and 0.7.0 delivery together because they form one observable production feature.
- [x] Q3) Before activation, confirm TRACK_044 completed without changing the integration assumptions recorded here.

Decision log
- Decision (split): The user approved TRACK_045 as the production-integration successor to the validation-only TRACK_044.
- Decision (roadmap): TRACK_044 and TRACK_045 are Phase 4 Tracks 3a and 3b; the roadmap's external OAuth outcome completes only when this Track completes.
- Decision (dependency): TRACK_045 must not activate before TRACK_044 completion and review.
- Decision (version impact): TRACK_045 advances MyMCP/package/server from 0.6.0 to 0.7.0, adds host configuration schema 5, selects production adapter/profile `oauth-jwt-jwks-v1`, adds one public protected-resource metadata GET route, and adds the OAuth-specific Bearer challenge. MCP protocol, FastAPI identity, host plugin API 1, manifest schema 1, external plugin-author contract, absent worker protocol, Authentication contract 1, `operator-bearer-v1`, verifier-source format 1, plugin/capability/data/runtime identities, Mnemosyne schemas, and absent Governance policy remain unchanged for the complete reasons listed under Risks / decisions.
- Decision (Q3): TRACK_044 completed with its validator, immutable startup snapshot loader, dormancy guards, full-suite/package/import validation, and independent acceptance review passing. Its delivered contracts preserve every integration assumption recorded here; no TRACK_045 correction is required before activation.
- Decision (activation): The user explicitly approved moving TRACK_045 to ACTIVE and checking S3. Implementation remains limited to one declared TDD chunk at a time; network actions, memory mutations, commit, push, tag, release, and credential handling remain unauthorized.
- Decision (S4 route): The `oauth-jwt-jwks-v1` adapter claims the exact `(authorization, bearer, None)` route shared with `operator-bearer-v1` because the HTTP boundary cannot distinguish token shapes; schema-5 co-declaration exclusion guarantees the two Bearer methods are never composed together, and the TRACK_044 route-profile tests were reconciled with focused coverage. Token shape never selects an adapter.
- Decision (S4 seams): Enabled-OAuth composition loads the discovery snapshot through injectable `_OAUTH_DISCOVERY_FETCH`/`_OAUTH_CLOCK` seams with deterministic offline test doubles; ordinary startup never loads `PyJWT[crypto]`.
- Decision (S4 shared helper): A new standard-library-only `mymcp/authentication/oauth.py` owns the canonical issuer/resource/profile identities so strict schema-5 and composition validation never imports the `PyJWT[crypto]` runtime.
- Decision (S5 metadata URL): The Bearer challenge's `resource_metadata` value and the metadata endpoint URL both derive from validated loopback server configuration via the new standard-library-only `derive_oauth_metadata_url`; request Host and forwarded headers never influence either identity.
- Decision (S5 app seam): `mymcp/app.py` derives the immutable `OAuthProtectedResource` surface directly from validated schema-5 configuration (oauth_jwt table plus an enabled `oauth-jwt-jwks-v1` declaration); host Authentication composition, the Authenticator, and the OAuth adapter are unchanged. Anonymous/operator/default/disabled-OAuth configurations never register the metadata route or present the challenge.

Plan (execution steps)
- [x] S1) Create this DRAFT successor during the approved split, carrying forward the public integration, complete version-impact, and release requirements from the original TRACK_044.
- [x] S2) Inspected TRACK_044 completion evidence and resolved Q3: its delivered contracts require no integration corrections.
- [x] S3) After separate explicit user approval, moved TRACK_045 to ACTIVE by synchronizing folder, filename, title, and Current path before implementation or implementation-driving tests.
- [x] S4) TDD chunk 1 (completed) — added focused failing tests for exact schema-5 parsing and issuer intent, schemas 1-4 compatibility, Bearer-method co-declaration rejection, mandatory disabled anonymous access, loopback resource derivation, bounded failures, immutable snapshot loading, production adapter composition, and Authentication-before-plugin-runtime ordering; implemented schema 5 and the lazy production OAuth composition; refactored, validated with the full suite, and recorded evidence below.
- [x] S5) TDD chunk 2 — added focused failing tests for thin OAuth evidence handling, body-free pre-MCP 401 with exact challenge, the single protected-resource metadata route/no-store response, IPv4/IPv6 identity, existing-configuration compatibility, and absence of authorization-server/registration routes; added the smallest route/application implementation; refactored, validated, and updated this Track.
- [x] S6) TDD chunk 3 — updated MyMCP/package/server to 0.7.0, version and packaging guards, README, Authentication, Configuration, Architecture, Glossary, Plugin Architecture, scoped guidance, tests guide, and release notes; ran focused/full/package/import/version checks and offline direct OAuth/operator/anonymous MCP checks; updated this Track.
- [x] S7) Ran independent acceptance review, inspected and reconciled the linked roadmap under separate mutation approvals, recorded all evidence, and transitioned status/path/title together after every acceptance criterion passed.

Current inventory
- TRACK_042 and TRACK_043 provide Authentication contract v1, exact routing, normalized principals, schemas 3-4, `operator-bearer-v1`, and pre-MCP 401 handling.
- TRACK_044 is the completed prerequisite for the pure OAuth validator and immutable metadata/JWKS snapshot loader; its `oauth-jwt-jwks-v1` adapter now claims the exact Authorization/Bearer route so the HTTP boundary can reach it.
- `mymcp/authentication/oauth.py` is the new standard-library-only shared helper owning `validate_oauth_issuer`, the `oauth-jwt-jwks-v1` profile identity, and loopback resource/audience derivation; it is never re-exported and never loads `PyJWT[crypto]`.
- `mymcp/host/configuration.py` owns strict schemas 1-5; schema 5 adds exact optional `[authentication.oauth_jwt] issuer`, requires it iff an oauth declaration exists (including disabled), prohibits it otherwise, rejects OAuth/operator-bearer co-declaration, and preserves schemas 1-4 unchanged.
- `mymcp/host/authentication.py` composes `operator-bearer-v1` and, for enabled schema-5 OAuth, lazily loads the discovery snapshot through injectable `_OAUTH_DISCOVERY_FETCH`/`_OAUTH_CLOCK` seams, derives the loopback resource audience, requires anonymous disabled, and fails bounded before plugin runtime publication.
- `mymcp/routes/mcp.py` owns bounded Authorization extraction and transport mapping and presents the exact OAuth-only Bearer challenge when it receives the S5 metadata URL; current public routes remain `/mcp`, `/health`, and `/version`, with the metadata route and challenge added only for enabled OAuth.
- `mymcp/routes/oauth.py` (S5) is the thin RFC 9728 protected-resource metadata surface: it owns the immutable `OAuthProtectedResource` value and the single GET `/.well-known/oauth-protected-resource/mcp` route serving exactly `resource`, one-element `authorization_servers`, and `bearer_methods_supported=["header"]` with `Cache-Control: no-store`.
- `mymcp/app.py` derives the `OAuthProtectedResource` surface from validated schema-5 configuration (enabled-OAuth only) and threads the challenge URL plus metadata router into the FastAPI assembly; non-OAuth configurations receive no route and no challenge.
- `mymcp/authentication/oauth.py` additionally owns `derive_oauth_metadata_url` (loopback IPv4/IPv6 metadata URL), still standard-library-only.
- `pyproject.toml` and `mymcp/settings.py` identify MyMCP/package/server 0.7.0. The isolated wheel metadata also reports 0.7.0; the current long-lived editable environment still exposes stale installed-distribution metadata 0.6.0 and requires reinstall/reconnect outside this Track's authorized workspace changes.

Artifacts
- Prerequisite: `.backlog/COMPLETED/2026/TRACK_044_COMPLETED_oauth_validation_foundation.md`.
- Authentication architecture: `docs/AUTHENTICATION.md`.
- Host configuration: `docs/CONFIGURATION.md`.
- Architecture/version model: `docs/ARCHITECTURE.md`, `docs/PLUGIN_ARCHITECTURE.md`, and `docs/GLOSSARY.md`.
- Workflow: `docs/AI_WORKFLOW.md`, `.backlog/README.md`, `.backlog/PORE.md`, and applicable `AGENTS.md` files.
- Roadmap references: `project/mymcp/roadmaps`; canonical index `mem_5f3b5f4871d0406995f222d48e0357b7`; Phase 4 `mem_ec6d4b50c830463383ad0d1e221910c7`.

Completion notes
- Created under explicit user approval by splitting the original DRAFT TRACK_044 before implementation.
- Reviewed TRACK_044 completion evidence for S2/Q3. Its acceptance criteria A1-A10, focused/full/package/import checks, dormancy proof, and independent review passed; the resulting validator and loader contracts match this Track's issuer, resource-audience, immutable-snapshot, bounded-failure, and production-composition assumptions without correction.
- S4 (TDD chunk 1) delivered schema 5 and production startup composition.
  - Red evidence: `python -m pytest -q tests/host/test_oauth_host_integration.py` failed at collection (missing shared OAuth helper module and schema-5 composition); the flagged compatibility run reported 32 failed / 27 passed including the pre-change dormancy/route/unsupported-version guards.
  - Implementation: added standard-library-only `mymcp/authentication/oauth.py` (canonical `validate_oauth_issuer`, `OAUTH_JWT_PROFILE`, `derive_oauth_resource`), re-homed the issuer validator out of `oauth_jwt.py`, changed the `oauth-jwt-jwks-v1` adapter route to the exact `(authorization, bearer, None)` route so HTTP extraction can reach it, added schema 5 with exact optional `[authentication.oauth_jwt] issuer` plus co-declaration/consistency/issuer validation, and extended `mymcp/host/authentication.py` with lazy OAuth discovery/snapshot composition behind injectable `_OAUTH_DISCOVERY_FETCH`/`_OAUTH_CLOCK` seams, loopback resource-audience derivation, mandatory disabled anonymous access, and bounded content-free composition errors.
  - Reconciliations: updated the S5-era dormancy guards to reflect that schema 5 and the OAuth adapter are now production-registered while ordinary startup still never loads `PyJWT[crypto]` (module-level import scan + runtime probes retained), replaced the unsupported-version fixtures with schema 6, and updated the TRACK_044 OAuth route-profile tests to the exact bearer route with focused coverage.
  - Green evidence: 36 new S4 focused tests passed; `python -m pytest -q tests/host/test_oauth_host_integration.py tests/test_oauth_dormancy.py tests/host/test_configuration_schema.py tests/authentication/adapters/test_oauth_jwt.py tests/authentication/adapters/test_oauth_discovery.py` passed 455; host/routes/authentication/app suites passed 841 with 3 platform skips; the complete suite passed 1978 with 3 skips; packaging/import/identity checks passed 42; `git diff --check` passed.
- This Track owns the complete public OAuth outcome and roadmap reconciliation; S6 delivered the 0.7.0 version/docs/package/direct-check work, while S7 acceptance and roadmap reconciliation remain.

# S5 (TDD chunk 2) — protected-resource metadata and OAuth-only Bearer challenge

- Red evidence (before implementation): the shared-helper import guard failed at
  collection (`ImportError: cannot import name 'derive_oauth_metadata_url'`), and
  the new focused route suite `python -m pytest -q tests/routes/test_oauth_protected_resource.py`
  returned 11 failed / 8 passed: the metadata route was absent (404), non-GET
  methods were not 405, the body was not RFC 9728-exact, no-store was absent, and
  `/mcp` failures carried no `WWW-Authenticate`. The 8 passes were the
  existing-configuration compat guards (default anonymous, disabled OAuth,
  operator-bearer) and the authorization-server/registration absence guards,
  proving only the intended OAuth surface was missing.
- Implementation (smallest, conditional, OAuth-only):
  - Added standard-library-only `derive_oauth_metadata_url(address, port)` to
    `mymcp/authentication/oauth.py`, deriving the loopback
    `http://<IP>:<port>/.well-known/oauth-protected-resource/mcp` identity from
    validated server configuration (IPv4 dotted / IPv6 compressed bracketed).
  - Added `mymcp/routes/oauth.py` with the immutable `OAuthProtectedResource`
    value and a GET-only router for `/.well-known/oauth-protected-resource/mcp`
    returning exactly `{resource, authorization_servers, bearer_methods_supported}`
    with `Cache-Control: no-store`; it never reads Host/forwarded headers.
  - Extended `mymcp/routes/mcp.py` `create_router` with an optional
    `oauth_resource_metadata_url` keyword; when set, Authentication failures
    return a body-free pre-MCP `401` with exactly
    `WWW-Authenticate: Bearer resource_metadata="<metadata URL>"` (no
    token-derived error distinction), otherwise the empty 401 is unchanged.
  - Extended `mymcp/app.py`: `create_app` accepts an optional
    `oauth_protected_resource` and conditionally includes the metadata router and
    passes the challenge URL; `create_production_app` derives the
    `OAuthProtectedResource` only for enabled schema-5 OAuth (oauth_jwt table plus
    an enabled `oauth-jwt-jwks-v1` declaration), keeping anonymous/operator/
    disabled-OAuth/schema 1-4 configurations route- and challenge-free. No
    authorization-server, OpenID Provider, or `/register` routes are added.
  - Reconciliation: updated the S4 ordering test's monkeypatched `create_app`
    stub to accept the new keyword and asserted the delivered resource surface;
    Authentication validation/composition itself is unchanged.
- Green evidence:
  - `python -m pytest -q tests/routes/test_oauth_protected_resource.py tests/host/test_oauth_host_integration.py` passed 58 (19 new S5 route tests + 3 new metadata-URL derivation tests alongside the S4 suite).
  - `python -m pytest -q tests/test_oauth_dormancy.py tests/host/test_configuration_schema.py tests/test_app.py tests/routes/ tests/authentication/adapters/` passed 650 (S4/S5 guards and route suites).
  - `python -m pytest -q` passed the complete suite: 2000 passed, 3 skipped (baseline 1978).
  - `git diff --check` passed.

# S6 (TDD chunk 3) — MyMCP 0.7.0 identity, documentation, and validation

- Red evidence: after changing the focused guards to require 0.7.0,
  `python -m pytest -q tests/test_project_identity.py tests/test_packaging.py`
  failed twice because `SERVER_VERSION` and the built wheel still reported
  0.6.0.
- Implementation: advanced only `pyproject.toml` and `mymcp/settings.py` to
  0.7.0; updated explicit server/package/version guards; strengthened wheel
  filename and METADATA assertions; updated README, Vision, Authentication,
  Configuration, Architecture, Glossary, Plugin Architecture, tests guidance,
  applicable scoped guidance, and `docs/releases/0.7.0.md`. Documentation uses
  reserved non-real examples and records the loopback HTTP exception, isolated
  PyJWT dependency, bounded token/revocation boundary, and unchanged identity
  dimensions without claiming a tag or publication.
- Green evidence:
  - Version/package guards passed 5 tests; focused OAuth/operator/anonymous
    route and adapter checks passed 403; schema/composition/bootstrap/app checks
    passed 169.
  - `python -m pytest -q` passed 2000 tests with 3 platform skips.
  - The isolated packaging test built and inspected
    `mymcp-0.7.0-py3-none-any.whl` in pytest temporary storage, verified
    dist-info `Version: 0.7.0`, the bounded PyJWT dependency, packaged OAuth
    modules/routes, manifest parity, and absence of repository build artifacts.
  - Source imports and the runtime marker report `mymcp 0.7.0`; the current
    long-lived editable environment's installed-distribution metadata remains
    stale at 0.6.0 and is not source or wheel evidence.
  - `git diff --check` passed. No live provider/network, credential, memory
    mutation, commit, push, tag, or release action occurred.
- S7 independent acceptance passed A1-A12a. The complete suite passed 2000 tests
  with 3 platform skips; focused OAuth acceptance passed 374 and compatibility
  acceptance passed 222; isolated wheel construction/inspection, compile/import,
  version, security/redaction, and `git diff --check` checks passed. Source and
  wheel report 0.7.0; stale installed metadata belongs to the long-lived editable
  environment and is not release evidence.
- Roadmap reconciliation was approved and completed in bounded order: delivered
  baseline revision 6 records TRACK_044/045 and MyMCP 0.7.0; Phase 4 revision 10
  records external OAuth delivered and method-neutral MCP principal/session
  integration NEXT; canonical index revision 17 records the new baseline and
  NEXT step. A13 is satisfied.
- Removed the generated untracked `build/` packaging artifact before completion.
  Unrelated local `opencode.json` changes were left untouched. No commit, push,
  tag, hosted release, live provider/network action, or credential handling was
  performed.
- TRACK_045 completed with every acceptance criterion, milestone, and plan step
  satisfied. MyMCP/package/server 0.7.0 is the delivered build state; publication
  remains a separate explicitly authorized action.

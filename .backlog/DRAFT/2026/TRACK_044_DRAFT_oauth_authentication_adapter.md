# TRACK 044 [DRAFT]: OAuth Authentication adapter

Track
- ID: TRACK_044
- Repository: MyMCP
- Branch: main
- Current path: .backlog/DRAFT/2026/TRACK_044_DRAFT_oauth_authentication_adapter.md

Problems (PORE)
- P1: As a MyMCP operator, I cannot configure MyMCP as an OAuth protected resource for one external OAuth authorization server, because MyMCP has no production OAuth Authentication adapter that validates externally issued access tokens.
- P2: As an MCP-client user, I cannot complete OAuth discovery and authenticate to MyMCP with an access token obtained by my client, because MyMCP publishes neither OAuth protected-resource metadata nor a Bearer challenge and has no bounded OAuth resource-server validation path for that token.
- P3: As a MyMCP maintainer, I could not safely implement OAuth access-token validation without first resolving the OAuth protected-resource profile, token-validation mechanism, authorization-server metadata, resource validation, validation material, caching, outage, revocation, challenge, subject, dependency, and strict bearer-method selection contracts recorded by this Track.
- P4: As a Mnemosyne user, I need OAuth Authentication to preserve the existing MCP, plugin, memory, anonymous-access, and operator-bearer contracts unless an approved compatibility decision changes them, because Authentication must remain upstream of MCP and domain behavior.

Objective
- Define and, only after DRAFT review and activation, deliver one startup-fixed host-owned OAuth Authentication adapter through which MyMCP, as an OAuth resource server, validates access tokens issued by exactly one configured external OAuth authorization server per process and maps valid tokens to the normalized registered-principal contract.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- MyMCP is an OAuth resource server only. The MCP client obtains and presents the access token; MyMCP does not perform browser login, authorization-code handling, refresh-token handling, client registration, token issuance, token exchange, or authorization-server administration.
- One MyMCP process may configure exactly one external OAuth authorization server for this adapter. Multiple external OAuth authorization servers in one process are out of scope.
- Host configuration, authorization-server metadata, and validation material are immutable for a process start. Configuration and signing-key changes require restart; the running process performs no refresh, introspection, or remote validation call.
- Preserve the layer order: HTTP server, Authentication, MCP server, Governance, Plugin runtime, Plugin, and Plugin data or external service.
- HTTP routes extract bounded evidence and map Authentication outcomes only. OAuth validation belongs in Authentication; MCP carries only normalized principals.
- Authentication remains transport-neutral and must not import FastAPI, routes, MCP, Governance, plugin contracts, plugins, or host configuration.
- The host constructs canonical principal identities. The OAuth adapter returns only one validated stable adapter-local subject or a bounded failure.
- OAuth Authentication establishes identity only. It grants no Governance allowance, Tool authorization, client consent, exact-call approval, plugin trust, isolation, or session semantics.
- Never expose raw access tokens, Authorization values, token claims, authorization-server responses, validation material, introspection responses, secret-bearing URLs, exception details, or tracebacks through principals, errors, logs, MCP, plugins, durable memory, or documentation examples.
- Submitted evidence routes by one exact host-derived descriptor to one enabled adapter. There is no token-shape inference, sequential adapter probing, registration-order selection, cross-adapter fallback, or fallback to anonymous access.
- OAuth and `operator-bearer-v1` are alternative Bearer Authentication methods for one MyMCP process. At most one may be enabled. A configuration enabling both fails startup; switching methods requires configuration change and restart.
- An enabled OAuth adapter requires `anonymous_enabled = false`; evidence-free requests must enter OAuth discovery rather than become anonymous. OAuth and `operator-bearer-v1` cannot be co-declared in one schema-5 document because both claim the same exact route, regardless of enabled state.
- OAuth-protected `/mcp` responses without acceptable evidence return HTTP 401 with a standards-conforming `WWW-Authenticate: Bearer` challenge containing the protected-resource metadata URL. MyMCP publishes RFC 9728 protected-resource metadata for its `/mcp` resource and advertises exactly the configured external OAuth authorization server.
- MyMCP does not publish authorization-server metadata or OpenID Provider metadata and does not implement dynamic client registration. Those remain responsibilities of the configured external authorization server.
- Preserve local-first, single-user, least-privilege, and loopback-only assumptions unless an explicitly approved decision changes them.
- Do not add unrestricted filesystem or network features, secret storage, generic external-adapter loading, host-managed dependency environments, plugin changes, or provider-management Tools or endpoints.
- Deterministic local fixtures, clocks, and controlled doubles are the primary automated-test method. Any real authorization-server interoperability check is supplementary, approval-gated, and must not place credentials in Git.
- This release permits OAuth bearer tokens and protected-resource metadata over the existing literal loopback HTTP endpoint as an explicit local interoperability exception and deliberate deviation from OAuth/RFC 9728 HTTPS transport requirements. Only the metadata document and challenge shapes follow those standards; this is not an RFC-conformant deployment, does not claim TLS equivalence, and supports no non-loopback OAuth endpoint. HTTPS termination and remote deployment remain future work.

Acceptance criteria
- [ ] A1) [P1] Host configuration expresses one bounded OAuth authorization-server intent per MyMCP process, validates it strictly, composes it immutably at startup, and records approved compatibility behavior for schemas 1-4 and absent configuration.
- [ ] A2) [P1] Invalid, ambiguous, unavailable, unsafe, or incompatible OAuth configuration fails closed before Authentication, MCP, or plugin-runtime publication, with bounded content-free output and no partial runtime.
- [ ] A3) [P2] A valid OAuth access token submitted through the approved exact evidence route yields only `Principal.registered(configured_adapter_id, stable_subject)`; host canonical-principal construction remains host-owned and no token or claim data is available downstream.
- [ ] A4) [P2] MyMCP performs no OAuth client, browser, redirect, callback, authorization-code, refresh-token, token-exchange, token-issuance, client-registration, or authorization-server-management behavior.
- [ ] A5) [P3] The adapter accepts only the approved RFC 9068-style compact `at+jwt` access-token profile signed with RS256 and validates exact issuer, exact MyMCP audience, signature and key suitability, required claims, time bounds, and stable subject derivation; opaque, encrypted, nested, ID, unsigned, symmetric, and other-algorithm tokens fail closed.
- [ ] A6) [P3] Enabled OAuth startup retrieves bounded RFC 8414 authorization-server metadata and bounded JWKS exactly once over validated HTTPS before runtime publication, retains one immutable validation snapshot, performs no runtime refresh or introspection, requires restart for key rotation, and makes no immediate-revocation claim beyond token expiry and restart-observed key removal.
- [ ] A7) [P2] [P3] MyMCP serves RFC 9728 OAuth protected-resource metadata for the `/mcp` resource with the exact resource identifier and exactly one configured authorization-server issuer, and every OAuth-protected `/mcp` HTTP 401 includes a standards-conforming `WWW-Authenticate: Bearer` challenge whose `resource_metadata` value identifies that document. The approved exact metadata fields, no-store behavior, absence of scope advertisement, canonical URI handling, and single path are covered by implementation tests.
- [ ] A8) [P3] Malformed, unsupported, ambiguous, expired, invalid, wrongly issued, wrongly targeted, revoked under the approved boundary, unavailable under the approved policy, or rejected OAuth evidence fails closed before streaming, body parsing, MCP logging, or dispatch and never becomes anonymous.
- [ ] A9) [P3] OAuth and `operator-bearer-v1` cannot be co-declared in one schema-5 document, even when one is disabled, because both claim the unchanged exact Authorization Bearer route; either method may be configured alone, token shape never selects an adapter, and switching requires configuration replacement and restart.
- [ ] A10) [P3] Automated tests use generated ephemeral RSA keys, an injected clock, and deterministic bounded fetch doubles for OAuth metadata, JWKS, token validation, startup outages, rotation, expiry-bound revocation, and failure modes; tests prove sensitive evidence is absent from representations, logs, errors, downstream calls, and durable state.
- [ ] A11) [P4] Existing MCP protocol behavior, endpoint routes, Tool discovery and dispatch, plugin composition, runtime-generation semantics, Mnemosyne identities and records, configured anonymous behavior, and `operator-bearer-v1` behavior remain unchanged except for explicitly approved upstream Authentication effects.
- [ ] A12) [P1] [P2] [P3] [P4] Focused tests, full suite, import-boundary tests, package and version guards, packaging checks, direct MCP checks, and any approved supplementary interoperability check pass.
- [ ] A13) [P1] [P2] [P3] [P4] README, Authentication, Configuration, Architecture, Glossary, Plugin Architecture, release and version material, and this Track accurately describe the delivered OAuth contract, exclusions, compatibility behavior, and version impact.
- [ ] A14) [P1] [P2] [P3] [P4] The complete final identity and version-impact decision is approved before implementation, including an approved reason for every relevant dimension left unchanged.
- [ ] A15) [P2] MyMCP does not answer `/.well-known/oauth-authorization-server`, `/.well-known/openid-configuration`, or `/register` as an authorization server; clients discover or invoke those capabilities at the configured external authorization server.
- [ ] A16) [P2] Enabling OAuth requires anonymous access to be disabled; every evidence-free `/mcp` request therefore receives the OAuth Bearer discovery challenge rather than an anonymous principal.

Why now / impact
- TRACK_043 delivered the first registered-principal adapter through `operator-bearer-v1`. The Phase 4 roadmap identifies an external OAuth adapter as the next identity path. This Track scopes OAuth resource-server access-token validation without moving OAuth behavior into MCP, Governance, plugins, or Mnemosyne.

Scope
- In scope:
  - One configured external OAuth authorization server per MyMCP process.
  - One host-owned production OAuth Authentication adapter selected through strict host startup configuration.
  - OAuth resource-server validation of access tokens supplied by the MCP client.
  - An approved OAuth protected-resource validation profile.
  - RFC 9068-style RS256 JWT access-token validation using one immutable startup JWKS snapshot and the narrowly isolated `PyJWT[crypto]` dependency.
  - Bounded RFC 8414 authorization-server metadata and JWKS retrieval, protected-resource metadata, exact resource/audience validation, startup outage, restart-based key rotation, and expiry-bound revocation contracts.
  - RFC 9728 protected-resource metadata for the `/mcp` resource and a `WWW-Authenticate: Bearer` challenge with `resource_metadata` on OAuth-protected `/mcp` HTTP 401 responses.
  - Stable subject derivation compatible with Authentication contract v1.
  - Exact evidence routing with strict schema-5 co-declaration exclusion between OAuth and `operator-bearer-v1`, plus mandatory disabled anonymous access for enabled OAuth.
  - Restart-based configuration and approved OAuth validation-state lifecycle.
  - Focused automated tests, required documentation, version governance, packaging and boundary checks, direct MCP validation, and optional approved supplementary provider validation.
- Out of scope:
  - More than one external OAuth authorization server per process.
  - OAuth client behavior by MyMCP, including browser login, redirects, callbacks, authorization-code processing, refresh tokens, token exchange, token issuance, client registration, or authorization-server administration.
  - ID-token validation or treating an ID token as an OAuth access token.
  - Authorization-server metadata endpoints, OpenID Provider metadata endpoints, dynamic client registration, or `/register` behavior hosted by MyMCP; those belong to the configured external authorization server.
  - OAuth access tokens, refresh tokens, client secrets, private keys, credentials, or secret values in Git, host TOML, durable memory, logs, errors, or MCP-visible data.
  - Sessions, Governance or ACL policy, OAuth-scope-to-Tool policy, filtered discovery or dispatch, Tool authorization, exact-call approval, security audit, broad remote deployment, or multi-user operation.
  - New MCP methods or Tools, plugin contracts, plugin composition semantics, Mnemosyne behavior, capability contracts, plugin data, or memory record schemas.
  - Generic Authentication-adapter discovery or loading, host-managed installation, dependency-environment management, hot activation, hot configuration reload, provider isolation, or runtime lifecycle management.
  - Resolving the listed OAuth implementation questions by implementation before S1 completes the DRAFT design review.

Milestones
- [ ] M1) Complete DRAFT OAuth design review: resolve the protected-resource profile, configuration, token validation, metadata, resource validation, routing, lifecycle, testing, documentation, and version-impact questions.
- [ ] M2) Activate only after every required OAuth public-contract, bearer-method selection, dependency, and version-impact decision is recorded.
- [ ] M3) Implement the approved pure OAuth adapter and validation behavior through coherent TDD chunks.
- [ ] M4) Implement approved configuration, production composition, and thin HTTP integration through coherent TDD chunks.
- [ ] M5) Complete documentation, full validation, direct MCP checks, optional approved OAuth interoperability evidence, acceptance review, and roadmap reconciliation.

Risks / decisions
- Risk: OAuth access tokens and `operator-bearer-v1` credentials both arrive through the same exact Authorization Bearer route; schema 5 must reject co-declaration rather than introduce token-shape inference, adapter order, or sequential validation.
- Risk: Selecting an OAuth protected-resource validation profile without explicit issuer, resource, authorization-server metadata, token-validation, and subject rules could admit tokens not intended for MyMCP.
- Risk: JWT validation, token introspection, authorization-server metadata, validation-material retrieval, cache expiry, outage handling, key rotation, and revocation impose materially different network, dependency, availability, and security boundaries.
- Risk: Remote OAuth validation dependencies can conflict with local-first startup determinism, restart-based configuration, loopback operation, and fail-closed authentication.
- Risk: Access tokens, claims, validation material, responses, metadata, and exceptions can leak sensitive information unless every representation and failure boundary remains bounded.
- Risk: A strict host-configuration change and the new protected-resource metadata route and Bearer challenge affect public compatibility and require explicit schema, endpoint, and version decisions.
- Risk: New OAuth dependencies enlarge the supply-chain and packaging surface; dependency choice must be explicit and testable.
- Risk: OAuth over literal loopback HTTP does not provide TLS confidentiality against hostile local software; this approved exception is limited to the current machine-local endpoint and must not be presented as a remote or HTTPS-equivalent deployment.
- Decision: This Track consumes Authentication contract v1, exact routing, normalized principals, schema 4, and `operator-bearer-v1` from TRACK_042 and TRACK_043.
- Decision: MyMCP is an OAuth resource server. The MCP client obtains the access token and presents it to MyMCP.
- Decision: One external OAuth authorization server is the process-wide maximum for this adapter.
- Decision: Configuration is restart-based.
- Decision: OAuth and `operator-bearer-v1` are alternative process configurations and cannot be co-declared in one schema-5 document, including disabled declarations, because current strict configuration requires unique declared routes. Either method may be selected alone; switching requires configuration replacement and restart.
- Decision: An enabled OAuth adapter requires `anonymous_enabled=false`. Evidence-free requests receive the OAuth Bearer discovery challenge; failed submitted evidence never becomes anonymous.
- Decision: MyMCP will implement RFC 9728 protected-resource metadata for its `/mcp` resource and will identify it from OAuth-protected `/mcp` HTTP 401 responses through the `resource_metadata` parameter of a `WWW-Authenticate: Bearer` challenge.
- Decision: MyMCP will advertise exactly the one configured external OAuth authorization server. It will not act as that authorization server and will not host `/.well-known/oauth-authorization-server`, `/.well-known/openid-configuration`, or `/register` for it.
- Decision: Local deterministic fixtures and controlled doubles are the primary test approach. Any live authorization-server validation is supplementary, separately approved, and credential-free in Git.
- Decision: The adapter profile is `oauth-jwt-jwks-v1`: RFC 9068-style compact JWT access tokens, exact `typ=at+jwt`, asymmetric RS256 only, one configured issuer, one exact MyMCP audience, and offline signature verification against one immutable startup JWKS snapshot. Opaque tokens, introspection, ID tokens, JWE, nested JWTs, unsigned tokens, HMAC, and other algorithms are unsupported.
- Decision: Add `PyJWT[crypto]>=2.13.0,<3.0` as the only new direct runtime dependency; its current crypto extra induces `cryptography>=3.4.0`. Third-party imports are confined to the concrete OAuth adapter package; Authentication contracts and routing remain standard-library-only. MyMCP owns bounded metadata/JWKS retrieval, strict parsing, key selection, snapshot lifecycle, and redaction rather than delegating those policies to `PyJWKClient`. The scoped Authentication guidance must be updated with this narrow exception in the implementation documentation chunk.
- Decision: Configuration supplies one exact canonical HTTPS issuer URI using a lowercase DNS hostname, optional non-root path, no query, fragment, userinfo, IP literal, localhost name, non-default port, percent-encoding, dot segment, or trailing slash. Root issuer `https://host` derives `https://host/.well-known/oauth-authorization-server`; path issuer `https://host/path` derives `https://host/.well-known/oauth-authorization-server/path`. Enabled OAuth startup fetches that document and its declared HTTPS `jwks_uri` exactly once, with certificate and hostname validation, no redirects, bounded timeout and bodies, strict UTF-8/JSON and duplicate-key rejection, byte-for-byte metadata issuer equality, and bounded key count. Startup fails closed before runtime publication on any retrieval or validation failure.
- Decision: The authorization-server metadata body is at most 16 KiB; JWKS is at most 64 KiB and 16 keys. Unknown metadata members are ignored for interoperability. Only `issuer` and `jwks_uri` are consumed. `jwks_uri` must use the same HTTPS origin and default port as the configured issuer and contain no userinfo or fragment; no token-controlled URL is ever fetched.
- Decision: The canonical OAuth resource identifier is derived only from validated loopback server address and port as `http://<IPv4>:<port>/mcp` or `http://[<compressed-IPv6>]:<port>/mcp`. Request Host and forwarded headers never influence it. JWT `aud` must contain that exact string; no origin-only, wildcard, prefix, or normalized-equivalent audience is accepted.
- Decision: A valid token has exactly three compact JWS segments, duplicate-free JSON object header and payload, `alg=RS256`, `typ=at+jwt`, one bounded nonblank ASCII `kid`, a unique suitable RSA signing JWK, exact configured `iss`, exact resource audience membership, and valid bounded `sub`, `exp`, `iat`, `client_id`, and `jti`; optional `nbf` is enforced. Clock skew is 30 seconds, future `iat` is bounded by that skew, and `exp - iat` is at most five minutes.
- Decision: The adapter-local subject is `oauth-jwt-v1:` plus unpadded base64url SHA-256 of exact UTF-8 issuer, one zero byte, and exact UTF-8 `sub`. The raw `sub` must first satisfy Authentication-v1 subject validity. The derived value changes with issuer or subject and prevents raw identity claims from reaching downstream layers.
- Decision: Metadata and JWKS are fetched only during enabled startup and retained immutably. A running process does not refresh keys, use stale fallback, or call the authorization server. Normal rotation requires overlapping old and new keys followed by restart. There is no immediate token revocation: a valid token may remain accepted through its maximum five-minute lifetime, and key removal is observed only after restart.
- Decision: Protected-resource metadata contains exactly `resource`, one-element `authorization_servers`, and `bearer_methods_supported=["header"]`; it omits scopes because Governance does not exist. It is served as JSON with `Cache-Control: no-store` only at `/.well-known/oauth-protected-resource/mcp`.
- Decision: When OAuth is enabled, every `/mcp` Authentication failure remains body-free HTTP 401 and carries exactly `WWW-Authenticate: Bearer resource_metadata="<derived metadata URL>"`, without error, description, scope, or token-derived distinction. Operator-bearer and anonymous-only configurations retain the existing challenge-free empty 401.
- Decision: The current literal loopback HTTP endpoint is an approved local interoperability exception and deliberate deviation from OAuth/RFC 9728 HTTPS transport requirements. OAuth configuration remains restricted to a loopback-derived resource; metadata/challenge shape follows the standards, but this deployment is not RFC-conformant and MyMCP claims no TLS equivalence or support for non-loopback, proxied, or remote OAuth endpoints. A standards-compliant HTTPS deployment boundary requires a separate Track.
- Decision: Host configuration schema 5 preserves schemas 1-4 and adds exact optional `[authentication.oauth_jwt]` with only non-secret `issuer`. The table is required whenever `oauth-jwt-jwks-v1` is declared, including disabled, and prohibited otherwise. Resource, metadata path, JWKS URI, token, client ID, secrets, algorithms, cache settings, and provider-specific values are not configurable.
- Decision: Stable bounded OAuth failures distinguish only configuration invalidity, metadata unavailable/invalid, JWKS unavailable/invalid, route invalidity, and bearer-method conflict. Logs and errors contain no issuer, URI, key ID, claim, response content, token, exception, or traceback.
- Decision: Activation authorizes only approved TDD chunks. Roadmap mutation, commit, push, tag, release publication, authorization-server account creation, networked provider setup, dependency installation, and credential use remain separately approval-gated.
- Version impact: Approved S1 decision. This Track advances MyMCP distribution/package/server marker from `0.6.0` to `0.7.0`, adds host configuration schema 5, and adds stable adapter/profile identity `oauth-jwt-jwks-v1` because it delivers a new production OAuth method, public RFC 9728 route, and Bearer challenge. Schemas 1-4 remain supported and unchanged.
  - MCP protocol version and negotiation: unchanged because OAuth is upstream HTTP Authentication behavior and adds no MCP method, message, Tool, result, or error contract.
  - Endpoint identity and existing `/mcp`, `/health`, and `/version` routes: unchanged except `/version` reports 0.7.0 and OAuth-selected `/mcp` failures add the approved challenge. One new public GET route `/.well-known/oauth-protected-resource/mcp` is added only for OAuth protected-resource metadata.
  - HTTP authentication failure contract: body-free HTTP 401 remains; OAuth-selected failures add exactly the approved Bearer challenge, while operator-bearer and anonymous-only behavior remains challenge-free.
  - FastAPI application identity: unchanged because the application remains MyMCP and route assembly remains host-owned.
  - Host plugin API: unchanged at 1 because OAuth Authentication is outside the Tools-only plugin API.
  - Manifest schema: unchanged at 1 because no plugin declaration changes.
  - External plugin-author contract: unchanged at `mymcp_plugin_v1` because no plugin-author behavior changes.
  - Worker protocol: unchanged and absent because no worker, sandbox, or lifecycle protocol is introduced.
  - Host configuration schema: adds schema 5 with exact OAuth issuer intent; schemas 1-4 and absent-file behavior remain accepted and unchanged.
  - Authentication contract: remains 1 because principal, evidence, request context, adapter result, exact routing, anonymous admission, and canonical-principal construction are unchanged.
  - Authentication adapter and validation-profile identity: new `oauth-jwt-jwks-v1`. RFC 8414 metadata, RFC 7517 JWKS, and RFC 9068-style token inputs use their standards identities; no separate persisted metadata, JWKS, cache, or source-file format is introduced.
  - `operator-bearer-v1` and verifier-source format 1: unchanged. OAuth and operator-bearer remain independently selectable across separate configurations, but schema 5 rejects co-declaration because both claim the same exact Authorization Bearer route.
  - Plugin identities and versions: unchanged, including bundled Mnemosyne `0.3.0`, because no plugin behavior changes.
  - Capability kinds and local IDs, capability contract versions, endpoint-visible Tool bindings, and the Tool-definition digest ledger: unchanged because no Tool contract changes.
  - Plugin configuration schemas and plugin-data schemas: unchanged because OAuth configuration is host-owned.
  - Mnemosyne configuration, storage, logging, lifecycle, and memory-record schemas 1 and 2: unchanged because OAuth does not change Mnemosyne-domain behavior.
  - Governance policy revision: unchanged and absent because this Track establishes identity only.
  - Runtime-generation semantics: unchanged because Authentication composition remains before plugin-runtime publication and OAuth state is not part of the plugin runtime generation.
  - Tracked official client connection and agent identity, `mymcp` connection key, and `mymcp_*` permission-prefix policy: unchanged because this Track changes no tracked client configuration or Tool surface.
  - Documentation and release notes: must describe MyMCP 0.7.0, schema 5, `oauth-jwt-jwks-v1`, RFC 9728 metadata, Bearer challenge, PyJWT dependency, startup remote dependency, five-minute revocation bound, loopback-HTTP exception, and unchanged downstream contracts.

Open questions
- [x] Q1) Implement the bounded `oauth-jwt-jwks-v1` OAuth resource-server profile using RFC 9728, RFC 8414, RFC 7517, RFC 9068-style access tokens, RFC 8707 exact resource binding, and JWT best-current-practice validation.
- [x] Q2) Accept only self-contained RS256 JWT access tokens and use `PyJWT[crypto]` in the concrete adapter package; do not implement opaque tokens, introspection, provider SDKs, or fallback validation.
- [x] Q3) Configure one exact HTTPS issuer; enabled startup retrieves bounded RFC 8414 metadata and its HTTPS JWKS once with certificate validation, no redirects, strict parsing, exact issuer equality, and fail-closed publication.
- [x] Q4) Derive the exact loopback HTTP `/mcp` resource identifier from validated server address and port and require exact JWT audience membership; never derive identity from request headers.
- [x] Q5) Require the approved compact RS256 `at+jwt` form, unique suitable keyed RSA verification, exact issuer/audience, bounded `sub`, `exp`, `iat`, `client_id`, and `jti`, optional enforced `nbf`, 30-second skew, and five-minute maximum lifetime.
- [x] Q6) Derive the bounded adapter-local subject as `oauth-jwt-v1:<base64url-sha256(issuer || NUL || sub)>` after validating the raw subject; expose no raw claim downstream.
- [x] Q7) Fetch metadata/JWKS only during enabled startup, retain one immutable bounded snapshot, perform no runtime refresh or stale fallback, and require overlapping keys plus restart for rotation.
- [x] Q8) Claim no immediate revocation. Valid tokens remain usable until expiry within the five-minute maximum; key removal is observed only after restart.
- [x] Q9) Publish exact RFC 9728 metadata only at `/.well-known/oauth-protected-resource/mcp`, with exact resource, one authorization server, header bearer method, no scopes, and `no-store`; OAuth failures use a body-free Bearer challenge with only `resource_metadata`. Literal loopback HTTP is an explicit local exception, not remote/TLS support.
- [x] Q10) Add adapter/profile `oauth-jwt-jwks-v1` and schema 5 exact `[authentication.oauth_jwt] issuer`; retain schemas 1-4, require disabled anonymous access for enabled OAuth, and use only bounded content-free OAuth startup failures.
- [x] Q11) OAuth and `operator-bearer-v1` are alternative process configurations and cannot be co-declared in one schema-5 document because both claim the unchanged exact Authorization Bearer route. Switching requires configuration replacement and restart.
- [x] Q12) Use runtime-generated ephemeral RSA keys, injected clocks, bounded fetch doubles, and non-secret synthetic tokens; cover every validation, retrieval, rotation, redaction, route, compatibility, IPv4/IPv6 resource, and no-refresh boundary without committed usable credentials.
- [x] Q13) Live-provider interoperability is supplementary, not an acceptance prerequisite, and requires separate approval for network/account/credential actions. Retain only provider-independent pass/fail behavior and redaction evidence, never provider or account identifiers, URLs, tokens, claims, keys, or response bodies.
- [x] Q14) Release MyMCP/package/server 0.7.0 with configuration schema 5 and adapter/profile `oauth-jwt-jwks-v1`; retain Authentication contract 1 and every listed MCP, plugin, capability, data, runtime, and Mnemosyne identity.

Decision log
- Decision (roadmap): This is Phase 4 Track 3 following TRACK_042 and TRACK_043; the living roadmap identifies an external OAuth adapter as NEXT.
- Decision (user: authorization-server count): Exactly one external OAuth authorization server may be configured per MyMCP process.
- Decision (user: lifecycle): OAuth configuration is restart-based.
- Decision (user: client responsibility): The MCP client obtains and presents the OAuth access token; MyMCP does not obtain tokens for the client.
- Decision (user: server responsibility): MyMCP is an OAuth resource server and validates supplied OAuth access tokens.
- Decision (user: discovery): MyMCP publishes OAuth protected-resource metadata for `/mcp` and returns its URL in a `WWW-Authenticate: Bearer` challenge. Authorization-server discovery endpoints and dynamic client registration remain on the configured external authorization server, not MyMCP.
- Decision (user: verification): Deterministic local doubles for OAuth metadata, validation material, and tokens are the primary automated-test strategy. A real authorization-server interoperability check is supplementary only if feasible, separately approved, and never places credentials in Git.
- Decision (routing): OAuth and `operator-bearer-v1` cannot be co-declared in schema 5. Either method alone uses the unchanged exact Authorization Bearer route; OAuth token shape never selects an adapter, and enabled OAuth requires anonymous access disabled.
- Decision (boundaries): Authentication remains host-owned and transport-neutral. HTTP remains thin. MCP, Governance, plugins, plugin data, and Mnemosyne do not parse or receive OAuth tokens, claims, or validation material.
- Decision (versioning): MyMCP/package/server advances to 0.7.0; host configuration adds schema 5; Authentication contract remains 1; the new adapter/profile is `oauth-jwt-jwks-v1`; every unchanged identity and rationale is recorded in the approved version-impact decision above.
- Decision (S1 design): The user approved the complete `oauth-jwt-jwks-v1` direction: PyJWT-backed RS256 JWT validation, bounded startup RFC 8414/JWKS acquisition, exact loopback resource audience, five-minute expiry-bound revocation, immutable restart-based key state, schema 5, MyMCP 0.7.0, no OAuth authorization scopes, and the explicit loopback-HTTP interoperability exception.
- Decision (activation): No implementation, implementation-driving tests, configuration edits, dependency installation, authorization-server interaction, durable-memory mutation, roadmap mutation, commit, push, tag, release, or credential handling is authorized while this Track is DRAFT.

Plan (execution steps)
- [x] S1) Completed DRAFT OAuth design review without implementation: inspected the linked roadmap, current source, tests, MCP Authorization 2025-11-25, and applicable RFCs; resolved Q1-Q14; approved the `oauth-jwt-jwks-v1` profile, PyJWT dependency boundary, startup metadata/JWKS snapshot, exact resource and claims, expiry-bound revocation, metadata/challenge behavior, bearer-method exclusion, schema 5, MyMCP 0.7.0, deterministic tests, loopback-HTTP exception, and final version impact; replaced provisional steps with exact TDD chunks.
- [ ] S2) After explicit user approval and only after S1 is complete, move TRACK_044 to ACTIVE by synchronizing folder, filename, title, and Current path. Check this step before implementation or implementation-driving tests.
- [ ] S3) Before implementation-driving tests, update `mymcp/authentication/AGENTS.md` under explicit approval to permit only `PyJWT`/`cryptography` imports inside the concrete OAuth adapter package while keeping contracts, router, and other Authentication modules standard-library-only; then add focused failing tests for compact duplicate-free RS256 `at+jwt` parsing, strict header/key/claim/time/audience checks, five-minute lifetime, hashed issuer-subject projection, bounded failures, redaction, and dependency boundaries; add the smallest PyJWT-backed pure adapter implementation; refactor, validate, and update this Track.
- [ ] S4) TDD chunk 2 - add focused failing tests for bounded no-redirect HTTPS RFC 8414 metadata and JWKS acquisition, strict parsing, issuer/JWKS validation, size/key limits, immutable startup snapshot, outage failure, no runtime refresh, and restart-based rotation; add the smallest injected-fetch snapshot loader; refactor, validate, and update this Track.
- [ ] S5) TDD chunk 3 - add focused failing tests for exact schema-5 OAuth parsing, issuer canonicalization rejection, schemas 1-4 compatibility, OAuth/operator co-declaration rejection, mandatory disabled anonymous access, server-derived resource identity, bounded failures, startup snapshot loading, and composition before plugin-runtime publication; add the smallest configuration and host-composition implementation; refactor, validate, and update this Track.
- [ ] S6) TDD chunk 4 - add focused failing tests for thin GET and POST OAuth evidence extraction, body-free pre-MCP 401 with the exact Bearer challenge, the single RFC 9728-shaped protected-resource metadata route and no-store response, loopback IPv4/IPv6 identifiers, challenge-free operator/anonymous compatibility, and absence of MyMCP authorization-server discovery or registration routes; add the smallest route/application implementation; refactor, validate, and update this Track.
- [ ] S7) TDD chunk 5 - update MyMCP/package/server to 0.7.0, dependency and version guards, README, Authentication, Configuration, Architecture, Glossary, Plugin Architecture, tests guide, and release notes; run focused/full/package/import/version checks, direct OAuth/operator-bearer/anonymous MCP checks, optional separately approved interoperability, independent acceptance review, and roadmap reconciliation.
- [ ] S8) Complete the Track only after every acceptance criterion passes, the roadmap reconciliation outcome is recorded, and status, path, and title transition are synchronized.

Current inventory
- TRACK_042 delivered Authentication contract v1, exact immutable evidence routing, normalized principals, configured anonymous admission, schema 3, and the principal-aware MCP application seam.
- TRACK_043 delivered MyMCP/package/server `0.6.0`, host configuration schema 4, `operator-bearer-v1`, verifier-source format 1, strict bearer extraction, and empty pre-MCP HTTP 401 behavior.
- `mymcp/authentication/contracts.py` owns transport-neutral Authentication-v1 contracts, bounded evidence, adapter results, and normalized principal construction constraints.
- `mymcp/authentication/router.py` routes one host-derived evidence descriptor to exactly one registration and has no fallback.
- `mymcp/authentication/adapters/` contains the concrete host-owned Authentication-method implementation boundary; `operator_bearer.py` is the current production adapter.
- `mymcp/host/configuration.py` owns strict schemas 1-4 and immutable startup snapshots.
- `mymcp/host/authentication.py` composes production Authentication before plugin-runtime publication.
- `mymcp/routes/mcp.py` owns bounded Authorization extraction and empty-401 transport mapping for both `/mcp` methods.
- `docs/AUTHENTICATION.md` defers external OAuth and requires an explicit architecture and Track decision.
- `docs/CONFIGURATION.md`, `docs/ARCHITECTURE.md`, `docs/PLUGIN_ARCHITECTURE.md`, and `docs/GLOSSARY.md` define current configuration, ownership, and identity and version baselines.
- `pyproject.toml` and `mymcp/settings.py` identify the current public host, package, and server as `0.6.0`.
- Existing Authentication, host-configuration, route, application, bootstrap, import-boundary, package and version, plugin, capability-ledger, and Mnemosyne tests provide the compatibility baseline.

Artifacts
- Authentication architecture: `docs/AUTHENTICATION.md`.
- Host configuration contract: `docs/CONFIGURATION.md`.
- Current architecture: `docs/ARCHITECTURE.md`.
- Identity and version model and Phase 4: `docs/PLUGIN_ARCHITECTURE.md`.
- Workflow and governance: `docs/AI_WORKFLOW.md`, `.backlog/README.md`, `.backlog/PORE.md`, root `AGENTS.md`, `.backlog/AGENTS.md`, and `mymcp/authentication/AGENTS.md`.
- Delivered prerequisites:
  - `.backlog/COMPLETED/2026/TRACK_042_COMPLETED_authentication_routing_and_principal_foundation.md`
  - `.backlog/COMPLETED/2026/TRACK_043_COMPLETED_operator_provisioned_bearer_credential_authentication_adapter.md`
- Living roadmap memory references: `project/mymcp/roadmaps`; canonical index `mem_5f3b5f4871d0406995f222d48e0357b7`; Phase 4 section `mem_ec6d4b50c830463383ad0d1e221910c7`. S1 must freshly inspect the complete collection, canonical index, current delivered baseline, Phase 4 section, and roadmap rules before implementation planning or reconciliation.

Completion notes
- DRAFT rewrite records the OAuth resource-server problem, exact user-approved scope, bounded exclusions, complete approved identity and version assessment, resolved OAuth design questions, and approval-gated execution plan.
- The prior generic external-authorization-server framing was replaced in full because it incorrectly treated OAuth as an unresolved alternative rather than this Track's fixed implementation scope.
- DRAFT refinement makes RFC 9728 protected-resource metadata and a `WWW-Authenticate: Bearer` challenge mandatory for OAuth client discovery, while keeping authorization-server metadata and registration outside MyMCP.
- User-approved routing refinement makes OAuth and `operator-bearer-v1` alternative process configurations: at most one may be enabled, and switching requires configuration change and restart.
- S1 design review completed under user approval with no implementation: it resolves the full OAuth validation, configuration, discovery, key lifecycle, resource identity, challenge, dependency, testing, and version contracts and records five exact TDD chunks. The Track remains DRAFT pending separate activation approval.
- No implementation, implementation-driving test, production, configuration, documentation, dependency, authorization-server, durable-memory, roadmap, Git-history, release, or credential state changes are authorized by this DRAFT.
- Before completion, inspect the linked living roadmap and record whether it was revised under separate user approval, has a revision proposal pending, or remains current.

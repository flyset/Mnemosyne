# TRACK 044 [COMPLETED]: OAuth validation foundation

Track
- ID: TRACK_044
- Repository: MyMCP
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_044_COMPLETED_oauth_validation_foundation.md

Problems (PORE)
- P1: As a MyMCP maintainer, I cannot safely add an external OAuth Authentication method because MyMCP has no bounded validator for externally issued access tokens or immutable authorization-server validation material.
- P2: As a MyMCP operator, I need OAuth validation material acquired safely and fixed for one process start, because runtime discovery, refresh, or fallback would weaken deterministic fail-closed startup.
- P3: As a MyMCP user, I need token, claim, key, provider-response, and exception data contained at the Authentication boundary, because identity evidence must never reach MCP, Governance, plugins, logs, errors, or durable memory.

Objective
- Deliver a host-owned, transport-neutral `oauth-jwt-jwks-v1` validation foundation that acquires one bounded immutable startup snapshot and maps a valid externally issued access token to one opaque adapter-local subject, without configuring or publicly exposing OAuth Authentication.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- This Track produces no enabled production Authentication route, host-configuration schema, HTTP metadata endpoint, Bearer challenge, MCP behavior, or public OAuth deployment.
- MyMCP remains an OAuth resource server only. Client login, token acquisition, refresh, issuance, exchange, registration, and authorization-server administration are out of scope.
- Authentication remains transport-neutral and must not import FastAPI, routes, MCP, Governance, plugin contracts, plugins, or host configuration.
- Third-party imports are permitted only inside the concrete OAuth adapter package. Authentication contracts and routing remain standard-library-only.
- Validation uses one configured external authorization server, one exact resource audience supplied by the future host integration, and one immutable startup snapshot.
- Never expose access tokens, Authorization values, claims, keys, issuer or JWKS URIs, provider responses, exception details, or tracebacks.
- Preserve local-first, single-user, least-privilege, exact-routing, normalized-principal, and restart-based assumptions.
- Deterministic local fixtures, generated ephemeral RSA keys, injected clocks, and bounded fetch doubles are the automated-test method. No live provider, account, credential, or network action is part of this Track.

Acceptance criteria
- [x] A1) [P1] A pure `oauth-jwt-jwks-v1` adapter validates only the approved compact RS256 `at+jwt` access-token profile and returns only a bounded stable adapter-local subject or bounded failure.
- [x] A2) [P1] Validation requires exact issuer and audience, unique suitable keyed RSA verification, required bounded claims, a 30-second skew, and a maximum five-minute token lifetime; unsupported, malformed, ambiguous, wrongly issued, wrongly targeted, or expired tokens fail closed.
- [x] A3) [P1] The adapter-local subject is `oauth-jwt-v1:` plus unpadded base64url SHA-256 of exact UTF-8 issuer, one zero byte, and exact UTF-8 `sub`; raw identity claims do not cross the adapter boundary.
- [x] A4) [P2] A bounded no-redirect HTTPS loader retrieves strict RFC 8414 metadata and its same-origin JWKS exactly once, validates all approved URI/body/key constraints, and returns one immutable snapshot.
- [x] A5) [P2] The running validator performs no metadata refresh, JWKS refresh, introspection, stale fallback, or provider call. Rotation and key removal become visible only after restart.
- [x] A6) [P3] Tests prove sensitive values are absent from representations, failures, logs, downstream results, and durable state.
- [x] A6a) [P3] Documentation and test examples contain no usable token, credential, private key, provider response, secret-bearing URL, or real provider/account identifier.
- [x] A7) [P1] [P2] The narrowly isolated `PyJWT[crypto]>=2.13.0,<3.0` dependency and import-boundary exception are explicit, packaged, and guarded.
- [x] A8) [P1] Existing Authentication contract v1, router, principals, `operator-bearer-v1`, host configuration schemas 1-4, MCP, plugins, and Mnemosyne behavior remain unchanged.
- [x] A9) [P1] [P2] [P3] Focused tests, full suite, import-boundary checks, package checks, and independent review pass.
- [x] A10) [P1] [P2] [P3] Documentation accurately marks this foundation as dormant until TRACK_045 integrates it.

Why now / impact
- The original TRACK_044 combined cryptographic validation, a new network boundary, host configuration, HTTP discovery, and release integration. Splitting first isolates and reviews the security-critical validator before any public route can select it.

Scope
- In scope:
  - Compact duplicate-free RS256 `at+jwt` parsing and validation.
  - Exact issuer/resource audience, claim, time, key-suitability, and subject-projection rules.
  - Bounded RFC 8414 metadata and RFC 7517 JWKS retrieval over validated HTTPS.
  - One immutable startup validation snapshot, deterministic fetch seam, and restart-based rotation boundary.
  - `PyJWT[crypto]` dependency isolation, redaction, tests, and foundation documentation.
- Out of scope:
  - Host configuration schema 5, production adapter registration, startup composition, route selection, protected-resource metadata, Bearer challenges, and version 0.7.0 delivery; TRACK_045 owns these.
  - OAuth client behavior, opaque-token introspection, ID tokens, JWE, nested JWTs, HMAC, token refresh, runtime key refresh, immediate revocation, scopes, Governance, sessions, authorization, approval, audit, or multi-user operation.
  - Live authorization-server interoperability or credential use.

Milestones
- [x] M1) Activate the approved validation-only scope.
- [x] M2) Deliver and review pure token validation.
- [x] M3) Deliver and review bounded immutable validation-material loading.
- [x] M4) Complete compatibility, packaging, documentation, and acceptance evidence without public activation.

Risks / decisions
- Risk: JWT validation has many ambiguous or unsafe forms; the accepted profile must remain narrow and exact.
- Risk: Metadata/JWKS retrieval introduces a remote startup dependency into a local-first host; bounds and fail-closed behavior are mandatory.
- Risk: A dormant production module could be mistaken for an enabled feature; documentation and composition tests must prove it is unreachable.
- Decision: The profile is `oauth-jwt-jwks-v1`: compact JWT, exact `typ=at+jwt`, RS256 only, exact issuer, exact resource audience membership, and offline verification against one immutable startup JWKS snapshot.
- Decision: Tokens require exactly three compact JWS segments, duplicate-free JSON objects, bounded nonblank ASCII `kid`, a unique suitable RSA signing JWK, and bounded `sub`, `exp`, `iat`, `client_id`, and `jti`; optional `nbf` is enforced.
- Decision: Clock skew is 30 seconds, future `iat` is bounded by that skew, and `exp - iat` is at most five minutes.
- Decision: Opaque, encrypted, nested, ID, unsigned, symmetric, and other-algorithm tokens are unsupported.
- Decision: Add `PyJWT[crypto]>=2.13.0,<3.0` as the only direct runtime dependency; MyMCP owns strict parsing, key selection, lifecycle, bounds, and redaction rather than using `PyJWKClient` policy.
- Decision: The configured issuer is one canonical HTTPS URI with lowercase DNS hostname, optional non-root path, and no query, fragment, userinfo, IP literal, localhost, non-default port, percent encoding, dot segment, or trailing slash.
- Decision: Startup derives and fetches RFC 8414 metadata, then its declared same-origin HTTPS `jwks_uri`, exactly once with certificate and hostname validation, no redirects, bounded time and body, strict UTF-8/JSON, duplicate-key rejection, exact metadata issuer equality, and at most 16 keys.
- Decision: Metadata is at most 16 KiB; JWKS is at most 64 KiB. Unknown metadata members are ignored; only `issuer` and `jwks_uri` are consumed. No token-controlled URL is fetched.
- Decision: Rotation requires overlapping keys and restart. There is no immediate revocation claim; a valid token may remain accepted until expiry within five minutes, and key removal is observed only after restart.
- Decision: TRACK_045 alone will derive the loopback resource URI, configure and register this adapter, expose OAuth metadata/challenges, and release MyMCP 0.7.0.
- Version impact: This foundation changes packaged implementation and adds a runtime dependency but is not independently released or endpoint-reachable. MyMCP/package/server remains `0.6.0` until TRACK_045 completes the single 0.7.0 release train.
  - MCP protocol, endpoints, HTTP failure behavior, FastAPI identity, host plugin API, manifest schema, external plugin-author contract, worker protocol, host configuration schemas 1-4, Authentication contract 1, `operator-bearer-v1`, plugin/capability/data/runtime identities, Mnemosyne schemas, and Governance policy remain unchanged because no production route or composition selects the foundation.
  - New internal stable adapter/profile identity: `oauth-jwt-jwks-v1`.
  - Packaging dependency metadata changes to include the approved isolated PyJWT dependency; package/version guards must explicitly allow this unreleased foundation state.

Open questions
- [x] Q1) Use the narrow `oauth-jwt-jwks-v1` RS256 JWT profile rather than opaque-token introspection or provider SDKs.
- [x] Q2) Acquire bounded metadata and JWKS once at startup and retain an immutable snapshot with no runtime provider calls.
- [x] Q3) Hash issuer and subject into an opaque adapter-local subject.
- [x] Q4) Keep the foundation dormant until TRACK_045 provides configuration, resource derivation, registration, and HTTP discovery.
- [x] Q5) Treat TRACK_044 and TRACK_045 as one 0.7.0 release train; do not publish this intermediate foundation independently.

Decision log
- Decision (split): The user approved splitting the original OAuth Track before activation because validation/loading and public host integration are distinct security and acceptance boundaries.
- Decision (roadmap): TRACK_044 remains Phase 4 Track 3a and TRACK_045 becomes Track 3b; together they deliver the roadmap's external OAuth adapter outcome.
- Decision (version impact): TRACK_044 adds the internal stable `oauth-jwt-jwks-v1` foundation and isolated `PyJWT[crypto]>=2.13.0,<3.0` packaging dependency but keeps MyMCP/package/server at 0.6.0 because no production route or composition selects it. MCP protocol, endpoints, HTTP failures, FastAPI identity, host plugin API 1, manifest schema 1, external plugin-author contract, absent worker protocol, host configuration schemas 1-4, Authentication contract 1, `operator-bearer-v1`, operator-bearer verifier-source format 1, plugin/capability/data/runtime identities, Mnemosyne schemas, and absent Governance policy remain unchanged and are guarded as listed under Risks / decisions.
- Decision (activation): The user explicitly activated TRACK_044 and separately approved S3. Network action, memory mutation, commit, push, tag, and release remain unauthorized.

Plan (execution steps)
- [x] S1) Complete the DRAFT split and validation-foundation design review; preserve the approved profile while removing public host integration into TRACK_045.
- [x] S2) After explicit user approval, move TRACK_044 to ACTIVE by synchronizing folder, filename, title, and Current path. Check this step before implementation or implementation-driving tests.
- [x] S3) TDD chunk 1 — updated scoped Authentication guidance; added focused failing tests for compact duplicate-free RS256 `at+jwt` parsing, strict header/key/claim/time/audience validation, five-minute lifetime, opaque subject projection, bounded failures, redaction, and dependency boundaries; declared the isolated dependency and added the pure dormant adapter; hardened adversarial parsing and validation after independent review; refactored, validated, and updated this Track.
- [x] S4) TDD chunk 2 — added focused failing tests for bounded no-redirect HTTPS metadata/JWKS acquisition, strict parsing, issuer/JWKS validation, size/key limits, immutable snapshot, outage failure, no runtime refresh, and restart-based rotation; added the injected-fetch loader and concrete bounded HTTPS transport; hardened it after independent security review; refactored, validated, and updated this Track.
- [x] S5) Proved through focused composition/import tests that the foundation is not registered or endpoint-reachable; updated foundation documentation, ran focused/full/package/import checks and independent review, then updated this Track.
- [x] S6) Inspected the linked roadmap at completion and recorded that the split foundation does not yet change its delivered baseline or NEXT outcome; completed after every acceptance criterion passed and transitioned status/path/title together. No release or roadmap mutation was performed; TRACK_045 owns public delivery and final roadmap reconciliation.

Current inventory
- TRACK_042 delivered Authentication contract v1, exact routing, normalized principals, schema 3, and the principal-aware MCP application seam.
- TRACK_043 delivered MyMCP 0.6.0, schema 4, `operator-bearer-v1`, immutable verifier snapshots, strict Bearer extraction, and empty pre-MCP HTTP 401 behavior.
- `mymcp/authentication/contracts.py` and `router.py` own the standard-library-only contract and exact routing.
- `mymcp/authentication/adapters/operator_bearer.py` is the current concrete-adapter model.
- `mymcp/authentication/adapters/oauth_jwt.py` now owns the dormant pure `oauth-jwt-jwks-v1` validator, immutable key snapshot, strict issuer/profile validation, injected clock, and opaque subject projection.
- `mymcp/authentication/adapters/oauth_discovery.py` now owns dormant RFC 8414 metadata/JWKS acquisition, strict same-origin and JWK selection, bounded content-free failures, and a verified-TLS, proxy-disabled, no-redirect, deadline/body-bounded standard-library fetch implementation behind an injected test seam.
- `PyJWT[crypto]>=2.13.0,<3.0` is the sole new direct runtime dependency and is confined to the concrete OAuth module; ordinary Authentication/adapter package imports do not load it.
- No OAuth host configuration, production registration, route, challenge, or public deployment currently exists; the metadata/JWKS loader is packaged but dormant and unreachable from production composition.

Artifacts
- Authentication architecture: `docs/AUTHENTICATION.md`.
- Workflow: `docs/AI_WORKFLOW.md`, `.backlog/README.md`, `.backlog/PORE.md`, and applicable `AGENTS.md` files.
- Prerequisites: completed TRACK_042 and TRACK_043.
- Successor: `.backlog/DRAFT/2026/TRACK_045_DRAFT_oauth_authentication_host_integration.md`.
- Roadmap: `project/mymcp/roadmaps`, Phase 4 external OAuth outcome.

Completion notes
- The original TRACK_044 was split under explicit user approval before activation or implementation.
- This Track intentionally stops at a tested, packaged, unreachable foundation. TRACK_045 owns all public OAuth behavior and MyMCP 0.7.0.
- S3 red evidence: the first focused run failed at collection because `mymcp.authentication.adapters.oauth_jwt` did not exist; independent adversarial review then drove 23 additional failing cases covering bounded malformed input, signature-before-claims ordering, dormant imports, strict audience/issuer/base64 handling, and JSON-depth bounds; the numeric-DNS correction added 3 focused failing cases.
- S3 green evidence: 177 focused OAuth tests passed; 362 Authentication plus packaging tests passed; independent final S3 security review passed; `git diff --check` passed. The full suite reached 1,802 passed and 3 skipped with one unrelated pre-existing `tests/test_opencode_config.py` failure caused by local `opencode.json` credential-header/OAuth fields outside this Track's approved scope.
- S4 red evidence: the initial focused run failed at collection because the discovery module did not exist; independent review then drove failing cases for RFC 8414 path derivation, executable TLS/no-redirect/proxy/deadline/body bounds, canonical same-origin JWKS URIs, strict JSON, suitable-key filtering, base64urlUInt minimality, and `key_ops` handling.
- S4 green evidence: 293 focused OAuth validator/discovery tests passed; 478 Authentication plus packaging tests passed; independent final S4 security review passed; `git diff --check` passed. The full suite reached 1,918 passed and 3 skipped with the same unrelated pre-existing `tests/test_opencode_config.py` local-configuration failure.
- S5 added 23 focused dormancy guards proving ordinary imports/startup do not load OAuth/PyJWT, schemas remain 1-4, only `operator-bearer-v1` is registered, public routes and MCP Tools remain unchanged, and built packages contain the dormant modules/dependency without auto-registration. README, Architecture, Authentication, and Glossary now describe the dormant boundary.
- S5 final validation: 316 focused OAuth/dormancy tests passed; the complete suite passed with 1,942 tests and 3 platform skips; wheel and sdist builds passed and contained both dormant modules plus the bounded PyJWT dependency; `git diff --check` passed; independent acceptance review passed A1-A10. The stale OpenCode test was corrected to match the already-tracked safe credential-file reference and `oauth: false` configuration without reading credential content.
- Completion roadmap reconciliation: freshly inspected the canonical roadmap index, Phase 4 section, and delivered baseline. They remain current: the external OAuth adapter is still NEXT because TRACK_044 delivers only its dormant validation foundation, while TRACK_045 owns production integration and the complete roadmap outcome. No roadmap mutation was required or performed.
- TRACK_044 completed with all acceptance criteria, milestones, and plan steps satisfied. MyMCP remains 0.6.0; no release, commit, push, tag, public OAuth route, schema 5, or production OAuth registration was performed.

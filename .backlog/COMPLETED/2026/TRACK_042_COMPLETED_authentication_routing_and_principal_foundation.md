# TRACK 042 [COMPLETED]: Authentication routing and principal foundation

Track
- ID: TRACK_042
- Repository: MyMCP
- Branch: main
- Current path: .backlog/COMPLETED/2026/TRACK_042_COMPLETED_authentication_routing_and_principal_foundation.md

Problems (PORE)
- P1: As the MyMCP maintainer, I cannot add multiple authentication methods without coupling evidence parsing and fallback behavior to HTTP routes or MCP handling, because the host has no Authentication adapter and routing contracts.
- P2: As the MyMCP maintainer, I cannot give Governance stable collision-free ACL identities across authentication sources, because no normalized principal kind, adapter namespace, adapter-local subject, or canonical principal identity exists.
- P3: As the MyMCP operator, I cannot configure authentication adapters and anonymous access independently, because current anonymous access is an implicit absence of authentication rather than explicit startup intent.
- P4: As the Mnemosyne user, I need the Authentication foundation to preserve all current HTTP, MCP, plugin runtime, plugin, Tool, configuration, storage, record, and domain behavior.

Objective
- Establish the permanent host-owned Authentication adapter, evidence-routing, and namespaced-principal contracts; make anonymous access an explicit independent configuration choice; and preserve current behavior without implementing bearer, OAuth, MCP sessions, or Governance.

Non-negotiables
- All implementation follows TDD: a focused failing test, the smallest passing implementation, then refactoring and validation.
- Follow the documented layer order: HTTP server, Authentication, MCP server, Governance, Plugin runtime, Plugin, and Plugin data or external service.
- Authentication adapters are a separate host-owned security boundary, not Tool plugins or part of the Tools-only plugin-author contract.
- Host configuration enables zero or more named adapter instances and independently controls anonymous access. The immutable startup snapshot fixes both until restart.
- Submitted evidence routes unambiguously to exactly one enabled adapter. There is no sequential probing, adapter-order dependence, downgrade, or cross-adapter fallback.
- Invalid, malformed, ambiguous, unsupported, or rejected evidence never falls back to anonymous. Evidence-free requests become anonymous only when explicitly enabled.
- The host assigns stable adapter configuration identities and constructs canonical principal IDs. Clients and adapters cannot assert ACL namespaces.
- Registered principals expose normalized kind, adapter identity, adapter-local subject, and canonical prefixed identity. Anonymous exposes fixed kind/identity and null adapter/subject.
- No normalized principal contains credentials, tokens, headers, raw OAuth claims, certificates, secrets, executable module identity, or client-supplied method identity.
- The MCP server remains authentication-protocol-neutral; plugin layers receive no Authentication capability or credential context.
- Preserve current anonymous HTTP/MCP behavior and every existing plugin and Mnemosyne identity unless a separately approved public-contract decision explicitly changes it.
- Do not add bearer provisioning, OAuth, external authorization services, client sessions, Governance policy, exact-call approval, security audit, secret storage, remote trust, or plugin isolation.

Acceptance criteria
- [x] A1) [P1] Immutable host-owned adapter and result contracts accept only bounded method-specific evidence/context and return one validated adapter-local subject or one bounded failure.
- [x] A2) [P1] An immutable host-owned router classifies submitted evidence and invokes exactly one enabled adapter; ambiguous configuration or evidence fails closed without sequential attempts or fallback.
- [x] A3) [P1] Automated dependency tests prove Authentication remains independent of MCP Tools, plugin contracts/domains, route implementation, FastAPI behavior, and Governance policy beyond approved transport-neutral values.
- [x] A4) [P2] The normalized-principal contract contains exactly approved principal kind, nullable stable adapter identity, nullable adapter-local subject, and canonical host-constructed identity, with strict collision-free grammar and consistency rules.
- [x] A5) [P2] Governance-facing values preserve adapter namespace for ACLs without exposing credentials or protocol claims; downstream code cannot supply or rewrite canonical identity.
- [x] A6) [P3] MyMCP host configuration independently controls anonymous access and zero or more named adapters, validates bounded settings into the immutable startup snapshot, and requires restart for changes.
- [x] A7) [P3] Evidence-free requests produce exactly the fixed anonymous principal only when anonymous access is enabled; when disabled they fail before MCP handling.
- [x] A8) [P3] Invalid submitted evidence always fails before MCP handling even when anonymous access is enabled; tests prove no downgrade, fallback, or adapter-order behavior.
- [x] A9) [P4] Production configuration preserves current anonymous `/mcp`, initialization, notification, discovery, dispatch, Tool, plugin runtime, and Mnemosyne behavior under automated compatibility coverage.
- [x] A10) [P4] Ordinary imports remain side-effect free, startup remains deterministic, and plugin composition/runtime generation remain independent of Authentication adapter composition.
- [x] A11) [P4] Authentication and architecture documentation accurately describe delivered routing, principal, configuration, and anonymous contracts while marking bearer, OAuth, sessions, and Governance unimplemented.
- [x] A12) [P1] The complete identity/version impact decision is approved before implementation, and every applicable package, endpoint, protocol, configuration, runtime, plugin, capability, and compatibility guard passes.

Why now / impact
- Phase 4 begins with an Authentication foundation before concrete registered-client adapters. This Track establishes the permanent multi-adapter routing and ACL identity model, keeps anonymous access explicit, and prevents later bearer or OAuth behavior from leaking into MCP, Governance, or plugins.

Scope
- In scope:
  - Immutable adapter identity, adapter interface, result, and bounded failure contracts.
  - Host-owned evidence classification and unambiguous adapter routing.
  - Normalized anonymous/registered principal contracts and canonical namespaced identity construction.
  - Independent host configuration for anonymous access and zero or more adapter instances.
  - The minimum application/HTTP seam needed to apply anonymous/no-evidence behavior and carry normalized principals without changing current public behavior.
  - Test-owned synthetic adapters proving simultaneous composition, unambiguous routing, collision rejection, and no fallback without becoming production methods.
  - Import/dependency boundaries, deterministic tests, complete compatibility coverage, version governance, and documentation.
- Out of scope:
  - Production bearer or OAuth adapters and all method-specific provisioning, storage, discovery, issuer, token, rotation, revocation, or client behavior.
  - Request-driven loading, adapter installation/discovery, arbitrary external adapter code, hot activation, or runtime switching.
  - MCP session semantics, negotiated-context binding, session lifecycle, or runtime/policy session binding.
  - Governance policy design beyond carrying normalized ACL identity fields, filtered discovery/dispatch, Tool authorization, approval, or durable audit.
  - Changes to plugin contracts, plugin composition, plugins, Mnemosyne, or plugin-owned data.

Milestones
- [x] M1) Resolve principal grammar, adapter/router contracts, evidence classification, anonymous behavior, host configuration, package ownership, failures, compatibility, and version impact.
- [x] M2) Implement and validate principal, adapter, router, and anonymous contracts through focused TDD.
- [x] M3) Implement and validate immutable configuration/composition and the minimum permanent HTTP/application seam with unchanged public behavior.
- [x] M4) Complete documentation, full validation, independent acceptance review, and roadmap reconciliation.

Risks / decisions
- Risk: Bearer and OAuth commonly use the same HTTP authorization scheme; routing must not depend on unsafe guessing, sequential validation, or adapter order.
- Risk: Exposing adapter identity to Governance can couple ACLs to unstable implementation names unless the host owns stable configuration identity separately from code.
- Risk: Prefix construction can collide or become ambiguous unless adapter and subject grammars and canonical encoding are explicit.
- Risk: Treating anonymous as adapter failure or missing configuration would preserve a downgrade path.
- Risk: Designing generic settings before concrete adapters could freeze an unusable configuration shape; foundation settings must remain bounded to composition identity and routing needs.
- Risk: Wiring principal context deeply into MCP would absorb the separate principal/session-integration workstream.
- Decision: Follow `docs/AUTHENTICATION.md`: multiple adapters may operate simultaneously, anonymous is an independent mode, and submitted evidence routes to exactly one adapter without fallback.
- Decision: Governance may use principal kind, stable adapter identity, adapter-local subject, and canonical prefixed identity in ACLs; raw method evidence remains private to Authentication.
- Decision: TRACK_042 delivers contracts, routing, principal construction, configuration, and anonymous behavior only. Bearer and external OAuth remain separate Tracks.
- Decision: Activation authorizes only the declared TDD chunks, one at a time. It does not authorize roadmap mutation, commit, or push.
- Version impact: MyMCP distribution and endpoint/server marker advance together from `0.4.0` to `0.5.0` because this release adds a public host-configuration schema and an HTTP authentication gate, even though compatibility defaults preserve existing behavior. Host configuration adds schema 3; schemas 1 and 2 remain accepted with their exact plugin syntax and implicit compatibility authentication state. MCP protocol, host plugin API, manifest schema, external plugin-author contract, plugin identities/versions, capability contracts, plugin configuration/data schemas, policy revision, runtime-generation semantics, endpoint-visible bindings, and Mnemosyne record schemas remain unchanged because Authentication is a host-owned upstream layer and changes none of those contracts. The normalized-principal and Authentication-adapter contracts begin at host contract version 1 in documentation and code ownership; they are not MCP, plugin, or persisted-data version fields.

Open questions
- [x] Q1) What exact immutable fields, nullability, grammars, bounds, and consistency rules define anonymous and registered principals?
- [x] Q2) How does the host construct a collision-free canonical principal ID from adapter identity and adapter-local subject, and which delimiter or encoding prevents ambiguity?
- [x] Q3) What exact adapter interface and result/failure values remain independent of HTTP framework objects, MCP messages, Tools, plugins, and Governance?
- [x] Q4) Which bounded evidence descriptor lets the router select exactly one adapter before validation, especially when methods share an HTTP scheme?
- [x] Q5) What startup checks reject duplicate adapter identities, overlapping evidence descriptors, unknown adapter types, invalid settings, or ambiguous routing before application publication?
- [x] Q6) What exact host-configuration schema independently represents anonymous enablement and zero or more named adapter instances while preserving schema-1/schema-2 and absent-file compatibility?
- [x] Q7) What evidence-free HTTP behavior applies when anonymous is enabled or disabled, and what bounded failure applies to submitted invalid evidence?
- [x] Q8) What minimum principal-carrying application seam is delivered now, and what remains for the later MCP principal/session Track?
- [x] Q9) Which package owns principals, adapters, routing, composition, and settings, and which dependency tests enforce the system layers?
- [x] Q10) Which synthetic multi-adapter, application, route, runtime, plugin, and Mnemosyne tests prove routing and unchanged compatibility without adding a production method?
- [x] Q11) What is the complete identity/version impact, documentation set, exact TDD sequence, and final validation matrix?

Decision log
- Decision (system layers): Authentication is a host-owned layer between HTTP and MCP; it does not implement MCP sessions or Governance policy.
- Decision (anonymous): Anonymous is an independent configured access mode, not an adapter and never a fallback from submitted evidence.
- Decision (multi-adapter): Zero or more named adapters may be active simultaneously when evidence routing is unambiguous and startup-fixed.
- Decision (ACL identity): Governance receives normalized principal kind, stable adapter namespace, adapter-local subject, and canonical prefixed identity, but no credential or raw protocol claim.
- Decision (Track decomposition): TRACK_042 establishes the routing/principal foundation. Bearer and external OAuth follow as separate production-adapter Tracks.
- Decision (Q1 principal values): `Principal` is an immutable host value with exactly `kind`, nullable `adapter_id`, nullable `subject`, and host-derived `principal_id`. Kind is exactly `anonymous` or `registered`. Anonymous is exactly `(anonymous, null, null, anonymous)`. Registered requires a validated adapter ID and subject and cannot accept a caller-supplied canonical ID. Adapter IDs use the stable lowercase-kebab host identity grammar, 1-64 ASCII characters. Subjects are nonblank Unicode text bounded to 256 code points and 1,024 UTF-8 bytes, with no control, surrogate, or normalization-changing behavior; Authentication preserves the adapter-returned text exactly after validation.
- Decision (Q2 canonical identity): Registered IDs are `registered:<adapter-id>:<subject-token>`, where `subject-token` is RFC 4648 base64url without padding over the exact UTF-8 subject bytes. The fixed kind prefix, adapter grammar excluding `:`, and injective UTF-8/base64url encoding make anonymous and registered identities disjoint and prevent cross-adapter or delimiter collisions. Only the host constructor computes this field.
- Decision (Q3 adapter contract): `mymcp/authentication/` owns immutable `AuthenticationEvidence`, `AuthenticationRequestContext`, success, bounded failure, adapter registration, and adapter protocol values. Evidence contains one host-derived route descriptor and one bounded opaque credential payload; context contains only HTTP method and endpoint class needed by a method. Adapters return one local subject or one stable failure code and never receive FastAPI requests, MCP messages, Tools, plugin/runtime objects, Governance policy, configuration sources, or canonical principal IDs.
- Decision (Q4 evidence routing): A route descriptor is the exact bounded tuple `(source, scheme, profile)` produced by host-owned HTTP evidence extraction/classification, never by a client assertion or adapter validation result. Source, normalized ASCII scheme, and optional normalized ASCII profile each have fixed vocabularies/bounds. Router composition requires enabled registrations to claim disjoint exact descriptors; one submitted descriptor selects zero or one adapter by lookup. Zero, multiple, malformed, or unsupported matches fail without invoking an adapter. Classification is not credential validation and never probes adapters. Concrete bearer/OAuth Tracks must define reliable host-owned profiles or remain mutually non-composable when their evidence cannot be distinguished; this foundation does not guess from adapter order or token acceptance.
- Decision (Q5 composition): Before application publication, composition rejects duplicate adapter IDs, duplicate/overlapping route descriptors, unknown enabled adapter types, unavailable enabled implementations, invalid declaration fields/settings, excessive counts, and descriptor/registration mismatch. Disabled declarations are validated but neither loaded nor registered. The initial production registry contains no registered method implementation; test-owned synthetic adapters exercise composition.
- Decision (Q6 configuration): Host configuration schema 3 preserves schema-2 server/plugin syntax and adds required `[authentication]` with required native boolean `anonymous_enabled` and optional ordered `[[authentication.adapters]]` declarations. Each declaration has exactly stable `id`, registered `type`, native boolean `enabled`, and one bounded route descriptor table; method-specific settings are intentionally absent until a concrete adapter Track versions their shape. Schema-1/schema-2 documents and an absent file map to `anonymous_enabled=true` and no adapters, preserving current access exactly. Schema 3 has no implicit anonymous default. The immutable snapshot fixes authentication and plugins independently until restart.
- Decision (Q7 HTTP outcome): Both `/mcp` transports authenticate before body parsing, MCP logging, or dispatch. Evidence-free requests receive the fixed anonymous principal only when enabled. Every no-evidence-disabled, malformed, ambiguous, unsupported, or rejected-evidence outcome is HTTP `401` with an empty body and no JSON-RPC envelope or method-specific challenge; submitted evidence never falls back. `/health` and `/version` remain operational and unauthenticated.
- Decision (Q8 application seam): Application assembly injects one immutable `Authenticator` beside the existing dispatcher. The thin `/mcp` route extracts bounded evidence/context, obtains one principal, and passes it with the request to a host-owned principal-aware MCP application boundary whose initial implementation delegates unchanged MCP semantics to `MCPDispatcher`. This Track neither creates MCP sessions nor uses principal values for authorization; the later integration Track binds principal/session context into MCP explicitly.
- Decision (Q9 ownership): The new `mymcp/authentication/` package owns contract-v1 principals, evidence, adapters, routing, composition, and bounded failures and imports only the standard library. `mymcp/host/configuration.py` owns startup declarations; application/bootstrap composition maps declarations to the Authentication registry; routes own HTTP extraction/401 transport only; `mymcp/mcp/`, `mymcp/plugin/`, and every plugin remain Authentication-independent. Scoped guidance and AST dependency tests enforce these boundaries.
- Decision (Q10 compatibility): Test-owned synthetic adapters prove two simultaneous disjoint routes, same-subject namespace separation, duplicate/ambiguous rejection, exactly-one invocation, bounded failures, and no fallback. Configuration tests prove all three schemas, immutable snapshots, strict fields, defaults, counts, and restart-only behavior. Route/application tests prove anonymous compatibility, disabled anonymous, invalid evidence, pre-body/pre-MCP rejection, and unchanged initialization, notification, discovery, dispatch, plugin runtime, and Mnemosyne behavior.
- Decision (Q11 validation): Documentation updates cover `README.md`, `docs/AUTHENTICATION.md`, `docs/ARCHITECTURE.md`, `docs/CONFIGURATION.md`, `docs/GLOSSARY.md`, `docs/PLUGIN_ARCHITECTURE.md`, and applicable scoped `AGENTS.md`. Validation includes focused Authentication/configuration/route/application tests; existing configuration, bootstrap, runtime, MCP, production-compatibility, import-boundary, plugin, capability-ledger, and Mnemosyne suites; the full suite; `git diff --check`; package/version/definition guards; and direct connected MCP discovery/dispatch with compatibility anonymous defaults. No Tool definition changes, so every Mnemosyne capability ledger entry remains unchanged.

Plan (execution steps)
- [x] S1) Complete DRAFT review: resolve Q1-Q11, refine acceptance criteria, record the complete version-impact decision, and replace provisional implementation steps with exact coherent TDD chunks.
- [x] S2) Move TRACK_042 to ACTIVE (folder, filename, title, and Current path status) before any implementation or implementation-driving test.
- [x] S3) TDD chunk 1 — add focused failing tests for immutable principal/adapter/evidence/result contracts, strict bounds and consistency, host-only canonical ID construction, and import independence; add the smallest `mymcp/authentication/` contract implementation; refactor, run the focused tests and dependency guards, then update this Track.
- [x] S4) TDD chunk 2 — add focused failing tests for exact descriptor lookup, simultaneous synthetic adapters, exactly-one invocation, duplicate/overlap/startup rejection, anonymous behavior, and no fallback; add the smallest immutable router/composition implementation; refactor, validate, then update this Track.
- [x] S5) TDD chunk 3 — add focused failing schema tests for schema-3 Authentication declarations, exact schema-1/schema-2/absent compatibility, strict bounded failures, immutable snapshots, and independent plugin state; implement the smallest configuration model/parser/semantic checks; refactor, validate, then update this Track.
- [x] S6) TDD chunk 4 — add focused failing application/route tests for injected Authentication, anonymous/default compatibility on GET/POST `/mcp`, empty `401` before body parsing/logging/dispatch, submitted-evidence rejection without downgrade, and principal-aware boundary delivery; implement the smallest HTTP/application seam without changing MCP semantics; refactor, run focused compatibility tests, then update this Track.
- [x] S7) Advance MyMCP/package/server to `0.5.0`; update approved Authentication, configuration, architecture, glossary, plugin-architecture, README, and scoped-guidance documentation; run focused and full validation plus `git diff --check`, package/version/definition guards, and direct MCP checks; obtain independent acceptance review, reconcile the roadmap if needed, and complete only when every criterion passes.

Current inventory
- `mymcp/authentication/contracts.py` owns immutable standard-library-only adapter IDs, principal kinds and host-only principal construction, exact evidence routes, secret-redacting bounded evidence, request context, bounded outcomes, and the adapter protocol.
- `mymcp/authentication/router.py` now owns immutable registrations, complete duplicate identity/route rejection, exact route lookup, independent anonymous admission, host principal construction after adapter success, and bounded fail-closed handling for unsupported evidence, adapter failure, invalid adapter output, and adapter exceptions.
- `mymcp/authentication/__init__.py` exposes the Authentication contract-v1 and router/composition values.
- `tests/authentication/test_contracts.py` covers strict IDs, fixed anonymous and namespaced registered principals, canonical base64url identity, Unicode/code-point/UTF-8 bounds, immutable evidence/context/outcomes, redacted evidence representation, adapter protocol shape, and package import independence.
- `tests/authentication/test_router.py` covers simultaneous exact routes, exactly-one invocation, namespace separation, anonymous enabled/disabled behavior, duplicate identity/route rejection, immutable snapshots, unsupported/rejected/invalid/exception outcomes, and no fallback.
- `docs/AUTHENTICATION.md` documents delivered contract-v1 principals, routing, configuration, anonymous HTTP behavior, and Governance-facing identity while marking concrete adapters, sessions, and Governance unimplemented.
- `mymcp/host/authentication.py` now composes the immutable production Authenticator before plugin runtime composition. The current production registry contains no concrete methods: disabled declarations are inert and any enabled unavailable type fails before runtime/generation or external-plugin work.
- `mymcp/host/mcp_application.py` owns the minimum principal-aware application boundary, validates the normalized principal, and delegates unchanged messages to `MCPDispatcher` without interpreting method evidence or applying Governance.
- `mymcp/routes/mcp.py` now extracts one bounded Authorization evidence value, authenticates GET and POST before streaming, body parsing, MCP logging, or dispatch, returns empty `401` on every failure, and passes normalized principals to the application boundary. Profile extraction remains absent until a concrete adapter defines reliable host-owned classification.
- `mymcp/app.py` accepts an explicit Authenticator, preserves anonymous compatibility for existing programmatic `create_app(runtime)` callers, and composes production Authentication before the plugin runtime.
- `mymcp/mcp/` owns unchanged MCP/JSON-RPC meaning and remains Authentication-protocol-neutral.
- `mymcp/host/runtime.py` owns plugin runtime state and must remain separate from Authentication composition.
- `mymcp/host/bootstrap.py` is the explicit production composition root; Authentication composition ownership must not weaken plugin boundaries.
- `mymcp/host/configuration.py` owns immutable startup intent and is the approved source for anonymous and adapter configuration; schema 3 is the approved evolution while schemas 1 and 2 retain compatibility defaults.
- Host configuration now accepts strict schema 3 with required explicit anonymous enablement, ordered immutable adapter declarations, exact bounded adapter IDs/types/routes, optional route profiles, a 32-adapter limit, and distinct bounded duplicate-ID/route and limit failures. Schema 3 retains schema-2 plugin locator shape; schemas 1, 2, and absent configuration produce anonymous-enabled/no-adapter compatibility state.
- Production Authentication composition is delivered, but no registered adapter implementation is available: disabled declarations are inert and enabled declarations fail before plugin runtime composition. Schema parsing alone grants no adapter authority.
- `mymcp/plugin/` and `mymcp/plugins/` must not gain Authentication authority.
- `docs/ARCHITECTURE.md` defines the system layers and links to `docs/AUTHENTICATION.md`.
- No ACTIVE or BLOCKED Track exists. TRACK_042 is completed.

Artifacts
- Authentication architecture: `docs/AUTHENTICATION.md`.
- Living roadmap memory: namespace `mymcp`, collection `roadmaps`; delivered baseline revision 4, Phase 4 revision 8, and canonical index revision 15 after completion reconciliation.
- Applicable roadmap workstream: Phase 4 Track 1 — Authentication foundation.
- Delivered dependency: `.backlog/COMPLETED/2026/TRACK_041_COMPLETED_external_plugin_startup_composition.md`.
- Governance: `docs/AI_WORKFLOW.md`, `.backlog/README.md`, `.backlog/PORE.md`, root `AGENTS.md`, and applicable scoped guidance.

Completion notes
- TRACK_042 was rewritten under explicit user approval for simultaneous adapters, separately configured anonymous access, namespaced principals, and Governance-visible adapter identity for ACLs.
- Bearer, external OAuth, MCP sessions, Governance policy, approval, audit, and interoperability remain separate Tracks.
- No implementation, implementation-driving test, public behavior, version, commit, or push change was made by this DRAFT rewrite.
- Activation resolved Q1-Q11, approved host contract version 1 for Authentication values, selected host configuration schema 3 and MyMCP `0.5.0`, declared four coherent TDD chunks, and changed only this Track. No implementation-driving test or production change was made during activation.
- S3 followed red-green-refactor: the new focused suite first failed because `mymcp.authentication` did not exist; the minimal contracts then passed after tightening host-only principal construction and suppressing opaque evidence from representations. Validation passed 65 focused contract/import-boundary tests and `git diff --check`. Independent review identified the unchecked helper and evidence-representation risks, both resolved before this Track update.
- S4 followed red-green-refactor: the focused router suite first failed because `mymcp.authentication.router` did not exist; the minimal immutable composition and exact lookup then passed. Independent review found weak callable validation, escaping adapter exceptions, and untyped bounded-value checks; all were tightened before final validation. Final evidence is 77 Authentication/import-boundary tests passed plus `git diff --check`.
- S5 followed red-green-refactor: focused schema tests first failed because the Authentication configuration values did not exist; the minimal schema-3 model/parser then passed while retaining the schema-1 default and schema-2 plugin contract. Independent review found a missing declaration limit and an inability to represent profile-less routes; S5 added a bounded 32-adapter limit and optional profile parsing. Final evidence is 262 focused configuration, loading, semantics, bootstrap, CLI, Authentication, and import-boundary tests passed with 3 native-Windows-only skips, plus `git diff --check`.
- S6 followed red-green-refactor: focused route/application tests first failed because `create_router` and `create_app` had no Authentication seam. The minimal host composition, principal-aware boundary, and pre-body GET/POST authentication then passed without changing MCP results. Independent review found production Authentication was composed after the plugin runtime; ordering and regression coverage were corrected so unavailable enabled adapters reject first. Final evidence is 299 focused application, route, production-compatibility, Authentication, configuration, bootstrap, and import-boundary tests passed with 3 native-Windows-only skips, plus `git diff --check`.
- S7 completed: MyMCP/package/server is `0.5.0`; Authentication contract version 1 and host configuration schema 3 are documented; protocol, host/plugin/manifest/Mnemosyne/capability/data/record identities remain unchanged. Focused version tests first failed 14 tests against `0.4.0`, then passed all 88 after the approved bump. Final automated evidence is 1,421 passed with 3 native-Windows-only skips; focused package/version/manifest/parity/capability-ledger guards passed 65 tests; compileall and `git diff --check` passed. A clean `python -m build` produced and verified `mymcp-0.5.0` sdist/wheel including Authentication modules, after which generated artifacts were removed. Independent test and repository acceptance reviews found no blocker after stale Track/glossary text was corrected. A restarted connected server reported `mymcp 0.5.0` with the expected nine enabled Tools. Roadmap delivered baseline, Phase 4, and canonical index were revised under per-call approval; Phase 4 is IN PROGRESS with the operator-provisioned bearer adapter NEXT.
- TRACK_042 moved to COMPLETED after all acceptance criteria, milestones, plan steps, final validation, direct connected-server verification, independent review, and roadmap reconciliation passed. No commit, push, tag, or release publication was performed.

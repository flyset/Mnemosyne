# TRACK 042 [DRAFT]: Authentication routing and principal foundation

Track
- ID: TRACK_042
- Repository: MyMCP
- Branch: main
- Current path: .backlog/DRAFT/2026/TRACK_042_DRAFT_authentication_routing_and_principal_foundation.md

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
- [ ] A1) [P1] Immutable host-owned adapter and result contracts accept only bounded method-specific evidence/context and return one validated adapter-local subject or one bounded failure.
- [ ] A2) [P1] An immutable host-owned router classifies submitted evidence and invokes exactly one enabled adapter; ambiguous configuration or evidence fails closed without sequential attempts or fallback.
- [ ] A3) [P1] Automated dependency tests prove Authentication remains independent of MCP Tools, plugin contracts/domains, route implementation, FastAPI behavior, and Governance policy beyond approved transport-neutral values.
- [ ] A4) [P2] The normalized-principal contract contains exactly approved principal kind, nullable stable adapter identity, nullable adapter-local subject, and canonical host-constructed identity, with strict collision-free grammar and consistency rules.
- [ ] A5) [P2] Governance-facing values preserve adapter namespace for ACLs without exposing credentials or protocol claims; downstream code cannot supply or rewrite canonical identity.
- [ ] A6) [P3] MyMCP host configuration independently controls anonymous access and zero or more named adapters, validates bounded settings into the immutable startup snapshot, and requires restart for changes.
- [ ] A7) [P3] Evidence-free requests produce exactly the fixed anonymous principal only when anonymous access is enabled; when disabled they fail before MCP handling.
- [ ] A8) [P3] Invalid submitted evidence always fails before MCP handling even when anonymous access is enabled; tests prove no downgrade, fallback, or adapter-order behavior.
- [ ] A9) [P4] Production configuration preserves current anonymous `/mcp`, initialization, notification, discovery, dispatch, Tool, plugin runtime, and Mnemosyne behavior under automated compatibility coverage.
- [ ] A10) [P4] Ordinary imports remain side-effect free, startup remains deterministic, and plugin composition/runtime generation remain independent of Authentication adapter composition.
- [ ] A11) [P4] Authentication and architecture documentation accurately describe delivered routing, principal, configuration, and anonymous contracts while marking bearer, OAuth, sessions, and Governance unimplemented.
- [ ] A12) [P1] The complete identity/version impact decision is approved before implementation, and every applicable package, endpoint, protocol, configuration, runtime, plugin, capability, and compatibility guard passes.

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
- [ ] M1) Resolve principal grammar, adapter/router contracts, evidence classification, anonymous behavior, host configuration, package ownership, failures, compatibility, and version impact.
- [ ] M2) Implement and validate principal, adapter, router, and anonymous contracts through focused TDD.
- [ ] M3) Implement and validate immutable configuration/composition and the minimum permanent HTTP/application seam with unchanged public behavior.
- [ ] M4) Complete documentation, full validation, independent acceptance review, and roadmap reconciliation.

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
- Decision: This DRAFT authorizes no implementation-driving test, production change, version change, roadmap mutation, commit, or push.
- Version impact: Unresolved. Before activation, decide every relevant distribution, endpoint marker, MCP protocol, host plugin API, manifest schema, external plugin-author contract, host configuration schema, plugin, capability contract, plugin configuration/data, policy revision, runtime generation, public binding, and Mnemosyne record-schema dimension.

Open questions
- [ ] Q1) What exact immutable fields, nullability, grammars, bounds, and consistency rules define anonymous and registered principals?
- [ ] Q2) How does the host construct a collision-free canonical principal ID from adapter identity and adapter-local subject, and which delimiter or encoding prevents ambiguity?
- [ ] Q3) What exact adapter interface and result/failure values remain independent of HTTP framework objects, MCP messages, Tools, plugins, and Governance?
- [ ] Q4) Which bounded evidence descriptor lets the router select exactly one adapter before validation, especially when methods share an HTTP scheme?
- [ ] Q5) What startup checks reject duplicate adapter identities, overlapping evidence descriptors, unknown adapter types, invalid settings, or ambiguous routing before application publication?
- [ ] Q6) What exact host-configuration schema independently represents anonymous enablement and zero or more named adapter instances while preserving schema-1/schema-2 and absent-file compatibility?
- [ ] Q7) What evidence-free HTTP behavior applies when anonymous is enabled or disabled, and what bounded failure applies to submitted invalid evidence?
- [ ] Q8) What minimum principal-carrying application seam is delivered now, and what remains for the later MCP principal/session Track?
- [ ] Q9) Which package owns principals, adapters, routing, composition, and settings, and which dependency tests enforce the system layers?
- [ ] Q10) Which synthetic multi-adapter, application, route, runtime, plugin, and Mnemosyne tests prove routing and unchanged compatibility without adding a production method?
- [ ] Q11) What is the complete identity/version impact, documentation set, exact TDD sequence, and final validation matrix?

Decision log
- Decision (system layers): Authentication is a host-owned layer between HTTP and MCP; it does not implement MCP sessions or Governance policy.
- Decision (anonymous): Anonymous is an independent configured access mode, not an adapter and never a fallback from submitted evidence.
- Decision (multi-adapter): Zero or more named adapters may be active simultaneously when evidence routing is unambiguous and startup-fixed.
- Decision (ACL identity): Governance receives normalized principal kind, stable adapter namespace, adapter-local subject, and canonical prefixed identity, but no credential or raw protocol claim.
- Decision (Track decomposition): TRACK_042 establishes the routing/principal foundation. Bearer and external OAuth follow as separate production-adapter Tracks.

Plan (execution steps)
- [ ] S1) Complete DRAFT review: resolve Q1-Q11, refine acceptance criteria, record the complete version-impact decision, and replace provisional implementation steps with exact coherent TDD chunks.
- [ ] S2) Move TRACK_042 to ACTIVE (folder, filename, title, and Current path status) before any implementation or implementation-driving test.
- [ ] S3) Execute the approved focused TDD chunk for normalized principals, adapter contracts, and canonical identity construction; update this Track immediately.
- [ ] S4) Execute the approved focused TDD chunk for router classification, multi-adapter composition, configuration, anonymous behavior, and no-fallback boundaries; update this Track immediately.
- [ ] S5) Execute the approved focused TDD chunk for the minimum application/HTTP seam, synthetic multi-adapter coverage, and unchanged compatibility; update this Track immediately.
- [ ] S6) Apply approved version/documentation decisions, run focused and full validation plus `git diff --check`, obtain independent acceptance review, reconcile the roadmap if needed, and complete only when every criterion passes.

Current inventory
- `docs/AUTHENTICATION.md` defines multiple configured adapters, independent anonymous access, unambiguous evidence routing, namespaced principals, Governance ACL visibility, and security invariants; implementation does not yet exist.
- `mymcp/routes/mcp.py` owns thin HTTP transport and currently reaches MCP handling without an explicit Authentication router.
- `mymcp/mcp/` owns MCP/JSON-RPC meaning and currently receives no normalized principal; it must remain authentication-method-neutral.
- `mymcp/host/runtime.py` owns plugin runtime state and must remain separate from Authentication composition.
- `mymcp/host/bootstrap.py` is the explicit production composition root; Authentication composition ownership must not weaken plugin boundaries.
- `mymcp/host/configuration.py` owns immutable startup intent and is the approved source for anonymous and adapter configuration; exact schema evolution remains unresolved.
- `mymcp/plugin/` and `mymcp/plugins/` must not gain Authentication authority.
- `docs/ARCHITECTURE.md` defines the system layers and links to `docs/AUTHENTICATION.md`.
- No ACTIVE or BLOCKED Track exists. TRACK_042 is the only DRAFT Track.

Artifacts
- Authentication architecture: `docs/AUTHENTICATION.md`.
- Living roadmap memory: namespace `mymcp`, collection `roadmaps`, Phase 4 section “MyMCP roadmap — Phase 4 governance gateway,” revision 7 after this alignment.
- Applicable roadmap workstream: Phase 4 Track 1 — Authentication foundation.
- Delivered dependency: `.backlog/COMPLETED/2026/TRACK_041_COMPLETED_external_plugin_startup_composition.md`.
- Governance: `docs/AI_WORKFLOW.md`, `.backlog/README.md`, `.backlog/PORE.md`, root `AGENTS.md`, and applicable scoped guidance.

Completion notes
- TRACK_042 was rewritten under explicit user approval for simultaneous adapters, separately configured anonymous access, namespaced principals, and Governance-visible adapter identity for ACLs.
- Bearer, external OAuth, MCP sessions, Governance policy, approval, audit, and interoperability remain separate Tracks.
- No implementation, implementation-driving test, public behavior, version, commit, or push change was made by this DRAFT rewrite.

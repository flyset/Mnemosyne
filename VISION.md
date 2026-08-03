# MyMCP Vision

MyMCP is a local, client-neutral MCP host and governance gateway. It should let a
single user run narrowly scoped integrations behind one machine-local endpoint
without surrendering control of Tools, data, or mutation approval to a specific
AI client or plugin author.

MyMCP currently hosts the Mnemosyne user-governed memory domain through a
trusted bundled plugin. TRACK_031 delivered the Phase 1 kind-qualified runtime
foundation. TRACK_032 delivered immutable definition contracts, strict 64 KiB
manifest parsing, the complete packaged Mnemosyne declaration, exact
definition/contribution parity, and static bootstrap validation before
generation. TRACK_033's extraction implementation now places the canonical
Mnemosyne adapter, configuration, memory domain, and MCP adapters under
`mymcp/plugins/mnemosyne/`. TRACK_034 delivered the MyMCP/`mymcp` `0.2.0`
public-host release while permanently preserving Mnemosyne domain
behavior and identity.

The canonical repository is <https://github.com/flyset/MyMCP>; the former URL
redirects there. Repository/origin/history/tag/placeholder verification, tracked
and ignored OpenCode migration with Claude exclusion, normal endpoint/client
reconnect, and isolated approved-once and rejected/no-Tools-call checks are
complete. The public, non-draft, non-prerelease release
[`MyMCP 0.2.0: public-host cutover`](https://github.com/flyset/MyMCP/releases/tag/mymcp-v0.2.0)
is tagged `mymcp-v0.2.0` at `c2852bc`. MyMCP `0.4.0` delivered Phase 3 startup
composition for operator-installed, operator-trusted external plugins. MyMCP
`0.5.0` delivered Authentication contract version 1, exact routing, normalized
principals, and explicit anonymous configuration. MyMCP `0.6.0` delivered
`operator-bearer-v1` and host configuration schema 4. MyMCP `0.7.0` delivers
schema-5 OAuth integration: `oauth-jwt-jwks-v1` is a startup-fixed alternative
Bearer method, with one immutable validation snapshot and conditional RFC 9728
protected-resource metadata/challenge. Authentication still establishes identity
only; sessions and Gateway governance remain deferred.

## Role

MyMCP owns host-level composition and protocol mechanisms:

- one explicit MCP surface for independent compatible clients;
- stable Tool registration, identity, discovery, and dispatch;
- deterministic composition and collision handling;
- kind-qualified plugin-capability contracts and host-owned public bindings;
- startup composition, routing, policy, approval, and audit boundaries as they
  are introduced; and
- reusable host governance only after multiple integrations prove it generic.

Domain integrations own their application meaning. Mnemosyne therefore retains
its memory taxonomy, record semantics, retrieval, lifecycle policy, public
`memory_*` Tools, configuration, and storage identity.

## Current Foundation

The repository provides the MyMCP distribution and top-level Python host package,
kind-qualified immutable contracts, an explicit bundled Mnemosyne contribution,
host-owned bindings and `list_tools`, and an immutable runtime assembled by explicit
`build_production_runtime`. Its fixed packaged manifest is parsed strictly and
must exactly match the adapter definition and selected contribution before a
generation is constructed. `create_app(runtime)` and runtime-bound MCP dispatch
keep ordinary imports side-effect free; `create_production_app` is the supported
local Uvicorn factory target. The production surface contains the trusted
Mnemosyne `0.3.0` adapter over canonical registrations from the extracted bundled
plugin. Its per-capability contract declarations identify `memory_recall` as
`1.2.0` and the other seven capabilities as `1.1.0`; MyMCP's host/package/server
marker is independently `0.7.0`.

The released public-host cutover includes repository and operational
verification. MyMCP 0.4.0 adds schema-2 external startup composition while
retaining exact schema-1 behavior, including `enabled_plugin_unsupported`.
Configuration remains an immutable XDG-selected startup snapshot with loopback
packaged-launcher settings. Enabled schema-2 manifests preflight before any
import; compatible operator-trusted implementations then compose once for the
server start. Schema 3 adds immutable Authentication declarations and explicit
anonymous access. Schema 4 adds bounded non-secret verifier-source metadata for
the startup-fixed `operator-bearer-v1` adapter. Schema 5 adds one non-secret
canonical HTTPS OAuth issuer and composes `oauth-jwt-jwks-v1` from one immutable
startup snapshot before plugin runtime publication. OAuth and operator bearer
cannot be co-declared in schema 5; OAuth requires anonymous access disabled.
The OAuth resource identity derives only from configured loopback address and
port; literal loopback HTTP is a local interoperability exception, not remote or
TLS deployment support. Enabled OAuth alone publishes RFC 9728 metadata at
`/.well-known/oauth-protected-resource/mcp` and adds its body-free Bearer metadata
challenge to failed `/mcp` authentication. Client-neutral gateway policy and
reusable host services follow in that dependency order.

## Approved Target Architecture

MyMCP is working toward a generic versioned Tools-only plugin contract, an
immutable host runtime, explicit bundled bootstrap, vertically owned plugin
packages, and startup composition for operator-installed trusted external
plugins. The target places concrete bundled implementations under
`mymcp/plugins/` and all Mnemosyne production implementation and policy under
`mymcp/plugins/mnemosyne/`.

Bundled and configured external plugins share logical manifests, definitions,
kind-qualified capabilities, configuration declarations, and host-owned public
bindings. Enabled schema-2 manifests preflight before any external import; the
host then loads the trusted zero-argument `mymcp_plugin_v1` implementation and
validates definition/contribution parity and bindings before runtime construction.
External defaults are deterministic `<plugin-id>__<tool-local-id>` names; any
collision fails complete startup. Configuring an external plugin is the
operator's decision to trust it to execute; after validation it may run in
process. MyMCP does not promise sandboxing, isolation, filesystem or network
restriction, supervision, killability, or resource control for plugins. A
manifest is inert metadata, not authority, consent proof, or a safety claim.

Released `0.2.0` makes the endpoint/server, FastAPI
application, package metadata, and tracked official client identify MyMCP. The
canonical repository target is `https://github.com/flyset/MyMCP`; repository
migration is complete and the former URL redirects. The public release is tagged
`mymcp-v0.2.0` at `c2852bc`. Mnemosyne remains plugin
`mnemosyne` and retains every
`memory_*`, `MNEMOSYNE_*`, `~/.mnemosyne`, storage, record, and memory-domain
identity.

The client-neutral gateway target requires authenticated machine-local client
principals and sessions, policy-filtered discovery and dispatch,
host-verifiable single-use exact-call approval, and bounded content-free security
audit. Loopback reachability and client permission prompts are useful current
boundaries but do not satisfy that final server-enforced contract.

Every minimal implementation step should establish part of this declared target
rather than create an intentionally temporary boundary. The complete package,
manifest, identity, dependency, compatibility, security, and migration design is
defined in [the MyMCP plugin architecture](docs/PLUGIN_ARCHITECTURE.md).

## Principles

MyMCP should preserve:

- local-first operation and filesystem truth;
- a single-user model until a broader threat model is explicit;
- least privilege and small, explicit Tools;
- client-neutral server-enforced boundaries;
- explicit operator enablement and per-call user consent for mutations;
- deterministic startup and failure rather than hidden discovery or fallback;
- explicit operator trust for configured external plugin code;
- compatibility for existing integrations while contracts evolve; and
- separation between reusable host mechanism and domain-specific policy.

Generalization must be earned. A host service should not absorb Mnemosyne's
domain semantics merely because Mnemosyne is currently its only consumer. A
second real integration should prove reusable approval, audit, or storage
mechanisms before they become host infrastructure.

## Non-Goals

MyMCP should not become:

- a general shell-execution proxy;
- an unrestricted filesystem bridge;
- a secret store;
- a hidden system that bypasses client-visible consent;
- a multi-user or remote-trust platform before its threat model supports one;
- a client-specific bundle runtime presented as a universal MCP boundary;
- MCPB presented as the native MyMCP plugin format; or
- a marketplace, host-managed plugin installer, update/rollback manager, or
  plugin sandbox.

## Built-in Mnemosyne Domain

Mnemosyne remains the built-in user-governed memory domain. MyMCP/`mymcp`
`0.2.0` is the public-host release, while Mnemosyne's plugin, notebook,
Tool, configuration, storage, record, logging, consent, safety, and
domain-specific identity remain intact. Its direction is preserved in
[the Mnemosyne vision](docs/MNEMOSYNE_VISION.md).

Its seven canonical scopes are `self`, `relationship`, `preference`, `practice`,
`project`, `knowledge`, and `agent`. `agent` holds user-approved operational
configuration refinements for a named AI agent; it is not user-profile memory.
Structural boot configuration stays in the agent file, while approved
session-managed refinements may be Mnemosyne records without automatic sync.

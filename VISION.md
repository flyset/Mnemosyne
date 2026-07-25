# MyMCP Vision

MyMCP is a local, client-neutral MCP host and governance gateway. It should let a
single user run narrowly scoped integrations behind one machine-local endpoint
without surrendering control of Tools, data, or mutation approval to a specific
AI client or plugin author.

MyMCP currently hosts the Mnemosyne user-governed memory domain in-process.
TRACK_031 delivers the Phase 1 kind-qualified contracts, immutable `HostRuntime` with an
opaque generation, `ActivatedTool`/`PluginContribution` composition, trusted
internal effect/consent metadata, host-owned bindings and `list_tools`, explicit
production bootstrap, and runtime-bound dispatch. The public Mnemosyne 0.1.4
identity and behavior remain unchanged.

Manifest/`PluginDefinition` parity, `mymcp/plugins/mnemosyne/` extraction,
external installation/activation/isolation, lifecycle publication, gateway
governance, public metadata projection, and the 0.2.0 public-host cutover are
deferred.

## Role

MyMCP owns host-level composition and protocol mechanisms:

- one explicit MCP surface for independent compatible clients;
- stable Tool registration, identity, discovery, and dispatch;
- deterministic composition and collision handling;
- kind-qualified plugin-capability contracts and host-owned public bindings;
- native artifact, lifecycle, isolation, routing, policy, approval, and audit
  boundaries as they are introduced; and
- reusable host governance only after multiple integrations prove it generic.

Domain integrations own their application meaning. Mnemosyne therefore retains
its memory taxonomy, record semantics, retrieval, lifecycle policy, public
`memory_*` Tools, configuration, and storage identity.

## Current Foundation

The repository provides the MyMCP distribution and top-level Python host package,
kind-qualified immutable contracts, an explicit Mnemosyne contribution, host-owned
bindings and `list_tools`, and an immutable runtime assembled by explicit
`build_production_runtime`. `create_app(runtime)` and runtime-bound MCP dispatch
keep ordinary imports side-effect free; `create_production_app` is the supported
local Uvicorn factory target. The production surface still contains only the
trusted Mnemosyne 0.1.0 adapter over canonical registrations.

The next product step is strict shared definition/manifest parity and complete
Mnemosyne packaging under `mymcp/plugins/mnemosyne/`. The mandatory MyMCP
public-host cutover, inert native installation, isolated activation, lifecycle
publication, client-neutral gateway policy, public metadata projection, and
reusable host services then follow in that dependency order.

## Approved Target Architecture

MyMCP is working toward a generic versioned Tools-only plugin contract, an
immutable generation-ready host runtime, explicit bundled bootstrap, vertically
owned plugin packages, and a separately isolated native external-plugin
boundary. The target places concrete bundled implementations under
`mymcp/plugins/` and all Mnemosyne production implementation and policy under
`mymcp/plugins/mnemosyne/`.

Bundled and external plugins share logical manifest, definition,
kind-qualified capability, configuration, activation, and lifecycle semantics.
They do not share execution trust: source-controlled bundled plugins use reviewed
in-process adapters, while unknown external code is never imported into the host
and cannot activate without exact artifact approval, supervision, killability,
resource bounds, and default-deny filesystem/network enforcement. A manifest is
inert metadata, not authority, consent proof, or isolation.

After complete Mnemosyne extraction, a dedicated `0.2.0` compatibility migration
makes the endpoint/server, FastAPI application, repository metadata, and official
client identify MyMCP. Mnemosyne remains plugin `mnemosyne` and retains every
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
- separate trust and execution boundaries for reviewed bundled and unknown
  external code;
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
- a marketplace, unknown-code loader, or isolation claim before artifact,
  lifecycle, supervision, authority, and failure contracts are implemented and
  validated.

## Built-in Mnemosyne Domain

Mnemosyne remains the built-in user-governed memory domain and the current
`0.1.4` public server identity. The finished host is MyMCP, while Mnemosyne's
plugin, notebook, Tool, configuration, storage, record, safety, and
domain-specific identity remain intact. Its direction is preserved in
[the Mnemosyne vision](docs/MNEMOSYNE_VISION.md).

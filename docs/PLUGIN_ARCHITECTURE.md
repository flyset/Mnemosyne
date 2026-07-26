# MyMCP Plugin Architecture

> Status: approved target with the TRACK_031 Phase 1 foundation and implemented
> Phase 2 declaration/parity and bundled Mnemosyne extraction. This document
> distinguishes the current
> extracted bundled-plugin boundary from deferred external installation,
> activation/isolation, lifecycle management, gateway governance, and public
> metadata projection. TRACK_034 delivers the local MyMCP/`mymcp` `0.2.0`
> public-host candidate; repository migration, operational checks, and release
> publication remain pending. See
> [`ARCHITECTURE.md`](ARCHITECTURE.md) for the current code organization.

## Purpose

MyMCP is intended to become a local, client-neutral MCP host and governance
gateway. The host should combine narrowly scoped integrations behind one
machine-local endpoint while preserving clear ownership, least privilege,
explicit mutation consent, and compatibility.

That product direction needs a concrete technical destination. Otherwise a
series of locally minimal changes can create boundaries that must later be
reversed. MyMCP therefore uses **architectural minimalism**:

> Each implementation step should be the smallest correct step toward this
> declared target, not the smallest temporary structure that can be refactored
> after the architecture is invented later.

The first proof is Mnemosyne. It is now a vertically owned built-in plugin
without losing its public memory Tool, configuration, storage, or record
identity.

## Current position and target

The current implementation now provides:

- a generic immutable Tool registry;
- `ActivatedTool`/`PluginContribution` composition with trusted effect/consent;
- immutable `HostRuntime` with opaque generation identity;
- explicit `build_production_runtime` and runtime-bound MCP dispatch;
- host-owned complete-surface `list_tools`;
- one explicit in-process Mnemosyne integration;
- Mnemosyne-owned configuration;
- a Tool-independent memory domain;
- immutable definition contracts and strict manifest-v1 parsing; and
- fixed packaged Mnemosyne manifest/definition/contribution parity before
  runtime generation.

The local `0.2.0` candidate identifies the host endpoint/application, package,
and tracked official OpenCode connection/agent as MyMCP/`mymcp`. Its tracked
policy denies `mymcp_*` first, allows four read-only Tools, and asks for five
exact mutations. The canonical repository target is
`https://github.com/flyset/MyMCP`. Repository rename, client reconnect and
direct denial/approval verification, and tag/release publication remain pending.
Routes, MCP protocol, `list_tools`, and every Mnemosyne compatibility identity
remain unchanged.

The current ownership boundary is physically complete for the bundled
implementation. `mymcp/plugins/mnemosyne/` owns `manifest.json`, `plugin.py`,
`configuration.py`, the complete `memory/` domain, and all Mnemosyne MCP Tool
adapters under `mcp/tools/`. The TRACK_031 contribution has plugin
identity/version, qualified capability origin, trusted effect/consent metadata,
and host-owned endpoint-name bindings; TRACK_032 adds exact complete declaration
parity. Generic host MCP retains argument normalization, registry/dispatch, and
host-owned `list_tools`; explicit host bootstrap retains composition, bindings,
fixed manifest loading, parity validation, and runtime construction.

The target is a generic host, coherent bundled plugin implementations, and a
separately isolated native external-plugin boundary. Bundled and external
plugins share logical manifest, identity, capability, configuration, activation,
and lifecycle semantics; they do not share one trusted Python execution ABI.

The source package target is:

```text
mymcp/
  app.py
  cli.py
  settings.py

  routes/                         # HTTP transport only
    mcp.py
    health.py
    version.py

  mcp/                            # transport-neutral MCP behavior
    messages.py
    protocol.py
    dispatcher.py                 # runtime-bound MCP dispatch
    tool_arguments.py
    tool_registry.py
    tools/
      list_tools/                 # host-owned complete-surface Tool

  plugin/                         # generic plugin-author contract
    contracts.py
    definition.py
    manifest.py
    composition.py

  host/                           # immutable process assembly
    runtime.py
    bootstrap.py
    state.py                     # bindings, configuration, issued ownership
    installation.py              # inert artifacts, receipts, environments
    lifecycle.py                 # desired state and generation publication
    supervision.py               # isolated worker containment and grants
    gateway.py                   # principals, sessions, policy, approval
    audit.py                     # bounded host security records

  plugins/                        # concrete bundled plugins
    mnemosyne/
      manifest.json
      plugin.py
      configuration.py

      memory/                     # Mnemosyne memory domain
        errors.py
        scopes.py
        normalization.py
        records.py
        paths.py
        policy.py
        listing.py
        store.py
        retrieval.py
        service.py

      mcp/                        # Mnemosyne MCP adapters
        tools/
          _memory_content_refusal.py
          _memory_lifecycle.py
          _memory_revise.py
          _memory_forget.py
          memory_recall/
          memory_list/
          memory_inspect/
          memory_remember/
          memory_archive/
          memory_restore/
          memory_revise/
          memory_forget/
```

The exact implementation may add narrow `__init__.py` files and tests, but it
must preserve these ownership boundaries. Repository documentation, tests,
explicit bootstrap references, compatibility bindings, managed external
artifacts, and user data are not bundled Mnemosyne implementation logic and
remain outside the plugin directory.

Initial native external plugins are prebuilt Python wheels installed into
host-managed immutable environments outside both the MyMCP interpreter and
`mymcp/plugins/`. Unknown external code executes only through a separately
versioned supervised worker boundary after its complete artifact closure and
requested authority have been validated and approved. It is never imported into
the host process.

## Architectural layers

### HTTP transport

`mymcp/routes/` owns HTTP paths, request-body intake, status codes, streaming,
and FastAPI response serialization. It may depend on the composed host runtime
but must not import a plugin domain or plugin configuration.

The MCP layer returns transport-neutral protocol envelopes or notification
outcomes. FastAPI response types do not belong in the target MCP protocol
modules.

### Generic MCP runtime

`mymcp/mcp/` owns MCP and JSON-RPC meaning:

- message parsing and normalization;
- method dispatch;
- immutable Tool registration and invocation;
- schema-aware argument compatibility;
- standard result and error envelopes; and
- host-owned MCP Tools such as `list_tools`.

It owns no Mnemosyne taxonomy, configuration, storage, handler, or Tool
definition.

### Plugin-author contract

`mymcp/plugin/` is singular because it is one host-owned plugin API. It defines
bounded immutable contracts for manifests, definitions, activation,
kind-qualified capability identity, effect and consent metadata, public
bindings, configuration and data declarations, validation, and composition.

Host API v1 is Tools-only. The logical API is adapter-neutral and asynchronous:
activation, invocation, health, cancellation, deadlines, drain, and shutdown
have the same meaning for trusted bundled and isolated external plugins without
making their execution authority equivalent.

The contract package does not discover packages, import configured modules,
install software, supervise processes, grant authority, store secrets, or
contain a concrete plugin.

### Host runtime and bootstrap

`mymcp/host/runtime.py` owns the implemented immutable `HostRuntime`. The
current runtime
contains:

- the final immutable Tool registry;
- the ordered plugin inventory;
- kind-qualified capability origins;
- trusted internal effect and consent metadata;
- qualified-to-public Tool bindings; and
- one host-issued opaque runtime-generation identity.

It contains no Mnemosyne-specific policy or artifact identity. Artifact identity
and external activation remain deferred. The metadata is retained so later
gateway policy can reason about origin and effect without redesigning Tool
identity or treating a public name as authorization identity.

`mymcp/host/bootstrap.py` is the only generic-host module permitted to import
concrete bundled plugin adapters. Current bootstrap uses one explicit,
source-controlled Mnemosyne contribution. External definitions and activated
worker adapters later enter through host-owned validated installation and
supervision, not configured imports. Bootstrap performs no source-directory,
arbitrary
manifest-path, network, marketplace, or configured-module discovery.

Application assembly constructs the runtime explicitly. Importing an ordinary
`mymcp` package or submodule must not compose the production runtime as a side
effect in the target architecture.

The remaining host-owned modules establish authority outside the author
contract: state owns persisted bindings, validated ordinary configuration,
typed secret references, and issued data/state/cache ownership; installation
owns inert artifacts, receipts, and immutable managed environments; lifecycle
owns desired state and atomic runtime-generation publication; supervision owns
isolated workers and enforceable grants; gateway owns local principals,
sessions, policy, and approval; and audit owns bounded security records. These
mechanisms remain domain-neutral and never absorb Mnemosyne memory policy.

### Bundled plugins

`mymcp/plugins/` is plural because it contains concrete source-controlled
implementations. Every bundled plugin follows the shared logical author
contract. Its trusted in-process adapter remains distinct from the isolated
external execution adapter; built-in status grants reviewed host-process
authority, not a claim of sandboxing.

`mymcp/plugins/mnemosyne/` owns all Mnemosyne production meaning:

- manifest and plugin contribution;
- `MNEMOSYNE_*` and `~/.mnemosyne/config.toml` configuration;
- memory scopes, records, policy, retrieval, lifecycle, and persistence;
- every `memory_*` Tool definition and handler; and
- lazy memory-root, store, and service composition.

Mnemosyne may use generic host plugin and MCP contracts. It may not import HTTP
routes, application assembly, host bootstrap, or another plugin.

### Native external plugins

In host API v1, one native external plugin release is one prebuilt plugin wheel
plus a complete prebuilt hash-locked dependency-wheel closure. The initial
native contract accepts no source distribution, editable or VCS installation,
source build, setup hook, arbitrary command, or network dependency resolution.
One inert manifest is packaged at
`<distribution>.dist-info/mymcp-plugin.json`. Standard wheel entry-point
metadata may identify the isolated worker adapter, but inspecting metadata never
loads it and the host process never imports it.

The host validates archives and compatibility before execution, binds an
immutable installation receipt to every artifact digest and approved authority,
and installs offline into one immutable environment per plugin version and
artifact closure. Separate plugins never share an environment. Installation may
exist before isolation support; activation may not.

## Identity and version model

Several identities must remain separate:

| Dimension | Owner | Compatibility and evolution rule | Target example |
| --- | --- | --- | --- |
| MyMCP distribution version | MyMCP release | Semantic package/release evolution; it does not version a plugin or generation | `0.2.0` at public-host cutover |
| Endpoint/server identity and marker | MyMCP endpoint | Public compatibility marker, normally equal to the release version but changed only through an explicit endpoint migration | `mymcp 0.2.0` |
| MCP protocol version | MCP specification and endpoint negotiation | Session-negotiated independently of plugin and worker APIs | supported MCP revision |
| Host plugin API | MyMCP | Integer logical-contract level; incompatible definition or activation semantics require a new level | `1` |
| Manifest schema | MyMCP | Strict integer shape; unsupported versions fail closed | `1` |
| External worker protocol | MyMCP | Separately negotiated host/worker execution protocol; host API compatibility does not imply worker compatibility | bounded v1 protocol |
| Plugin identity | Plugin author, admitted by MyMCP | Stable machine identity excluding version | `mnemosyne` |
| Plugin version | Plugin author | Semantic implementation release agreeing across wheel, manifest, definition, and receipt | `1.0.0` |
| Capability kind and local ID | Plugin author, validated by MyMCP | Stable identity excluding version; host API v1 admits only `tool` | `tool`, `memory_recall` |
| Capability contract version | Plugin author | Semantic compatibility of one capability schema/result contract | `1.0.0` |
| Configuration schema | Plugin author | Explicit version validated before activation | `1` |
| Plugin-data schema | Plugin author | Monotonic durable-data version requiring supervised migration rules | `1` |
| Artifact identity | MyMCP installer | Exact digest of the plugin and complete dependency closure; versions never substitute for it | digest-bound receipt |
| Policy revision | MyMCP gateway | Immutable authorization snapshot; affected sessions and approvals become stale under defined policy changes | opaque revision |
| Runtime generation | MyMCP runtime | Opaque unique publication identity, never reused or interpreted as semantic compatibility | opaque generation ID |
| Endpoint-visible Tool name | MyMCP binding policy | Flat binding independent of qualified identity and plugin claims | `memory_recall` |

These values may coincide, but compatibility is never inferred from coincidence.
Identity excludes version. The MCP protocol, host API, manifest, worker
protocol, plugin, capability, configuration, plugin-data, policy, artifact, and
runtime-generation dimensions solve different problems and are validated
independently. Existing Mnemosyne record schema versions remain plugin-owned.

The host-controlled product, endpoint, FastAPI application, distribution
metadata, and tracked official client identity are MyMCP in the local `0.2.0`
candidate. The existing `0.1.x` line is the prior Mnemosyne-public-host
compatibility era. Repository rename, operational validation, and release
publication remain required before public completion; external activation and
gateway operation remain later gates.

| Public-host dimension | Prior `0.1.x` era | Local `0.2.0` candidate / final action |
| --- | --- | --- |
| Product, distribution, package, commands | MyMCP; `mymcp`; `mymcp*` commands | MyMCP; `mymcp`; `mymcp*` commands; package version `0.2.0` |
| MCP server machine name | `mnemosyne` | `mymcp` |
| FastAPI application title | `Mnemosyne MCP Server` | `MyMCP` |
| Canonical repository | `flyset/Mnemosyne` | Target `https://github.com/flyset/MyMCP` (rename pending) |
| Official client and agent key | `mnemosyne` | `mymcp` |
| Client-generated permission prefix | `mnemosyne_*` | `mymcp_*` |
| Routes and host Tool | `/mcp`, `/health`, `/version`, `list_tools` | Preserve |
| Mnemosyne identity | plugin `mnemosyne`, `memory_*`, `MNEMOSYNE_*`, `~/.mnemosyne`, memory formats and paths | Preserve |

The candidate endpoint marker changes from `mnemosyne 0.1.x` to `mymcp 0.2.0`
without a duplicate endpoint, fallback identity, or Tool alias. The MCP protocol
version changes only for an independent protocol-compatibility reason.

## Capability identity and public Tool binding

The durable internal capability identity is the triple:

```text
(plugin_id, capability_kind, capability_local_id)
```

For example:

```text
plugin identity:              mnemosyne
capability kind:              tool
plugin-local capability ID:   memory_recall
qualified capability identity: (mnemosyne, tool, memory_recall)
endpoint-visible Tool name:   memory_recall
```

Host API v1 accepts exactly capability kind `tool`. Adding MCP Resources,
Prompts, or another capability family requires explicit host-API evolution; they
must not be encoded as Tool IDs. Plugin IDs use bounded lowercase kebab identity,
Tool-local IDs use bounded lowercase underscore identity, and neither grammar
admits the reserved `__` separator.

The manifest declares capability kind and plugin-local ID but no endpoint name.
The host owns the binding from qualified identity to endpoint-visible name. The
final runtime retains both the public name and qualified origin.

This separation provides four properties:

1. Existing Mnemosyne names remain unchanged.
2. Plugins cannot reserve public endpoint names through manifest data alone.
3. Public-name collisions fail before a runtime is published.
4. External plugins receive a deterministic collision-visible default without
   changing qualified identity or creating duplicate Mnemosyne aliases.

Mnemosyne's current `memory_*` names are host-pinned canonical compatibility
bindings, not temporary aliases. Binding precedence is: host-reserved names and
prefixes; host-pinned compatibility bindings; persisted operator bindings; then
the deterministic external default `<plugin-id>__<tool-local-id>`. `list_tools`
and the `mymcp_*` prefix remain host-reserved. Final collisions reject the whole
candidate generation without overwrite, suffix fallback, shadowing, or duplicate
aliases. A persisted binding remains stable if a later release changes its
default algorithm.

Client-created prefixes such as the prior-era OpenCode
`mnemosyne_memory_recall` are client-side names derived from the configured
connection key and are not host binding inputs. The tracked local candidate uses
official key `mymcp` and `mymcp_*` permission names; endpoint-visible `memory_*`
names do not change. Direct operational approval checks remain pending.

## Trusted Tool effect and consent metadata

Every manifest Tool declaration contains four explicit effect dimensions:

- `read_only` — the Tool does not perform an externally observable mutation;
- `destructive` — the Tool may irreversibly remove or destructively replace
  state;
- `idempotent` — repeating the same successful request is intended to create no
  additional effect; and
- `open_world` — the Tool may interact with entities outside its bounded local
  domain.

Every declaration also contains `consent`:

- `none` — this plugin contract adds no per-call approval requirement; or
- `per_call` — the operation requires the existing client-visible approval
  boundary for each exact call.

These are trusted host/plugin contract values validated during composition. They
are not operating-system permissions, sandbox rules, or proof that a client
displayed and obtained approval. MyMCP must continue to use operator enablement
and compatible client approval for mutations.

The dimensions are informed by MCP Tool annotations, but public annotations are
explicitly untrusted hints in MCP. MyMCP does not derive trusted policy from
client-visible annotations and does not automatically publish internal metadata
as annotations. Any future public projection is a separate public-contract
decision.

## Manifest schema version 1

Each bundled plugin contains one strict `manifest.json`; each external wheel
contains the same logical manifest at the fixed inert `.dist-info` location.
Schema version 1 requires these conceptual fields:

- `manifest_version`;
- `id`;
- `title`;
- `description`;
- semantic `version`;
- `requires.host_api.min` and `requires.host_api.max`;
- complete kind-qualified `capabilities` declarations;
- a versioned bounded ordinary-configuration schema;
- declared secret-reference slots;
- a plugin-data schema version; and
- requested execution-authority classes.

An optional `$schema` may support authoring and validation tooling. Each v1
capability declaration requires:

- `kind`, exactly `tool`;
- plugin-local `id` and capability-contract `version`;
- `read_only`;
- `destructive`;
- `idempotent`;
- `open_world`; and
- `consent`, limited to `none` or `per_call`.

A minimal one-Tool example is:

```json
{
  "$schema": "https://mymcp.local/schemas/plugin-manifest-v1.json",
  "manifest_version": 1,
  "id": "example",
  "title": "Example",
  "description": "Example MyMCP plugin.",
  "version": "1.0.0",
  "requires": {
    "host_api": {
      "min": 1,
      "max": 1
    }
  },
  "capabilities": [
    {
      "kind": "tool",
      "id": "read_status",
      "version": "1.0.0",
      "read_only": true,
      "destructive": false,
      "idempotent": true,
      "open_world": false,
      "consent": "none"
    }
  ],
  "configuration": {
    "schema_version": 1,
    "schema": {
      "type": "object",
      "properties": {},
      "additionalProperties": false
    }
  },
  "secret_references": [],
  "data_schema_version": 1,
  "authority": {"filesystem": [], "network": false}
}
```

The concrete Mnemosyne manifest must enumerate all possible `memory_*` Tools,
including default-disabled mutations. Runtime gate selection determines which
declared capabilities enter the final registry for that process.

### Manifest responsibilities

The manifest:

- establishes stable plugin identity and version;
- states the supported host plugin-API interval;
- declares the complete possible kind-qualified capability inventory;
- declares trusted effect and consent metadata;
- declares bounded configuration shape, secret-reference slots, data version,
  and requested authority without carrying their values or granting access;
- supports strict package/contribution parity checks; and
- allows inert installation validation to fail before code execution and
  worker-returned definition/activation parity to fail before runtime
  publication.

Unknown fields, invalid identities or versions, unsupported capability kinds,
duplicate local identities, unsupported host API intervals, undeclared
activations, inconsistent effect/consent/configuration/data/authority metadata,
and invalid selected subsets are rejected with no partial installation or
runtime.

### Manifest non-responsibilities

Schema version 1 does not contain:

- executable module, class, command, or argument values;
- dynamic discovery, dependency resolution, or installation instructions;
- complete MCP Tool definitions or duplicated input/output schemas;
- endpoint-visible Tool names;
- environment values, configuration values, credentials, or secrets;
- arbitrary filesystem or network paths;
- runtime enablement state;
- client approval claims;
- granted operating-system permission or isolation claims;
- health, update, removal, or lifecycle metadata; or
- a memory-data index, manifest, migration ledger, backup, or tombstone.

The external wheel may separately carry one standard metadata entry point that
identifies its worker adapter. It is not manifest authority or an import request:
the host inspects it as inert metadata. After artifact validation, approval, and
isolation setup, the supervisor starts the worker in `activating` state. Only
that worker resolves the entry point and returns its definition for parity
checking before activation succeeds or any runtime generation is published.

Tool schemas remain derived from the plugin's canonical domain definitions and
runtime registrations. Mnemosyne's JSON memory files remain its storage source
of truth.

## Plugin definition, context, and activation

The immutable `PluginDefinition` contracts, strict manifest parser, and static
parity validation are implemented. `PluginContext` and activation remain target
architecture. The invariants are:

- `PluginDefinition` is immutable data that exactly agrees with the packaged
  manifest's identity, compatibility, complete capability metadata,
  configuration shape, secret slots, data version, and requested authority;
- it contains no handler, command, import, secret, open resource, running task,
  ambient host object, or registry mutation capability;
- the host supplies an immutable `PluginContext` containing exact plugin and
  runtime-generation identity, validated ordinary configuration, opaque
  declared secret handles, issued private data/state/cache capabilities,
  deadline/cancellation, and a bounded event sink;
- context contains no host application, service locator, shell, unrestricted
  path, ambient environment, principal credential, policy database, audit
  store, another plugin, or registry publication capability;
- activation returns the ordered selected subset of declared capabilities,
  complete authoritative MCP Tool definitions, adapter-owned invokers keyed by
  qualified identity, an optional bounded health probe, and required idempotent
  shutdown;
- selected definitions and invokers remain paired, and disabled capabilities do
  not enter discovery or dispatch;
- activation, invocation, health, cancellation, drain, and shutdown have
  asynchronous logical semantics with host deadlines and runtime-generation
  identity; and
- activation cannot mutate the already published runtime.

Trusted bundled adapters may wrap current synchronous handlers without changing
their public contract and shut down cooperatively. External adapters proxy to a
supervised worker; shutdown is cooperative until its deadline and then the host
terminates the complete process group. Generic composition sees the same
validated activation result and does not depend on which adapter produced it.

## Bootstrap and composition

The first target implementation remains static and in-process for trusted
source-controlled built-ins:

1. Host bootstrap imports each bundled adapter explicitly.
2. It declares their order and compatibility Tool bindings explicitly.
3. Each adapter produces one immutable definition and selected contribution.
4. The host strictly parses each fixed packaged manifest (at most 64 KiB).
5. The host validates plugin identity/version and host API compatibility.
6. The host validates complete manifest/definition/contribution parity.
7. The host validates each selected capability and public binding.
8. Duplicate plugin IDs, qualified capability identities, public names, and
   claims on host-reserved names fail composition.
9. Host-owned `list_tools` is bound to the complete selected public surface.
10. One immutable `HostRuntime` generation is constructed and used until
    restart.

Any failure returns no partial runtime. Static bootstrap performs no arbitrary
import, source-directory, configured-module, manifest-path, entry-point, or
network discovery. Later external composition consumes only approved installed
definitions and already supervised worker adapters. It never turns manifest or
configuration text into a host-process import.

Mnemosyne continues to resolve immutable mutation gates once during startup and
the memory root lazily after Tool-specific validation for each operation.

## Dependency rules

| Owner | May depend on | Must not depend on |
| --- | --- | --- |
| `mymcp/routes/` | FastAPI, transport-neutral MCP handling, composed runtime | plugin domains or plugin configuration |
| `mymcp/mcp/` | standard library, generic runtime contracts | FastAPI in target protocol modules, concrete plugins, Mnemosyne domain/configuration |
| `mymcp/plugin/` | standard library, generic MCP registration types | concrete plugins, routes, plugin configuration, installation or supervision |
| `mymcp/host/runtime.py` | generic plugin composition and MCP registry | concrete plugins or domain policy |
| `mymcp/host/bootstrap.py` | generic runtime plus explicit bundled adapters and validated external activation inputs | dynamic source discovery or configured import paths |
| `mymcp/host/state.py` | strict host/plugin configuration models, bindings, secret references, issued ownership | plaintext secrets, arbitrary plugin-selected paths, domain data semantics |
| `mymcp/host/installation.py` | inert wheel/metadata validation and host-owned state paths | importing plugin code, network resolution, domain data |
| `mymcp/host/lifecycle.py` | installation, supervision, runtime, and bounded host state contracts | plugin domain policy or partial publication |
| `mymcp/host/supervision.py` | isolated worker protocol and platform enforcement adapters | host registries/policy objects inside workers, unrestricted fallback |
| `mymcp/host/gateway.py` | runtime identity, principals, sessions, policy, approval verification | plugin policy claims as authority, Mnemosyne domain policy |
| `mymcp/host/audit.py` | bounded host security-event contracts and private persistence | request/result content, plugin-writable records |
| Mnemosyne `plugin.py` | generic plugin/MCP contracts and its own packages | routes, app assembly, host bootstrap, other plugins |
| Mnemosyne `mcp/` | generic MCP contracts and Mnemosyne memory types | FastAPI, routes, concrete host startup, other plugins |
| Mnemosyne `memory/` | standard library and its own modules | MCP, host, routes, FastAPI, other plugins |
| Mnemosyne `configuration.py` | standard library | MCP, host settings, routes, FastAPI, other plugins |
| external worker adapter | versioned worker SDK and its own installed environment | host Python objects, principal credentials, policy/audit stores, other plugins |

Only bootstrap may point from generic host code to a concrete bundled plugin.
Unknown external code is never imported by generic host code. Plugins may not
import one another. A host service may not absorb Mnemosyne taxonomy or policy
merely because Mnemosyne is the first consumer.

Automated boundary tests must enforce these rules. They should check dependency
direction and ownership rather than freeze incidental file counts forever.

## Compatibility contract during extraction

Plugin extraction is an ownership change, not permission to redesign
Mnemosyne. Structural migration preserves:

- `/mcp`, `/health`, and `/version` behavior;
- the MyMCP/`mymcp` `0.2.0` candidate server identity and compatibility marker;
- `list_tools` ownership, output, and first position;
- all existing `memory_*` names, order, schemas, results, and errors;
- host-generic one-layer Tool-argument normalization;
- tracked `mymcp_*` client-prefixed permission names and their deny-first,
  read-only-allow, exact-mutation-ask order;
- independent default-off mutation gates and startup-fixed availability;
- per-call approval requirements for exact mutation calls;
- `MNEMOSYNE_*` variables and strict `~/.mnemosyne/config.toml` behavior;
- `~/.mnemosyne/memory` and `MNEMOSYNE_MEMORY_ROOT`;
- lazy first-run root initialization;
- version-1 and version-2 record formats and deterministic paths;
- lifecycle, content-refusal, logging, and uncertain-outcome behavior;
- one process-shared list-cursor codec and mutation-lock registry; and
- filesystem JSON records as the source of truth.

Current internal Python paths are not a documented external API. Migration
should therefore move one canonical implementation and update repository imports
without permanent shims. If a coherent TDD chunk temporarily needs an old path,
that module may only re-export canonical objects and must be removed within the
extraction phase. It must never duplicate dataclasses, cursor state, locks, or
domain implementation.

The local candidate completes the code and tracked-policy portion of the
mandatory separate public-host identity migration. It changes server/application,
package, and official tracked-client identity from Mnemosyne to MyMCP in the
first `0.2.0` build while preserving the plugin compatibility list above. Client
connection-key and permission-prefix changes are atomic so no mutation Tool
becomes callable under a new prefix without its exact approval rule. Restart/
reconnect and direct discovery, denial/no-call, and exact-call approval checks,
plus repository rename and publication, remain pending. There is no duplicate
endpoint, Tool alias, or runtime identity fallback.

## Security and trust boundary

The bundled and external trust classes are explicit.

Trusted bundled plugins provide organizational and protocol least privilege, not
process isolation:

- only source-controlled adapters named by bootstrap execute;
- no MCP request or operator setting supplies an import or manifest path;
- only validated selected capabilities enter discovery and dispatch;
- manifests carry no secrets or executable locations;
- duplicate, incompatible, or inconsistent identity fails startup closed;
- Mnemosyne continues to reject caller-supplied storage paths;
- mutation Tools remain independently operator-enabled; and
- exact mutation calls still require compatible client approval.

An in-process Python plugin has the host process's operating-system authority.
Source control, review, and explicit bootstrap establish bundled trust; a
manifest does not sandbox filesystem or network access.

Unknown external code is never imported into the host process and cannot become
active until the platform enforces all approved controls:

- exact plugin and dependency artifact digests, local provenance, immutable
  approval receipt, and installed-file parity;
- inert manifest/artifact compatibility before code execution, followed by
  worker-returned definition parity while the isolated process is still
  `activating` and before runtime publication;
- one host-supervised process group with private bounded authenticated IPC;
- startup, invocation, cancellation, concurrency, queue, and message limits;
- a minimal allowlisted environment with no inherited host secrets;
- read-only code and only explicitly issued private data/state/cache paths;
- default-denied network, including separately controlled egress, listening,
  name resolution, and loopback;
- bounded CPU, memory, process descendants, open handles, disk/cache, output,
  and wall time; and
- reliable graceful shutdown followed by forced termination of the complete
  process tree.

An unsupported mandatory control refuses activation instead of weakening the
profile or falling back to host-process execution. Signing may strengthen
provenance later but never replaces exact digest approval, compatibility,
operator authorization, or isolation. Manifests request authority; only host
policy and the enforcement backend grant it.

MCP recommends human confirmation for sensitive operations but does not provide
the server cryptographic proof that a client displayed an approval prompt.
Effect and consent metadata therefore establish a trusted policy floor but do
not manufacture consent.

## Configuration, secrets, and plugin-owned data

Target host control state lives under `~/.mymcp/` and keeps these dimensions
separate:

- host desired installation/enablement, required-or-optional classification,
  public bindings, and execution grants;
- schema-validated ordinary per-plugin configuration;
- typed secret references, never plaintext secret values;
- immutable installation receipts and managed environments; and
- host-issued private durable data, durable operational state, and disposable
  cache ownership for each plugin.

Plugins cannot nominate arbitrary host paths or see another plugin's directories.
External workers receive only the approved logical grants in their sandbox.
Receipts, manifests, ordinary configuration, status, and logs never contain
plaintext secrets. Secret acquisition and provider implementation are separate;
until a declared secret can be resolved safely, the dependent plugin cannot
activate.

Mnemosyne is a deliberate compatibility adaptation: its bundled adapter retains
the existing `MNEMOSYNE_*`, `~/.mnemosyne/config.toml`, and
`~/.mnemosyne/memory` contracts. Extraction and host cutover do not relocate or
duplicate its configuration or data.

## Lifecycle and immutable runtime generations

Installation state, desired enablement, observed worker state, immutable runtime
generation, and plugin-data state are separate dimensions. Installation can be
`absent`, `staged`, or `installed`; desired state is `disabled` or `enabled`;
observed execution distinguishes inactive, activating, active, draining,
stopped, failed, and quarantined outcomes.

The first implementation may publish only at restart. Every publication still
constructs and validates a complete candidate generation before atomically
exposing it. Later live replacement follows the same rule: new calls bind to the
new generation, in-flight calls remain pinned to their original definitions,
handlers, artifacts, and bindings plus the separately selected immutable policy
context, and the old generation drains before shutdown. Required-plugin failure
aborts publication and leaves the active generation unchanged. Optional failure
is visible and audited, never silently omitted. Quarantine overrides desired
enablement until explicit recovery.

Update stages an immutable artifact and environment beside the active version.
It validates compatibility, authority, configuration, migration readiness, and
worker health before publication. Activation cannot migrate data implicitly.
Rollback requires code/data compatibility or an explicit reversible migration;
updates requiring unsupported data migration fail without replacing the active
generation.

Disable prevents new calls before drain and shutdown. Remove requires inactivity
and removes executable activation state while preserving configuration, secret
references, data, state, and cache by default. Purge is a separate destructive,
exact-target, approval-gated operation after drain and termination. It accepts
only host-recorded plugin-owned targets and does not claim secure erasure of
journals, snapshots, backups, client history, or external copies.

## Client-neutral gateway prerequisites

The one human user remains the only user. A client principal identifies one
operator-enrolled local client application or installation, not another human,
tenant, or data partition. Loopback reachability, MCP `clientInfo`, connection
key, process ID, user agent, and request ID do not authenticate a principal.

Host-created authenticated sessions carry immutable principal, policy revision,
runtime generation, and negotiated MCP context. Principal revocation and policy
restriction take effect immediately; new grants require session refresh. The
complete internal runtime is not itself a client view: `tools/list`, host
`list_tools`, and dispatch use one policy-filtered kind-qualified view, and every
dispatch independently rechecks authorization so stale discovery cannot invoke a
hidden, removed, or rebound capability.

Operator enablement, principal policy allowance, and exact-call approval are
independent conditions. Approval comes from a trusted local authority outside
the model/plugin request path and is single-use, short-lived, and bound to the
principal, session, qualified capability, public binding, runtime generation,
policy revision, Tool schema, trusted effect, and complete arguments after host
compatibility normalization. Replay, expiry, cancellation, denial, or any
mismatch fails before plugin invocation. Model-provided consent fields,
session-wide approval, auto-approval, and wildcard permission do not satisfy this
contract.

A host-owned bounded security audit records controlled authentication, policy,
approval, dispatch, generation, worker, lifecycle, and purge outcomes. Plugins
cannot write, suppress, or forge it. Audit records omit request arguments,
results, memory queries/content/metadata, headers, paths, environment values,
credentials, approval display text, raw request IDs, plugin output, exception
text, and tracebacks. Audit unavailability never broadens authorization; every
effect-sensitive pre-execution failure mode is explicitly fail-closed.

## Relationship to MCP ecosystem formats

The MCP specification exposes one flat endpoint Tool list. It does not currently
standardize composition of multiple in-process plugins behind one server. MyMCP
therefore needs an internal qualified identity and binding model while continuing
to publish ordinary MCP Tool definitions.

The official MCP Registry `server.json` describes a discoverable MCP server and
its packages or remote endpoints. MCPB packages one independently launchable
local MCP server for client installation. Both are whole-server distribution
formats, not MyMCP's native plugin-author or external-worker boundary.

MyMCP may later be published through the Registry or packaged as MCPB as one
server. Its native external plugin is instead a prebuilt Python wheel with inert
MyMCP metadata, a managed immutable dependency closure, and an isolated worker.
MyMCP reuses useful ecosystem concepts—stable machine identity, separate display
metadata, explicit versions, and compatibility—but does not adopt MCPB commands,
user configuration, or Registry package/remotes as its plugin format.

## Deliberate boundaries and deferrals

Permanent boundaries are that MCPB is not the native plugin format; unknown
external code is never imported into the host process; manifest claims never
grant authority; plugins never receive shell execution, ambient host secrets,
unrestricted filesystem/network access, or ownership of flat public bindings;
and separate external plugins never share one dependency environment.

Replaceable implementation choices deliberately remain deferred: the concrete
wheel installer and lock representation, worker framing and IPC library,
platform sandbox backend and quota values, signing PKI and publisher trust,
secret provider, live-reload control surface, reversible data-snapshot format,
Resources and Prompts after host API v1, cross-plugin dependencies, and reusable
host services before a second real plugin proves them generic. Marketplace or
network download, source formats/builds, and broader distribution mechanisms are
outside the initial native contract and current roadmap; considering them later
requires a new threat analysis and explicit API/architecture decision rather
than weakening v1 implicitly. Multi-user, remote-trust, and distributed
operation remain out of scope.

References reviewed for this design:

- [MCP Tools specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [Official MCP Registry](https://github.com/modelcontextprotocol/registry)
- [Official MCPB project](https://github.com/modelcontextprotocol/mcpb)

## Incremental delivery

The architecture is delivered in dependency order. A roadmap phase may require
multiple Tracks; each Track remains a coherent TDD unit.

### Architecture baselines

TRACK_029 records this target and aligns project documentation and the living
roadmap. TRACK_030 corrects its bundled-only external-author assumptions, makes
the MyMCP public-host cutover mandatory, and adds the native distribution,
activation, lifecycle, gateway, and version end-state requirements. Neither
Track changes runtime behavior.

### Phase 1 — Kind-qualified runtime foundation (implemented by TRACK_031)

Implement generic contracts before moving Mnemosyne:

1. versioned plugin identity and Tools-only capability-kind models;
2. qualified capability identity and origin metadata;
3. trusted effect and consent dimensions;
4. explicit public-name bindings and collision validation;
5. immutable `HostRuntime` and explicit bootstrap; and
6. transport-neutral MCP/runtime injection and removal of ordinary-import
   production composition.

TRACK_031 establishes this generation-ready logical seam and a trusted Mnemosyne 0.1.0
adapter over canonical registrations. It does not freeze that callable as the
external execution ABI. The public Mnemosyne 0.1.4 surface is preserved.

### Phase 2 — Definition, manifest, and built-in packaging

Implementation is delivered by TRACK_032 and TRACK_033.

Make Mnemosyne the first complete implementation of the contract:

1. **Delivered:** strict shared definition/manifest parsing and exact selected
   contribution parity;
2. **Delivered:** package and validate Mnemosyne's complete inert manifest,
   including wheel inclusion;
3. **Delivered:** move Mnemosyne MCP adapters under
   `mymcp/plugins/mnemosyne/mcp/`;
4. **Delivered:** move configuration under the same plugin boundary;
5. **Delivered:** move the canonical memory package under
   `mymcp/plugins/mnemosyne/memory/`;
6. **Delivered:** update import-boundary and compatibility tests; and
7. **Delivered:** remove transitional locations and any temporary re-exports.

Startup remains explicit, static, and in-process throughout this phase. The
packaged manifest remains inert; explicit host bootstrap imports the trusted
bundled adapter and performs composition.

### Mandatory compatibility cutover — MyMCP public host

**Local candidate delivered:** endpoint/server, FastAPI application, package,
and tracked official client identity are MyMCP/`mymcp` `0.2.0`, preserving every
Mnemosyne plugin, Tool, configuration, storage, record, logging, and consent
identity. The canonical repository target is `https://github.com/flyset/MyMCP`.
Repository rename, operational reconnect/direct approval checks, and tag/release
publication remain pending. This gate must fully complete before external
activation or gateway operation.

### Phase 3A — Native installation

Implement inert wheel inspection, exact artifact/dependency receipts, immutable
managed environments, validated ordinary configuration and secret references,
persisted bindings and desired installation/enablement state. Installation alone
grants no execution authority and does not alter the active runtime.

### Phase 3B — Isolated external activation

Implement the documented local unknown-code threat model, versioned worker
protocol, supervision, killability, deadlines/cancellation, resource limits,
minimal environment, and default-deny filesystem/network controls. No unknown
external plugin becomes active before this gate passes on the running platform.

### Phase 3C — Generation lifecycle

Implement complete runtime-generation staging/publication/drain,
required/optional failures, disablement, health/quarantine, update/rollback and
data-migration rules, remove/preserve, and separately approved purge. Candidate
failure leaves the active generation unchanged, and in-flight calls remain
pinned to their selected execution and policy context.

### Phase 4 — Client-neutral governance gateway

Add authenticated local client principals and sessions, immutable policy
revisions, policy-filtered discovery and dispatch, host-verifiable single-use
exact-call approval, and bounded content-free security audit behind one
machine-local endpoint. Validate at least two principals with distinct policies.
Do not make one AI client or bundle format the architectural boundary.

### Phase 5 — Reusable host services

Generalize approval, audit, storage, or other mechanisms only after a second real
plugin proves the requirement is shared. Mnemosyne's memory taxonomy remains
plugin-owned.

## Definition of architectural completion

The target is reached when:

- the endpoint, application, repository/distribution metadata, and official
  client identify the host as MyMCP;
- generic host packages contain no Mnemosyne implementation or memory policy;
- all Mnemosyne production implementation is under
  `mymcp/plugins/mnemosyne/`;
- Mnemosyne uses the shared logical definition, manifest, capability, and
  activation contract while retaining its trusted bundled adapter;
- one immutable runtime generation retains plugin, kind-qualified capability,
  effect/consent, artifact, and public-binding identity;
- authenticated session/dispatch context separately pins the applicable policy
  revision to that runtime generation;
- bootstrap is explicit and no ordinary package import starts the process;
- native external wheels are inspected and installed without executing code or
  mutating the host interpreter;
- unknown external code runs only through the approved supervised isolated
  worker boundary with default-deny authority and reliable killability;
- lifecycle publication, failure, update/rollback, removal/preservation, and
  purge semantics are complete;
- authenticated principal policy, exact-call approval, and bounded security
  audit are server-enforced;
- public Mnemosyne Tool, configuration, storage, and record compatibility remain
  validated; and
- reusable host services arise only after a second real plugin proves them
  domain-neutral.

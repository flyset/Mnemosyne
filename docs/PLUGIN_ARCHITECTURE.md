# MyMCP Plugin Architecture

> Status: approved target with the TRACK_031 Phase 1 foundation and implemented
> Phase 2 declaration/parity and bundled Mnemosyne extraction, plus the delivered
> schema-1 host-configuration foundation and delivered Phase 3 external startup
> composition. This document distinguishes the current extracted bundled-plugin
> and trusted external startup-composition boundaries from deferred gateway governance and public
> metadata projection. TRACK_034 delivered the MyMCP/`mymcp` `0.2.0` public-host
> release. Repository migration and operational checks are complete; the public,
> non-draft, non-prerelease GitHub release is tagged `mymcp-v0.2.0` at `c2852bc`.
> See
> [`ARCHITECTURE.md`](ARCHITECTURE.md) for the current code organization.
> TRACK_042 delivers MyMCP 0.5.0's Authentication contract/routing/principal
> foundation and host configuration schema 3. TRACK_043 delivers MyMCP 0.6.0's
> `operator-bearer-v1` registered adapter and host configuration schema 4 while
> retaining Authentication contract v1. TRACK_045 delivers MyMCP `0.7.0`, schema
> 5 OAuth integration, conditional RFC 9728 protected-resource metadata, and the
> OAuth-only Bearer challenge. TRACK_046 delivers MyMCP `0.8.0` process-local,
> registered-principal MCP session context under protocol `2025-11-25`; Governance
> policy, approval, and audit remain later Phase 4 Tracks.

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
  runtime generation; and
- immutable XDG-selected host configuration, loopback packaged-launcher settings,
  and ordered external-plugin declarations; and
- schema-2 enabled-external manifest preflight, ordered zero-argument
  `mymcp_plugin_v1` loading, parity validation, and complete runtime composition.

Released `0.2.0` identifies the host endpoint/application, package,
and tracked official OpenCode connection/agent as MyMCP/`mymcp`. Its tracked
policy denies `mymcp_*` first, allows four read-only Tools, and asks for five
exact mutations. The canonical repository target is
`https://github.com/flyset/MyMCP`, and the former URL redirects there.
Repository/origin/history/tag/placeholder verification, tracked and ignored
OpenCode migration with Claude exclusion, normal endpoint/client reconnect, and
isolated approved-once and rejected/no-Tools-call checks are complete. The
public release is available at
<https://github.com/flyset/MyMCP/releases/tag/mymcp-v0.2.0>.
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

The delivered architecture is a generic host, coherent bundled plugin
implementations, and startup composition for operator-installed trusted external
plugins. Bundled and
configured external plugins share logical manifest, identity, capability,
configuration, definition/contribution, and host-owned binding semantics.
Configuring an external plugin is an operator trust decision, not a request for
MyMCP to evaluate that plugin's safety.

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
    configuration.py              # schema-1 through schema-5 startup intent and source safety
    runtime.py
    bootstrap.py
    authentication.py            # production Authentication composition
    mcp_application.py           # principal/session MCP application seam
    sessions.py                  # bounded process-local session lifecycle
    gateway.py                   # future policy and approval
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

  authentication/                # host-owned contract v1, exact router, and adapters
    contracts.py
    router.py
    adapters/
      operator_bearer.py          # transport-neutral operator-bearer-v1 method
```

The exact implementation may add narrow `__init__.py` files and tests, but it
must preserve these ownership boundaries. Repository documentation, tests,
explicit bootstrap references, compatibility bindings, operator-managed external
plugin software, and user data are not bundled Mnemosyne implementation logic and
remain outside the plugin directory.

External plugin installation, dependency management, Python environments,
configuration, upgrades, rollback, and process operation are the operator's
responsibility. MyMCP does not define a native wheel installer or worker format.
At server start, the host preflights all enabled schema-2 inert metadata and
compatibility before importing any external implementation. It then imports each
trusted implementation in configuration order and validates complete definitions,
contributions, and public bindings before runtime construction. MyMCP does not
sandbox, supervise, restrict, kill, or resource-control configured plugins.

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
bounded immutable contracts for manifests, definitions, kind-qualified
capability identity, effect and consent metadata, public bindings,
configuration and data declarations, validation, and composition.

Host API v1 is Tools-only. It describes the logical Tool surface and composition
rules; it does not specify a plugin process model, sandbox, worker protocol,
health protocol, cancellation, drain, or shutdown contract.

The contract package does not install software, manage environments, grant
authority, assess code safety, store secrets, or contain a concrete plugin.

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

It contains no Mnemosyne-specific policy or artifact identity. External startup
composition is delivered. The metadata is retained so later
gateway policy can reason about origin and effect without redesigning Tool
identity or treating a public name as authorization identity.

`mymcp/host/bootstrap.py` is the only generic-host module permitted to import
concrete bundled plugin adapters. Current bootstrap uses one explicit,
source-controlled Mnemosyne contribution, preflights all enabled schema-2
external manifests before any import, and then imports validated external
modules in configuration order. Bootstrap performs no host-managed installation, network or
marketplace discovery, or runtime activation/switching.

Application assembly constructs the runtime explicitly. Importing an ordinary
`mymcp` package or submodule must not compose the production runtime as a side
effect in the target architecture.

Future composition may own validated ordinary configuration and persisted public
bindings. The gateway owns local principals, sessions, policy, and approval; the
audit layer owns bounded security records. These mechanisms remain domain-neutral
and never absorb Mnemosyne memory policy. They do not make configured plugin code
safe or restrict its host-process authority.

### Bundled plugins

`mymcp/plugins/` is plural because it contains concrete source-controlled
implementations. Every bundled plugin follows the shared logical author
contract. Built-in status grants reviewed host-process authority, not a claim of
sandboxing.

`mymcp/plugins/mnemosyne/` owns all Mnemosyne production meaning:

- manifest and plugin contribution;
- `MNEMOSYNE_*` and `~/.mnemosyne/config.toml` configuration;
- memory scopes, records, policy, retrieval, lifecycle, and persistence;
- every `memory_*` Tool definition and handler; and
- lazy memory-root, store, and service composition.

Mnemosyne may use generic host plugin and MCP contracts. It may not import HTTP
routes, application assembly, host bootstrap, or another plugin.

### Configured external plugins

An external plugin is software the operator has independently installed and
configured for the server environment. The operator selects its distribution,
dependencies, Python environment, configuration, updates, rollback, and process
start/stop/restart procedure. MyMCP does not prescribe a wheel closure, managed
environment, installer receipt, worker entry point, or isolated-worker format.

The delivered host composition phase validates every enabled schema-2 inert
manifest—host-API compatibility, identities and versions, and declared
capabilities—before any external implementation import. It then loads each
trusted implementation in configuration order and validates its definition,
selected contribution, and public bindings before constructing the runtime.
Passing those checks establishes only a compatible
composition. It does not establish provenance, safety, authority restriction, or
a sandbox. The configured plugin may run in the host process with the authority
available to that process.

## Identity and version model

Several identities must remain separate:

| Dimension | Owner | Compatibility and evolution rule | Target example |
| --- | --- | --- | --- |
| MyMCP distribution version | MyMCP release | Semantic package/release evolution; it does not version a plugin or generation | `0.8.0` |
| Endpoint/server identity and marker | MyMCP endpoint | Public compatibility marker, normally equal to the release version but changed only through an explicit endpoint migration | `mymcp 0.8.0` |
| MCP protocol version | MCP specification and endpoint negotiation | Session-negotiated independently of plugin APIs | supported MCP revision |
| Host plugin API | MyMCP | Integer logical-contract level; incompatible manifest, definition, or composition semantics require a new level | `1` |
| Manifest schema | MyMCP | Strict integer shape; unsupported versions fail closed | `1` |
| External plugin-author contract | MyMCP | Versioned external module entrypoint contract, separate from host API and manifest schema | `1` (`mymcp_plugin_v1`) |
| Host configuration schema | MyMCP | Strict host startup-document shape; schemas 1–2 retain plugin compatibility, schema 3 adds Authentication intent, schema 4 adds operator-bearer verifier-source metadata, and schema 5 adds OAuth issuer intent | `1`, `2`, `3`, `4`, `5` |
| Authentication contract | MyMCP | Host-owned principal/evidence/adapter-result/routing compatibility, independent of MCP and plugin APIs | `1` |
| Authentication adapter type | MyMCP | Stable concrete method identity, separate from the Authentication contract and route | `operator-bearer-v1` or `oauth-jwt-jwks-v1` |
| Operator bearer verifier-source format | MyMCP | Strict separately sourced verifier snapshot shape, independent of host configuration and Authentication contract versions | `1` |
| Plugin identity | Plugin author, admitted by MyMCP | Stable machine identity excluding version | `mnemosyne` |
| Plugin version | Plugin author | Semantic implementation release agreeing across manifest, definition, and contribution | Mnemosyne `0.3.0` |
| Capability kind and local ID | Plugin author, validated by MyMCP | Stable identity excluding version; host API v1 admits only `tool` | `tool`, `memory_recall` |
| Capability contract version | Plugin author | Semantic compatibility of one capability schema/result contract | Mnemosyne `memory_recall` `1.2.0` |
| Configuration schema | Plugin author | Explicit version validated during startup composition | `1` |
| Plugin-data schema | Plugin author | Plugin-owned durable-data compatibility version | `1` |
| Memory record schema | Mnemosyne plugin author | Persisted record compatibility; legacy sources remain readable without invented migration | `1`, `2` |
| Policy revision | MyMCP gateway | Immutable authorization snapshot; affected sessions and approvals become stale under defined policy changes | opaque revision |
| Runtime generation | MyMCP runtime | Opaque unique publication identity, never reused or interpreted as semantic compatibility | opaque generation ID |
| Endpoint-visible Tool name | MyMCP binding policy | Flat binding independent of qualified identity and plugin claims | `memory_recall` |

These values may coincide, but compatibility is never inferred from coincidence.
Identity excludes version. The MCP protocol, host API, manifest, plugin,
capability, configuration, plugin-data, policy, and runtime-generation
dimensions solve different problems and are validated independently. Existing
Mnemosyne record schema versions remain plugin-owned.

Current bundled Mnemosyne declares its plugin version as `0.3.0` and each
capability version explicitly: `memory_recall` is `1.2.0`; the other seven
`memory_*` capabilities are `1.1.0`. MyMCP's host/package/endpoint marker is
independently `0.8.0`. Bundling does not merge host, plugin, or capability version
ownership. A test-owned, version-keyed canonical-JSON Tool-definition
digest ledger couples each declared capability version to a SHA-256 digest and
readable properties/required-field fingerprints, preserving historical entries
for review. It guards declared Tool definitions only. It cannot determine changes
to handler result/error behavior or infer a missed increment, so behavioral tests
and the required explicit version-impact review remain necessary.

The host-controlled product, endpoint, FastAPI application, distribution
metadata, and tracked official client identity are MyMCP in released `0.2.0`.
The existing `0.1.x` line is the prior Mnemosyne-public-host compatibility era.
Repository migration, operational validation, and release publication are
complete. External startup composition is delivered; gateway operation remains a
later gate.

| Public-host dimension | Prior `0.1.x` era | Released `0.2.0` |
| --- | --- | --- |
| Product, distribution, package, commands | MyMCP; `mymcp`; `mymcp*` commands | MyMCP; `mymcp`; `mymcp*` commands; package version `0.2.0` |
| MCP server machine name | `mnemosyne` | `mymcp` |
| FastAPI application title | `Mnemosyne MCP Server` | `MyMCP` |
| Canonical repository | `flyset/Mnemosyne` | `https://github.com/flyset/MyMCP` (former URL redirects; [release](https://github.com/flyset/MyMCP/releases/tag/mymcp-v0.2.0) published) |
| Official client and agent key | `mnemosyne` | `mymcp` |
| Client-generated permission prefix | `mnemosyne_*` | `mymcp_*` |
| Routes and host Tool | `/mcp`, `/health`, `/version`, `list_tools` | Preserve |
| Mnemosyne identity | plugin `mnemosyne`, `memory_*`, `MNEMOSYNE_*`, `~/.mnemosyne`, memory formats and paths | Preserve |

The released endpoint marker changed from `mnemosyne 0.1.x` to `mymcp 0.2.0`
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
connection key and are not host binding inputs. The tracked released configuration uses
official key `mymcp` and `mymcp_*` permission names; endpoint-visible `memory_*`
names do not change. Direct operational approval checks are complete.

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

Each bundled plugin contains one strict `manifest.json`. Each enabled schema-2
configured external plugin supplies an equivalently strict inert manifest at its
configured absolute path, without a prescribed distribution format or
host-managed installation location.
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
- allows startup composition validation to fail before implementation loading
  where possible.

Unknown fields, invalid identities or versions, unsupported capability kinds,
duplicate local identities, unsupported host API intervals, undeclared
activations, inconsistent effect/consent/configuration/data/authority metadata,
and invalid selected subsets are rejected with no partial runtime.

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
- health, update, removal, restart, or lifecycle metadata; or
- a memory-data index, manifest, migration ledger, backup, or tombstone.

Tool schemas remain derived from the plugin's canonical domain definitions and
runtime registrations. Mnemosyne's JSON memory files remain its storage source
of truth.

## Plugin definition and startup composition

The immutable `PluginDefinition` contracts, strict manifest parser, and parity
validation are implemented for bundled and configured external plugins. Startup
composition preserves these invariants:

- `PluginDefinition` is immutable data that exactly agrees with the selected
  manifest's identity, compatibility, complete capability metadata,
  configuration shape, secret slots, data version, and requested authority;
- it contains no handler, command, import, secret, open resource, running task,
  ambient host object, or registry mutation capability;
- selected definitions and invokers remain paired, and disabled capabilities do
  not enter discovery or dispatch;
- startup validates inert manifest metadata before loading implementation code
  where possible, then validates definitions, selected contributions, and public
  bindings before runtime construction; and
- invalid composition produces a clear startup failure and no runtime.

There is no target `PluginContext`, plugin activation protocol, health protocol,
deadline/cancellation contract, drain, shutdown, or worker adapter. Once the
operator configures a compatible external plugin, its implementation is trusted
to run in process. Its safety and operational lifecycle remain the operator's
responsibility.

## Bootstrap and composition

Startup composition is explicit and in-process:

1. Bootstrap validates the immutable host snapshot and schema-1 bundled-ID
   compatibility.
2. It preflights every enabled schema-2 external manifest in configuration order
   before any external module import, enforcing source safety, manifest parsing,
   configured identity, host API, and plugin/capability limits.
3. It validates the fixed packaged Mnemosyne manifest, definition, and selected
   contribution.
4. It imports enabled external modules in configuration order; each zero-argument
   `mymcp_plugin_v1` entrypoint returns a `PluginAdapter`.
5. It validates every external manifest/definition/contribution parity contract.
6. It binds bundled Mnemosyne first, then external capabilities in configuration
   and capability order using `<plugin-id>__<tool-local-id>` defaults.
7. Duplicate plugin IDs, qualified capabilities, reserved names, bindings, or
   public names fail composition; host-owned `list_tools` is bound only to the
   complete surface.
8. One immutable `HostRuntime` generation is constructed and used until restart.

Any failure returns no partial runtime. Bootstrap performs no host-managed
installation, dependency/environment management, network or marketplace
discovery, hot activation, or runtime switching.

Mnemosyne continues to resolve immutable mutation gates once during startup and
the memory root lazily after Tool-specific validation for each operation.

## Dependency rules

| Owner | May depend on | Must not depend on |
| --- | --- | --- |
| `mymcp/routes/` | FastAPI, transport-neutral MCP handling, composed runtime | plugin domains or plugin configuration |
| `mymcp/mcp/` | standard library, generic runtime contracts | FastAPI in target protocol modules, concrete plugins, Mnemosyne domain/configuration |
| `mymcp/plugin/` | standard library, generic MCP registration types | concrete plugins, routes, plugin configuration, installation or supervision |
| `mymcp/host/runtime.py` | generic plugin composition and MCP registry | concrete plugins or domain policy |
| `mymcp/host/bootstrap.py` | generic runtime, explicit bundled adapters, and validated configured external manifests/adapters | dynamic network/marketplace discovery or runtime composition switching |
| `mymcp/host/gateway.py` | runtime identity, principals, sessions, policy, approval verification | plugin policy claims as authority, Mnemosyne domain policy |
| `mymcp/host/audit.py` | bounded host security-event contracts and private persistence | request/result content, plugin-writable records |
| Mnemosyne `plugin.py` | generic plugin/MCP contracts and its own packages | routes, app assembly, host bootstrap, other plugins |
| Mnemosyne `mcp/` | generic MCP contracts and Mnemosyne memory types | FastAPI, routes, concrete host startup, other plugins |
| Mnemosyne `memory/` | standard library and its own modules | MCP, host, routes, FastAPI, other plugins |
| Mnemosyne `configuration.py` | standard library | MCP, host settings, routes, FastAPI, other plugins |

Only bootstrap may point from generic host code to a concrete bundled plugin.
Configured external code is loaded only after inert compatibility preflight;
definition/contribution parity and composition validation then complete before a
runtime is published. Plugins may not import one another. A host
service may not absorb Mnemosyne taxonomy or policy
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

The release completes the mandatory separate public-host identity
migration. It changes server/application,
package, and official tracked-client identity from Mnemosyne to MyMCP in the
first `0.2.0` build while preserving the plugin compatibility list above. Client
connection-key and permission-prefix changes are atomic so no mutation Tool
becomes callable under a new prefix without its exact approval rule. Restart/
reconnect and direct discovery, denial/no-call, and exact-call approval checks,
plus repository migration, and release publication are complete. There is no duplicate
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

For a configured external plugin, the operator independently chooses to trust
the code. Delivered startup validation checks compatibility and composition, not
whether the code is benign. After it passes, the plugin may run in process with
the authority available to the host process. MyMCP makes no sandbox, isolation,
filesystem/network restriction, worker supervision, killability, or resource
control guarantee. It does not issue artifact receipts or make installation,
dependency, environment, update, rollback, stop, or restart decisions for the
operator.

MCP recommends human confirmation for sensitive operations but does not provide
the server cryptographic proof that a client displayed an approval prompt.
Effect and consent metadata therefore establish a trusted policy floor but do
not manufacture consent.

## Configuration and plugin-owned data

MyMCP 0.8.0 supports host configuration schemas 1–5. Schema 1 remains an
exact immutable desired-state contract: an enabled declaration fails with
`enabled_plugin_unsupported`. Schema 2 explicitly adds an absolute manifest
path and dotted module locator to every declaration, including disabled ones.
It does not normalize, expand, fall back, or autodiscover locators. Enabled
schema-2 manifests preflight as a complete ordered set before any import, then
each zero-argument `mymcp_plugin_v1` entrypoint returns a `PluginAdapter` for
parity validation and composition. Schema 3 preserves schema-2 plugin fields and
requires explicit anonymous access plus bounded Authentication adapter
declarations. Schema 4 preserves schema-3 syntax and adds the exact non-secret
operator-bearer `verifier_path` selector, required with any
`operator-bearer-v1` declaration. Schema 5 adds the exact non-secret OAuth
`issuer` table, required with any `oauth-jwt-jwks-v1` declaration, including a
disabled declaration, and prohibited otherwise. OAuth and operator bearer cannot
be co-declared in schema 5; enabled OAuth requires anonymous access disabled,
claims the same exact `(authorization, bearer, null)` route, and obtains one
immutable validation snapshot before plugin runtime construction. The production
operator adapter claims only exact
`(authorization, bearer, null)` evidence and loads its complete protected verifier
snapshot before plugin runtime construction. Authentication contract v1 and
schemas 1–3 remain unchanged. Enabled unavailable types fail before plugin
composition.
See [Configuration](CONFIGURATION.md) for the
complete operator contract.

The operator remains
responsible for external plugin installation, dependencies, Python environment,
configuration, updates, rollback, and server process operation. The host does
not create managed environments, issue installation receipts, provide plugin
sandboxes, or take ownership of plugin data.

Mnemosyne is a deliberate compatibility adaptation: its bundled adapter retains
the existing `MNEMOSYNE_*`, `~/.mnemosyne/config.toml`, and
`~/.mnemosyne/memory` contracts. Extraction and host cutover do not relocate or
duplicate its configuration or data.

## Startup composition and runtime-generation identity

`HostRuntime` is immutable for one server start and carries an opaque,
per-start runtime-generation identity. That identity distinguishes the composed
runtime used by dispatch and can support later gateway authorization binding; it
is not a plugin lifecycle system or compatibility version.

Plugin additions, removals, configuration changes, upgrades, rollback, and
stopping or restarting take effect only through operator action and a server
restart. MyMCP provides no runtime install, hot activation, generation
publication/switching/drain, quarantine, or host-managed update/rollback
lifecycle. Startup either composes one complete valid runtime or fails clearly;
it does not partially publish a composition.

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
approval, dispatch, and runtime-generation outcomes. Plugins
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
formats, not MyMCP's native plugin-author format.

MyMCP may later be published through the Registry or packaged as MCPB as one
server. MCPB is not the native MyMCP plugin format. MyMCP reuses useful ecosystem
concepts—stable machine identity, separate display metadata, explicit versions,
and compatibility—but does not adopt MCPB commands, user configuration, or
Registry package/remotes as its plugin format.

## Deliberate boundaries and deferrals

Permanent boundaries are that MCPB is not the native plugin format; manifest
claims never grant authority; plugins do not own flat public bindings; and
MyMCP does not promise shell, filesystem, network, environment, process, or
resource restrictions for operator-trusted in-process plugin code.

Resources and Prompts after host API v1, cross-plugin dependencies, and reusable
host services before a second real plugin proves them generic remain deferred.
Marketplace distribution, host-managed installation, and plugin isolation are
outside the current roadmap. Multi-user, remote-trust, and distributed operation
remain out of scope.

References reviewed for this design:

- [MCP Tools specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [Official MCP Registry](https://github.com/modelcontextprotocol/registry)
- [Official MCPB project](https://github.com/modelcontextprotocol/mcpb)

## Incremental delivery

The architecture is delivered in dependency order. A roadmap phase may require
multiple Tracks; each Track remains a coherent TDD unit.

### Architecture baselines

TRACK_029 records the original target and aligns project documentation and the
living roadmap. TRACK_030 corrects its bundled-only external-author assumptions
and makes the MyMCP public-host cutover mandatory. The current target supersedes
the former native-distribution and lifecycle direction with trusted external
startup composition, gateway, and version end-state requirements. Neither Track
changes runtime behavior.

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

**Released:** endpoint/server, FastAPI application, package,
and tracked official client identity are MyMCP/`mymcp` `0.2.0`, preserving every
Mnemosyne plugin, Tool, configuration, storage, record, logging, and consent
identity. The canonical repository target is `https://github.com/flyset/MyMCP`.
Repository migration and operational reconnect/direct approval checks are
complete, and the public release is tagged `mymcp-v0.2.0` at `c2852bc`. This
gate is complete before external startup composition or gateway operation.

### Phase 3 — Startup composition for trusted external plugins (delivered by TRACK_041)

Schema 1 preserves the bounded unsupported-enabled state. Schema 2 provides
validated external composition in explicit bootstrap: preflight all enabled
inert manifests before any implementation import; validate host API,
identities/versions, source safety, and 32-plugin/256-capability limits; then
load trusted implementations and validate definitions, contributions, and public
binding collisions before runtime construction. External bindings use
`<plugin-id>__<tool-local-id>`; bundled plugins precede configuration-order
externals, which retain capability order. Invalid composition fails startup
clearly with no partial runtime.

External plugin installation, dependency management, Python environments,
configuration, updates, rollback, and process stop/restart remain the operator's
responsibility. A configured plugin is trusted to execute in process after
validation. This phase provides no host-managed installer, runtime install, hot
activation, generation switching/drain, quarantine, update/rollback lifecycle,
worker protocol, sandbox, filesystem/network restriction, supervision,
killability, or resource-control guarantee.

### Phase 4 — Client-neutral governance gateway

**Track 1 delivered by TRACK_042:** MyMCP 0.5.0 provides Authentication contract
version 1, normalized namespaced principals, exact evidence routing, independent
anonymous admission, host configuration schema 3, and the principal-aware MCP
application seam. **Track 2 delivered by TRACK_043:** MyMCP 0.6.0 adds the
`operator-bearer-v1` registered-principal proof and schema 4 without changing the
Authentication-v1 principal, evidence, routing, anonymous-admission, or canonical
identity contracts.

Continue by adding authenticated local client adapters and sessions, immutable policy
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
- Mnemosyne uses the shared logical definition, manifest, and capability
  contract while retaining its trusted bundled adapter;
- one immutable runtime generation retains plugin, kind-qualified capability,
  effect/consent, and public-binding identity;
- authenticated session/dispatch context separately pins the applicable policy
  revision to that runtime generation;
- bootstrap is explicit and no ordinary package import starts the process;
- configured external plugins have inert metadata and compatibility validated
  before implementation loading where possible, followed by
  definition/contribution and public-binding validation before runtime
  construction, and invalid composition fails startup clearly;
- documentation makes clear that external plugins are operator-installed and
  operator-trusted in-process code, without host-managed installation,
  lifecycle, isolation, supervision, or resource-control claims;
- authenticated principal policy, exact-call approval, and bounded security
  audit are server-enforced;
- public Mnemosyne Tool, configuration, storage, and record compatibility remain
  validated; and
- reusable host services arise only after a second real plugin proves them
  domain-neutral.

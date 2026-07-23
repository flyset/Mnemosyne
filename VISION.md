# MyMCP Vision

MyMCP is a local, client-neutral MCP host and governance gateway. It should let a
single user run narrowly scoped integrations behind one machine-local endpoint
without surrendering control of Tools, data, or mutation approval to a specific
AI client or plugin author.

MyMCP currently hosts the Mnemosyne user-governed memory domain in-process. The
host/domain boundary is real, but plugin extraction, dynamic loading,
installation, lifecycle management, and isolation are not implemented yet.

## Role

MyMCP owns host-level composition and protocol mechanisms:

- one explicit MCP surface for independent compatible clients;
- stable Tool registration, identity, discovery, and dispatch;
- deterministic composition and collision handling;
- plugin contracts, routing, compatibility, and lifecycle boundaries as they are
  introduced; and
- reusable host governance only after multiple integrations prove it generic.

Domain integrations own their application meaning. Mnemosyne therefore retains
its memory taxonomy, record semantics, retrieval, lifecycle policy, public
`memory_*` Tools, configuration, and storage identity.

## Current Foundation

The repository already provides the MyMCP distribution and top-level Python host
package, a generic immutable Tool registry, an explicit Mnemosyne integration and
configuration boundary, and host-owned static ordered integration composition.
The production surface still contains only the built-in Mnemosyne integration.

The next product step is to define the plugin-author contract and Tool identity
rules required before third-party aggregation. Packaging, plugin lifecycle,
isolation, client-neutral gateway policy, and reusable host services follow only
after their prerequisites are explicit.

## Principles

MyMCP should preserve:

- local-first operation and filesystem truth;
- a single-user model until a broader threat model is explicit;
- least privilege and small, explicit Tools;
- client-neutral server-enforced boundaries;
- explicit operator enablement and per-call user consent for mutations;
- deterministic startup and failure rather than hidden discovery or fallback;
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
- a client-specific bundle runtime presented as a universal MCP boundary; or
- a plugin marketplace, loader, or isolation system before those contracts are
  actually implemented and validated.

## Built-in Mnemosyne Domain

Mnemosyne remains the built-in user-governed memory domain and the current public
server identity. Its notebook model, safety contract, and domain-specific
direction are preserved in [the Mnemosyne vision](docs/MNEMOSYNE_VISION.md).

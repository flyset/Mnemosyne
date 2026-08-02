# Authentication Architecture

## Purpose

Authentication is the system layer between the HTTP server and the MCP server.
It converts supported HTTP authentication evidence into one trusted, normalized
client principal or rejects the request.

Authentication answers **who the client is**. Governance decides what that
principal may do.

This document defines the approved architecture. Authentication is not yet
implemented.

## Adapter Model

MyMCP uses host-owned Authentication adapters so authentication methods remain
isolated from MCP, Governance, the plugin runtime, plugins, and plugin data.

Host configuration enables zero or more named adapter instances and separately
controls whether requests without authentication evidence may use anonymous
access. Configuration is validated into one immutable startup snapshot and
changes require restart.

Each adapter instance has one stable, host-assigned configuration identity. It:

1. receives only the bounded HTTP evidence and request context its method needs;
2. validates that evidence according to its method;
3. returns one bounded adapter-local subject on success; or
4. returns an authentication failure without invoking MCP handling.

A host-owned Authentication router classifies submitted evidence and invokes
exactly one matching adapter. Evidence formats and enabled adapter instances must
be unambiguous. The router never tries adapters sequentially and never falls back
from failed evidence to another adapter or to anonymous access.

Authentication adapters are not Tool plugins and are not part of the Tools-only
plugin-author contract. They hold upstream security authority and use a separate
host-owned boundary.

## Anonymous Access

Anonymous is a configurable access mode, not an Authentication adapter.

Request handling follows these rules:

1. Submitted authentication evidence must route unambiguously to one enabled
   adapter and pass that adapter's validation.
2. Malformed, ambiguous, unsupported, or rejected evidence fails authentication
   and never becomes anonymous.
3. A request with no authentication evidence becomes anonymous only when host
   configuration explicitly enables anonymous access.
4. A request with no evidence is rejected when anonymous access is disabled.

## Normalized Principal

Authentication constructs the canonical principal; clients and adapters cannot
assert it directly.

Conceptually, downstream layers receive:

```text
principal_kind: anonymous | registered
principal_adapter: <stable adapter identity> | null
principal_subject: <adapter-local stable subject> | null
principal_id: <canonical host-constructed identity>
```

Anonymous has null adapter and subject values and the fixed canonical identity
`anonymous`.

A registered principal has one configured adapter identity and one validated
adapter-local subject. The host constructs a collision-free canonical identity
using both values, conceptually:

```text
<principal-adapter>:<principal-subject>
```

The exact identity grammar and delimiter rules must prevent ambiguity and are
versioned host contracts. No principal field contains a credential, token,
authorization header, raw OAuth claim set, certificate, or other secret.

## Downstream Contract

The MCP server may carry trusted principal context through protocol handling but
does not interpret authentication protocols.

Governance may use principal kind, stable adapter identity, adapter-local
subject, and canonical principal identity in ACLs. It receives no credentials or
raw protocol claims and does not invoke Authentication adapters.

Adapter identity is a stable policy namespace, not an executable module, class,
package, or client-supplied method name. Different adapters may intentionally map
similar subject text to distinct canonical principals without collision.

The plugin runtime, plugins, and plugin data or external services receive no
authentication credential or adapter capability. They receive only calls that
have passed the upstream Authentication and Governance boundaries.

## Planned Adapters

### Operator-provisioned bearer credential

Validates a credential provisioned by the operator and returns one stable
adapter-local subject. Its provisioning, evidence format, verifier storage,
rotation, revocation, and client-support contracts require a bounded Track.

### External OAuth

Validates access tokens issued by a configured external authorization server and
returns one stable adapter-local subject. MyMCP remains the protected resource;
the external service owns client registration, user authorization, authorization
codes, token issuance, refresh, and provider-side revocation. Its discovery,
issuer, resource, validation, availability, and failure contracts require a
separate bounded Track.

### Future adapters

Another method may be added only through an explicit architecture and Track
decision. It must use the same router and normalized-principal contracts without
changing MCP, plugin runtime, plugins, or plugin data.

## Layer Responsibilities

### HTTP server

- Receives HTTP traffic and extracts bounded authentication evidence.
- Returns the approved HTTP authentication outcome.
- Owns no credential verification, principal construction, MCP meaning, or
  Governance policy.

### Authentication

- Owns configured adapter instances, evidence routing, validation, optional
  anonymous access, and canonical principal construction.
- Rejects invalid or unsupported evidence before MCP handling.
- Owns no Tool authorization or plugin behavior.

### MCP server

- Owns MCP and JSON-RPC meaning.
- Carries trusted principal context without parsing authentication protocols.
- Owns no credential, OAuth, certificate, or adapter invocation semantics.

### Governance

- Uses normalized principal fields to select and enforce ACL policy.
- Never receives credentials or invokes adapters.

### Plugin runtime and downstream layers

- Route and execute only calls admitted by upstream boundaries.
- Never authenticate clients or receive client credentials.

## Security Invariants

- Adapter enablement and anonymous access are explicit, startup-fixed host
  configuration.
- Multiple adapters may operate simultaneously only with unambiguous evidence
  routing.
- There is no sequential adapter probing, downgrade, cross-adapter fallback, or
  failed-evidence fallback to anonymous.
- Unsupported clients fail closed rather than weakening configured methods.
- The host assigns adapter identities and constructs canonical principal IDs;
  clients and adapters do not choose policy namespaces.
- MCP `clientInfo`, connection identity, process ID, user agent, request ID, and
  an unverified client ID are not authentication proof.
- Credentials and raw evidence are never exposed to MCP Tools, Governance policy,
  plugins, logs, errors, or durable project memory.
- Authentication establishes principal context, not Tool authority, user
  consent, plugin safety, or process isolation.

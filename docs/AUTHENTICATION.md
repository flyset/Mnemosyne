# Authentication Architecture

## Purpose

Authentication is the system layer between the HTTP server and the MCP server.
It converts supported HTTP authentication evidence into one trusted, normalized
client principal or rejects the request.

Authentication answers **who the client is**. Governance decides what that
principal may do.

MyMCP `0.9.0` retains the contract-version-1 principal, adapter-result,
evidence-routing, configuration, and anonymous HTTP foundation, plus two
alternative production methods: `operator-bearer-v1` and
`oauth-jwt-jwks-v1`. Authentication contract v1 is unchanged. Schema 5 selects
OAuth only from immutable startup configuration and composes one immutable
validation snapshot before the plugin runtime. Authentication establishes
identity plus a method-neutral host session boundary. Authentication contract v1,
adapters, and schemas remain unchanged. Governance, Tool authorization, exact-call
approval, and security audit remain unimplemented.

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

Downstream layers receive:

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
using both values:

```text
registered:<principal-adapter>:<base64url-subject>
```

The subject token is unpadded RFC 4648 base64url of the exact UTF-8 subject.
Adapter IDs exclude the delimiter, making the mapping injective and namespaces
collision-free. No principal field contains a credential, token,
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

## MCP session boundary

Authentication runs before every session lookup; `MCP-Session-Id` is never
Authentication evidence. Under MCP `2025-11-25`, a registered principal's
successful response-bearing `initialize` creates one opaque process-local session
and returns `MCP-Session-Id`. Later registered `/mcp` traffic must repeat exact
singleton session and `MCP-Protocol-Version` headers. Schema 6 may explicitly
permit only an absent protocol header on an already authenticated, validated
registered session; the host then uses that session's immutable negotiated version.
Supplied-header validation and anonymous stateless behavior remain strict. Sessions bind the complete
normalized principal and host runtime generation, are not persisted or shared
across restart, and are unavailable to adapters, generic MCP, plugins, and plugin
data. Anonymous access remains stateless and sends the negotiated
`MCP-Protocol-Version` without a session identifier after initialization. This context establishes no Tool
authority, policy, approval, or mutation consent.

## Delivered operator-provisioned bearer adapter

`operator-bearer-v1` is a host-owned, transport-neutral production adapter. An
enabled declaration must claim exactly `(authorization, bearer, null)` and
returns only a verified stable adapter-local subject; the host still constructs
the registered canonical principal. A route collision fails startup. No bearer
profile is inferred from credential shape and no second adapter is probed.

The accepted evidence is exactly one `Authorization` header with
case-insensitive ASCII `Bearer`, one ASCII space, and this ASCII credential:

```text
mymcp1.<credential-id>.<secret>
```

`credential-id` is exactly 32 lowercase hexadecimal characters. `secret` is
exactly 43 unpadded RFC 4648 base64url characters encoding 32 independently
generated random bytes (256 bits). Leading/trailing whitespace, tabs, Unicode,
empty or extra components, padding, and alternate base64 alphabets are rejected.

The adapter computes SHA-256 over the decoded secret and uses fixed-length
`hmac.compare_digest` verification against a stored 32-byte digest. An unknown ID
performs the same digest calculation and one fixed dummy-digest comparison before
the same bounded rejection. It retains only immutable credential IDs, subjects,
and digests, never plaintext credentials.

### Verifier source, provisioning, and lifecycle

Schema 4 selects one absolute, unexpanded local `verifier_path` in the exact
non-secret `[authentication.operator_bearer]` table. The table contains only that
field and is required whenever an `operator-bearer-v1` declaration exists,
including a disabled one; it is prohibited otherwise. Path shape is always
validated, but the source is accessed only for an enabled declaration.

The source is a complete strict UTF-8 JSON snapshot, at most 16 KiB:

```json
{"format_version":1,"credentials":[{"id":"<32-lowercase-hex>","subject":"<Authentication-v1 subject>","digest":"<43-character-unpadded-base64url-SHA-256>"}]}
```

Format version is `1`; top-level fields are exactly `format_version` and
`credentials`; every record has exactly `id`, `subject`, and `digest`; and at most
32 records are permitted. Duplicate JSON keys, unknown/missing fields, invalid
encoding or lengths, and duplicate IDs fail startup. Multiple IDs may map to one
subject for overlap rotation. The source and immediate parent must be non-link
regular/directory objects; on POSIX neither may be group/world writable and the
source has no group/world permission bits. No-follow and stable-source checks fail
closed if the source changes while read.

Provisioning is external and offline: stop MyMCP, independently generate a
credential and its record digest, deliver the plaintext credential once through a
chosen secure channel, atomically replace the complete protected snapshot, then
restart. To rotate, add a new ID for the same subject and restart; remove the old
ID in a later complete replacement and restart. To revoke, remove the ID and
restart. There is no credential issuance command or API, HTTP/MCP management
endpoint, plaintext TOML or environment setting, merge, revoked marker, runtime
reread, file watch, fallback, or hot revocation.

## Delivered OAuth resource-server method

`oauth-jwt-jwks-v1` is a host-owned, transport-neutral OAuth resource-server
method. Schema 5 requires the exact non-secret `[authentication.oauth_jwt]`
table containing one canonical HTTPS `issuer` whenever an OAuth declaration
exists, including a disabled declaration, and prohibits it otherwise. An enabled
OAuth declaration claims exactly `(authorization, bearer, null)`, requires
`anonymous_enabled = false`, and obtains its metadata/JWKS validation material
once at startup. The resulting snapshot is immutable for the process; key
rotation, removal, or configuration changes require restart.

OAuth and `operator-bearer-v1` claim the same Bearer evidence route because HTTP
cannot safely select a method from token shape. They are mutually exclusive in a
schema-5 document, including disabled declarations. The router still invokes
exactly one configured adapter and never probes, falls back, or turns failed
evidence into anonymous access.

The foundation accepts only a narrow compact RS256 `at+jwt` access-token
contract. It requires strict duplicate-free header and payload JSON, exact
`alg`, `typ`, and keyed RSA verification; exact issuer and audience membership;
required bounded identity and time claims; 30-second clock skew; and a maximum
five-minute lifetime. Unsupported, malformed, ambiguous, incorrectly issued or
targeted, expired, and invalidly signed inputs fail closed. It supports neither
opaque-token introspection, ID tokens, nested or encrypted JWTs, symmetric or
other signing algorithms, token refresh, nor token issuance.

A successful validation returns only the opaque adapter-local subject
`oauth-jwt-v1:` plus the unpadded base64url SHA-256 projection of exact UTF-8
issuer, one zero byte, and exact UTF-8 subject. Raw claims do not cross the
adapter boundary; the host would still construct the canonical principal.

At enabled OAuth startup, the loader derives the RFC 8414
metadata location from one canonical HTTPS issuer and acquires one immutable key
snapshot through exactly two bounded fetches: metadata and its same-origin HTTPS
JWKS. Its concrete transport uses verified certificate and hostname validation,
no environment proxy, no redirects, one deadline, and bounded bodies. The
validator makes no runtime metadata/JWKS refresh, provider call, fallback, or
introspection request. Key rotation and removal require restart; there is no
immediate revocation claim, and a valid token can remain acceptable only through
its bounded expiry.

`PyJWT[crypto]` is isolated to the concrete OAuth validator and supplies only
the RS256 signature-verification primitive after MyMCP has performed strict
parsing and key selection. Authentication principals, failures,
representations, logs, and downstream layers exclude tokens, Authorization
values, claims, keys, issuer/JWKS locations, provider responses, and exception
details.

The canonical OAuth resource and audience derive only from the validated loopback
server address and port: `http://<IPv4>:<port>/mcp` or
`http://[<compressed-IPv6>]:<port>/mcp`. Request `Host` and forwarded headers
never influence either identity. The literal loopback HTTP endpoint is a
deliberate local interoperability exception; it is not RFC-conformant HTTPS or
remote deployment support. Other future methods require an explicit architecture
and Track decision and must preserve the router and normalized-principal contracts
without changing MCP, plugin runtime, plugins, or plugin data.

## OAuth protected-resource discovery and challenge

Only when enabled OAuth is composed, MyMCP serves one GET endpoint:

```text
/.well-known/oauth-protected-resource/mcp
```

It returns exactly `resource`, a one-element `authorization_servers` array, and
`bearer_methods_supported: ["header"]`, with `Cache-Control: no-store`; it has no
scopes or extra fields. No OAuth metadata route exists for anonymous,
operator-bearer, or disabled-OAuth configuration. MyMCP does not host
authorization-server metadata, OpenID Provider metadata, dynamic client
registration, or `/register`.

Every OAuth-protected `/mcp` authentication failure remains a body-free HTTP 401
before streaming, body parsing, MCP logging, or dispatch. It carries exactly
`WWW-Authenticate: Bearer resource_metadata="<derived metadata URL>"`, without
token-derived error detail. Operator-bearer and anonymous-only configurations
retain the existing challenge-free empty 401 behavior.

## Delivered HTTP Boundary

Both `GET /mcp` and `POST /mcp` authenticate before streaming, body parsing, MCP
logging, or dispatch. A submitted Authorization value must be one header with one
ASCII scheme/token pair separated by one ASCII space. For operator bearer, the
scheme must be `Bearer` under ASCII case-insensitive comparison and the token must
meet the exact grammar above. Duplicate headers, empty/malformed/non-ASCII values,
wrong schemes, unsupported routes, and rejected credentials fail closed. Failure
returns HTTP `401` with an empty body and no JSON-RPC envelope. When enabled OAuth
is selected, and only then, the response carries the exact protected-resource
metadata Bearer challenge described above.
Submitted failed evidence never becomes anonymous.

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
- The OAuth method additionally excludes access tokens, claims, keys,
  issuer/JWKS locations, provider responses, and exception details from its
  results, representations, logs, and downstream context.
- Authentication establishes principal context, not Tool authority, user
  consent, plugin safety, or process isolation.

# Authentication Scope Rules

- Own transport-neutral normalized principals, bounded evidence/context, adapter results, exact evidence routing, and immutable Authentication composition here.
- Import only the standard library and this package. Do not import FastAPI, routes, MCP, Governance, plugin contracts, plugins, or host configuration.
- Never expose credentials, raw evidence, headers, claims, certificates, or exception details through principals, failures, representations, or logs.
- Route submitted evidence to exactly one registration by host-derived descriptor. Never probe sequentially or fall back to another adapter or anonymous access.
- Anonymous is an independent configured mode for evidence-free requests only.
- The host constructs canonical principal identities; adapters return only validated adapter-local subjects.

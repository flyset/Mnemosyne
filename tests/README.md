# Tests

Install the test extra, then run the suite from an activated project virtual
environment:

```bash
python -m pip install -e ".[test]"
mymcp-test
```

`python -m pytest tests` remains equivalent when the virtual environment is
active.

The suite uses pytest importlib mode and discovers tests below `tests/`.

Released MyMCP `0.2.0` keeps Mnemosyne compatibility tests alongside
host identity and tracked OpenCode policy coverage. The completed release
verification includes 1,139 full-suite tests and two packaging tests. Automated
tests complement, but do not replace, repository/client/operational checks. The
public, non-draft, non-prerelease release is
[`MyMCP 0.2.0: public-host cutover`](https://github.com/flyset/MyMCP/releases/tag/mymcp-v0.2.0),
tagged `mymcp-v0.2.0` at `c2852bc`. MyMCP `0.4.0` adds tested external startup
composition: schema-1 compatibility, schema-2 locators, source-safe manifest
preflight, ordered loading/parity, deterministic bindings, and collision failure.
MyMCP `0.5.0` adds tested Authentication contract/routing/principal behavior,
schema-3 configuration, explicit anonymous compatibility, and pre-MCP empty-401
rejection. The delivered `0.6.0` build adds the tested `operator-bearer-v1`
production adapter, protected verifier-source format 1, schema-4 configuration,
exact Authorization bearer handling, and registered-principal delivery. The delivered `0.7.0` build adds tested
schema-5 `oauth-jwt-jwks-v1` startup composition, mutually exclusive Bearer
methods, immutable OAuth validation snapshots, conditional RFC 9728
protected-resource metadata, and OAuth-only body-free 401 challenges. MCP,
plugin, Mnemosyne, and Governance behavior remain unchanged. The delivered `0.8.0`
build adds focused host and route coverage for reauthenticated, process-local
registered MCP sessions, session-header transport, termination, and stateless
anonymous compatibility; it does not add Governance or Tool authorization.

## Layout

- `tests/mcp/` covers host MCP message parsing, JSON-RPC helpers, runtime-bound
  dispatch, tool registration, argument normalization, host `list_tools`, and
  Mnemosyne Tool compatibility.
- `tests/plugin/` covers kind-qualified contracts, immutable definition values,
  strict manifest parsing, extracted bundled Mnemosyne declaration parity, and
  `ActivatedTool`/`PluginContribution` composition.
- `tests/authentication/` covers immutable principals/evidence/results, exact
  no-fallback routing, anonymous admission, synthetic multi-adapter behavior, and
  `operator-bearer-v1` and `oauth-jwt-jwks-v1` contracts.
- `tests/host/` covers immutable `HostRuntime`, schema-1 through schema-5 configuration,
  source-safe external manifest preflight, ordered loading, and explicit complete
  production bootstrap before runtime generation.
- `tests/routes/` covers FastAPI HTTP transport through `TestClient`.
- `tests/test_app.py` covers runtime-injected app assembly, production factory,
  and side-effect-free ordinary imports.
- `tests/test_production_compatibility.py` covers the default unmocked production
  factory, exact read-only Tool surface, and no-write startup/dispatch behavior.
- `tests/test_packaging.py` builds an offline wheel without installing it and
  verifies the complete extracted Mnemosyne plugin source-to-wheel inventory,
  fixed manifest resource, and parser parity.
- `tests/test_test_foundation.py` is the minimal test-runner discovery check.

## Conventions

- Keep tests focused on one observable contract.
- For behavior changes, first add a failing focused test, then make the
  smallest implementation pass it before refactoring.
- Prefer local fixtures unless a fixture is broadly reused.
- Run the full suite before recording Track validation evidence.

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
tagged `mymcp-v0.2.0` at `c2852bc`. External plugin, lifecycle, and gateway work
remains deferred.

## Layout

- `tests/mcp/` covers host MCP message parsing, JSON-RPC helpers, runtime-bound
  dispatch, tool registration, argument normalization, host `list_tools`, and
  Mnemosyne Tool compatibility.
- `tests/plugin/` covers kind-qualified contracts, immutable definition values,
  strict manifest parsing, extracted bundled Mnemosyne declaration parity, and
  `ActivatedTool`/`PluginContribution` composition.
- `tests/host/` covers immutable `HostRuntime` and explicit production bootstrap,
  including validation before runtime generation.
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

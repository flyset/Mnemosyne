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

## Layout

- `tests/mcp/` covers message parsing, JSON-RPC helpers, runtime-bound dispatch,
  tool registration, composition, and handlers.
- `tests/plugin/` covers kind-qualified contracts and
  `ActivatedTool`/`PluginContribution` composition.
- `tests/host/` covers immutable `HostRuntime` and explicit production bootstrap.
- `tests/routes/` covers FastAPI HTTP transport through `TestClient`.
- `tests/test_app.py` covers runtime-injected app assembly, production factory,
  and side-effect-free ordinary imports.
- `tests/test_production_compatibility.py` covers the default unmocked production
  factory, exact read-only Tool surface, and no-write startup/dispatch behavior.
- `tests/test_test_foundation.py` is the minimal test-runner discovery check.

## Conventions

- Keep tests focused on one observable contract.
- For behavior changes, first add a failing focused test, then make the
  smallest implementation pass it before refactoring.
- Prefer local fixtures unless a fixture is broadly reused.
- Run the full suite before recording Track validation evidence.

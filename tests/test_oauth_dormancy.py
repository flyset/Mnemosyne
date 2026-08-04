"""S5 composition/reachability guards for the dormant OAuth validation foundation.

TRACK_044 delivered the ``oauth-jwt-jwks-v1`` validator and discovery loader as a
packaged but intentionally unreachable foundation. These tests prove at the
production-ownership seams and at runtime that ordinary host startup never loads
the OAuth modules or the isolated ``PyJWT[crypto]`` runtime, that the host never
registers ``oauth-jwt-jwks-v1`` or a schema 5, that the public route surface
remains exactly ``/mcp`` GET+POST, ``/health`` GET, ``/version`` GET with no OAuth
resource-server routes, that the Tool surface and MCP dispatch are unchanged, and
that the built package carries the dormant modules and dependency metadata with
no auto-registration.

These guard tests inspect production source/import seams and runtime
``sys.modules`` state only; they deliberately avoid whole-repository string
scans that would flag documentation or test fixtures.
"""

import ast
import base64
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mymcp import authentication as authentication_package
from mymcp.authentication.adapters import __all__ as ADAPTERS_ALL
from mymcp.app import create_production_app
from mymcp.host.authentication import (
    HostAuthenticationCompositionError,
    build_production_authenticator,
)
from mymcp.host.configuration import (
    OPERATOR_BEARER_ADAPTER_TYPE,
    SUPPORTED_HOST_CONFIGURATION_SCHEMA_VERSIONS,
    parse_host_configuration_toml,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MYMCP_ROOT = PROJECT_ROOT / "mymcp"

OAUTH_PROFILE = "oauth-jwt-jwks-v1"
OAUTH_MODULES = frozenset(
    {
        "mymcp.authentication.adapters.oauth_jwt",
        "mymcp.authentication.adapters.oauth_discovery",
    }
)
_DORMANT_MODULES = (
    "authentication/adapters/oauth_jwt.py",
    "authentication/adapters/oauth_discovery.py",
)

# Standard OAuth2 / RFC 8414 / RFC 8707 / RFC 7591 resource-server paths that a
# registered OAuth Authentication surface would expose. None may be reachable.
_FORBIDDEN_OAUTH_PATHS = (
    "/.well-known/oauth-authorization-server",
    "/.well-known/oauth-protected-resource",
    "/.well-known/openid-configuration",
    "/protected-resource",
    "/authorization-server",
    "/authorize",
    "/token",
    "/introspect",
    "/revoke",
    "/register",
    "/device_authorization",
)

_MEMORY_DISABLED_VARS = (
    "MNEMOSYNE_MEMORY_REMEMBER_ENABLED",
    "MNEMOSYNE_MEMORY_ARCHIVE_RESTORE_ENABLED",
    "MNEMOSYNE_MEMORY_REVISE_ENABLED",
    "MNEMOSYNE_MEMORY_FORGET_ENABLED",
)


def _oauth_module_probe_tail() -> str:
    return """loaded = sorted(
    name
    for name in sys.modules
    if name.startswith("mymcp.authentication.adapters.oauth_")
    or name == "jwt"
    or name == "cryptography"
    or name.startswith("cryptography.")
)
print(",".join(loaded))
"""


def _run_probe(
    source: str,
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = dict(os.environ)
    if env is not None:
        merged.update(env)
    merged.pop("MNEMOSYNE_MEMORY_ROOT", None)
    return subprocess.run(
        [sys.executable, "-c", source],
        cwd=PROJECT_ROOT,
        env=merged,
        capture_output=True,
        text=True,
        check=False,
    )


def _assert_probe_loads_nothing_oauth(
    completed: subprocess.CompletedProcess[str],
) -> None:
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stderr == ""
    assert completed.stdout.splitlines() == [""]


def _verifier_digest_text() -> str:
    return (
        base64.urlsafe_b64encode(hashlib.sha256(bytes(range(32))).digest())
        .rstrip(b"=")
        .decode("ascii")
    )


def _write_verifier(tmp_path: Path) -> str:
    source = tmp_path / "verifier.json"
    source.write_text(
        json.dumps(
            {
                "format_version": 1,
                "credentials": [
                    {
                        "id": "a" * 32,
                        "subject": "stable-subject",
                        "digest": _verifier_digest_text(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    os.chmod(source, 0o600)
    return str(source)


@pytest.fixture(scope="module")
def production_client(tmp_path_factory):
    root = tmp_path_factory.mktemp("oauth-dormancy")
    saved = {
        name: os.environ.get(name)
        for name in ("HOME", "XDG_CONFIG_HOME", *tuple(_MEMORY_DISABLED_VARS))
    }
    os.environ["HOME"] = str(root / "home")
    os.environ["XDG_CONFIG_HOME"] = str(root / "xdg")
    for var in _MEMORY_DISABLED_VARS:
        os.environ[var] = "false"
    os.environ.pop("MNEMOSYNE_MEMORY_ROOT", None)
    try:
        return TestClient(create_production_app())
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


# --------------------------------------------------------------------------- #
# Runtime import guards: ordinary app/config/operator-bearer startup
# --------------------------------------------------------------------------- #


def test_ordinary_app_cli_and_config_imports_do_not_load_oauth_runtime() -> None:
    probe = (
        "import sys\n"
        "import mymcp.app\n"
        "import mymcp.cli\n"
        "import mymcp.host.configuration\n"
        + _oauth_module_probe_tail()
    )
    completed = _run_probe(probe)
    _assert_probe_loads_nothing_oauth(completed)


def test_operator_bearer_startup_does_not_load_oauth_runtime(tmp_path: Path) -> None:
    verifier_path = _write_verifier(tmp_path)
    probe = (
        "import sys\n"
        "from mymcp.host.configuration import parse_host_configuration_toml\n"
        "from mymcp.host.authentication import build_production_authenticator\n"
        'configuration = parse_host_configuration_toml("""\n'
        "schema_version = 4\n"
        "[authentication]\n"
        "anonymous_enabled = true\n"
        "[[authentication.adapters]]\n"
        'id = "local-client"\n'
        'type = "operator-bearer-v1"\n'
        "enabled = true\n"
        'route = {source = "authorization", scheme = "bearer"}\n'
        "[authentication.operator_bearer]\n"
        f'verifier_path = "{verifier_path}"\n'
        '""")\n'
        "build_production_authenticator(configuration)\n"
        + _oauth_module_probe_tail()
    )
    completed = _run_probe(probe)
    _assert_probe_loads_nothing_oauth(completed)


def test_production_app_construction_does_not_load_oauth_runtime(
    tmp_path: Path,
) -> None:
    env = {
        "HOME": str(tmp_path / "home"),
        "XDG_CONFIG_HOME": str(tmp_path / "xdg"),
        **{var: "false" for var in _MEMORY_DISABLED_VARS},
    }
    probe = (
        "import sys\n"
        "from mymcp.app import create_production_app\n"
        "create_production_app()\n"
        + _oauth_module_probe_tail()
    )
    completed = _run_probe(probe, env=env)
    _assert_probe_loads_nothing_oauth(completed)


def test_production_host_source_never_imports_dormant_oauth_modules_at_module_level() -> None:
    # No importable module may statically (module-level) import the dormant OAuth
    # adapter/discovery modules. ``mymcp.host.authentication`` loads them lazily
    # only inside an enabled-OAuth composition function, which the module-level
    # scan below intentionally does not flag; the runtime probes instead prove
    # ordinary startup never loads the OAuth/PyJWT runtime.
    violations: list[str] = []
    for path in sorted(MYMCP_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(MYMCP_ROOT).as_posix()
        if relative in _DORMANT_MODULES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)
        for name in imported:
            if any(
                name == module or name.startswith(module + ".")
                for module in OAUTH_MODULES
            ):
                violations.append(f"{relative} imports {name}")
    assert violations == []


# --------------------------------------------------------------------------- #
# Registered adapter types / configuration schemas stay exactly current
# --------------------------------------------------------------------------- #


def test_host_authentication_registration_adds_oauth_under_schema_five() -> None:
    assert OPERATOR_BEARER_ADAPTER_TYPE == "operator-bearer-v1"
    assert OAUTH_PROFILE not in {OPERATOR_BEARER_ADAPTER_TYPE}
    assert SUPPORTED_HOST_CONFIGURATION_SCHEMA_VERSIONS == frozenset({1, 2, 3, 4, 5, 6})
    assert 5 in SUPPORTED_HOST_CONFIGURATION_SCHEMA_VERSIONS


def test_oauth_profile_type_is_not_registered_and_fails_closed() -> None:
    source = f"""
schema_version = 4
[authentication]
anonymous_enabled = true
[[authentication.adapters]]
id = "external-oauth"
type = "{OAUTH_PROFILE}"
enabled = true
route = {{source = "authorization", scheme = "bearer", profile = "oauth"}}
"""
    configuration = parse_host_configuration_toml(source)

    with pytest.raises(HostAuthenticationCompositionError) as captured:
        build_production_authenticator(configuration)

    assert captured.value.code == "adapter_type_unavailable"


def test_authentication_package_never_reexports_oauth_symbols() -> None:
    # ``mymcp.authentication.oauth`` is the standard-library-only shared helper
    # module and necessarily appears as a package submodule attribute; the
    # package still never re-exports any OAuth adapter/discovery symbol.
    assert not any("oauth" in name.lower() for name in authentication_package.__all__)
    assert not any("oauth" in name.lower() for name in ADAPTERS_ALL)
    assert "OAuthJwtAdapter" not in dir(authentication_package)


# --------------------------------------------------------------------------- #
# Public route surface stays exactly /mcp GET+POST, /health GET, /version GET
# --------------------------------------------------------------------------- #


def _public_routes(app) -> dict[str, frozenset[str]]:
    surface: dict[str, set[str]] = {}
    stack = [*app.routes]
    seen: set[int] = set()
    while stack:
        route = stack.pop()
        marker = id(route)
        if marker in seen:
            continue
        seen.add(marker)
        if type(route).__name__ == "_IncludedRouter":
            inner = getattr(route, "original_router", None)
            if inner is not None and hasattr(inner, "routes"):
                stack.extend(inner.routes)
            continue
        path = getattr(route, "path", None)
        if path is None:
            continue
        # FastAPI's own documentation surface is not part of the public host API.
        if path in {"/docs", "/redoc", "/openapi.json"} or path.startswith("/docs/"):
            continue
        surface.setdefault(path, set()).update(getattr(route, "methods", ()) or ())
    return {path: frozenset(methods) for path, methods in sorted(surface.items())}


def test_production_app_route_surface_remains_mcp_health_version(
    production_client,
) -> None:
    assert _public_routes(production_client.app) == {
        "/mcp": frozenset({"GET", "POST", "DELETE"}),
        "/health": frozenset({"GET"}),
        "/version": frozenset({"GET"}),
    }


@pytest.mark.parametrize("path", _FORBIDDEN_OAUTH_PATHS)
def test_no_oauth_resource_server_routes_are_reachable(production_client, path) -> None:
    for method in ("get", "post"):
        response = getattr(production_client, method)(path)
        assert response.status_code == 404, (method, path)


# --------------------------------------------------------------------------- #
# Tool surface and MCP dispatch stay unchanged
# --------------------------------------------------------------------------- #


def test_default_tool_surface_stays_exact_read_only_set(production_client) -> None:
    tools = production_client.post(
        "/mcp", headers={"MCP-Protocol-Version": "2025-11-25"}, json={"id": "tools", "method": "tools/list"}
    ).json()["result"]["tools"]
    names = [tool["name"] for tool in tools]
    assert names == ["list_tools", "memory_recall", "memory_list", "memory_inspect"]
    assert all("oauth" not in name.lower() for name in names)


def test_mcp_dispatch_preserves_initialize_contract(production_client) -> None:
    response = production_client.post(
        "/mcp", json={"id": "init", "method": "initialize"}
    )

    assert response.status_code == 200
    assert response.json()["result"] == {
        "protocolVersion": "2025-11-25",
        "capabilities": {"tools": {}},
        "serverInfo": {"name": "mymcp", "version": "0.9.0"},
    }


def test_mcp_dispatch_rejects_unknown_methods_unchanged(production_client) -> None:
    response = production_client.post(
        "/mcp", headers={"MCP-Protocol-Version": "2025-11-25"}, json={"id": "r", "method": "missing"}
    )

    assert response.json() == {
        "jsonrpc": "2.0",
        "id": "r",
        "error": {"code": -32601, "message": "Unknown method: missing"},
    }


# --------------------------------------------------------------------------- #
# Package guards
# --------------------------------------------------------------------------- #

def _console_script_names(entry_points: str) -> set[str]:
    names: set[str] = set()
    for line in entry_points.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("[") or stripped.startswith("#"):
            continue
        names.add(stripped.split("=", 1)[0].strip())
    return names


def test_built_package_bundles_dormant_oauth_modules_without_autoregistration(
    tmp_path,
) -> None:
    import shutil
    from zipfile import ZipFile

    source_directory = tmp_path / "source"
    wheel_directory = tmp_path / "dist"
    source_directory.mkdir()
    shutil.copy2(PROJECT_ROOT / "pyproject.toml", source_directory / "pyproject.toml")
    shutil.copy2(PROJECT_ROOT / "README.md", source_directory / "README.md")
    shutil.copytree(
        PROJECT_ROOT / "mymcp",
        source_directory / "mymcp",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(wheel_directory),
        ],
        cwd=source_directory,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

    wheels = tuple(wheel_directory.glob("*.whl"))
    assert len(wheels) == 1
    with ZipFile(wheels[0]) as wheel:
        wheel_files = set(wheel.namelist())
        for module in (
            "mymcp/authentication/adapters/oauth_jwt.py",
            "mymcp/authentication/adapters/oauth_discovery.py",
        ):
            assert module in wheel_files

        metadata_name = next(
            name for name in wheel_files if name.endswith(".dist-info/METADATA")
        )
        metadata = wheel.read(metadata_name).decode("utf-8")
        pyjwt_requirement = next(
            line
            for line in metadata.splitlines()
            if line.startswith("Requires-Dist: PyJWT[crypto]")
        )
        assert ">=2.13.0" in pyjwt_requirement
        assert "<3.0" in pyjwt_requirement

        entry_points_name = next(
            name
            for name in wheel_files
            if name.endswith(".dist-info/entry_points.txt")
        )
        entry_points = wheel.read(entry_points_name).decode("utf-8")
        # Only the three host console scripts exist; no oauth auto-registration.
        assert _console_script_names(entry_points) == {
            "mymcp",
            "mymcp-dev",
            "mymcp-test",
        }
        assert "oauth" not in entry_points.lower()

import ast
import os
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_PACKAGE = PROJECT_ROOT / "mymcp" / "plugins" / "mnemosyne"
MEMORY_PACKAGE = PLUGIN_PACKAGE / "memory"
HOST_SETTINGS = PROJECT_ROOT / "mymcp" / "settings.py"
MNEMOSYNE_CONFIGURATION = PLUGIN_PACKAGE / "configuration.py"
LISTING_MODULE = MEMORY_PACKAGE / "listing.py"
PLUGIN_MCP_TOOLS = PLUGIN_PACKAGE / "mcp" / "tools"
LIST_PACKAGE = PLUGIN_MCP_TOOLS / "memory_list"
RECALL_PACKAGE = PLUGIN_MCP_TOOLS / "memory_recall"
REMEMBER_PACKAGE = PLUGIN_MCP_TOOLS / "memory_remember"
INSPECT_PACKAGE = PLUGIN_MCP_TOOLS / "memory_inspect"
ARCHIVE_PACKAGE = PLUGIN_MCP_TOOLS / "memory_archive"
RESTORE_PACKAGE = PLUGIN_MCP_TOOLS / "memory_restore"
FORGET_PACKAGE = PLUGIN_MCP_TOOLS / "memory_forget"
REVISE_PACKAGE = PLUGIN_MCP_TOOLS / "memory_revise"
REVISE_HELPER = PLUGIN_MCP_TOOLS / "_memory_revise.py"
FORGET_HELPER = PLUGIN_MCP_TOOLS / "_memory_forget.py"
MNEMOSYNE_INTEGRATION = PLUGIN_PACKAGE / "plugin.py"
MCP_DISPATCHER = PROJECT_ROOT / "mymcp" / "mcp" / "dispatcher.py"
MCP_PROTOCOL = PROJECT_ROOT / "mymcp" / "mcp" / "protocol.py"
TOOL_REGISTRY = PROJECT_ROOT / "mymcp" / "mcp" / "tool_registry.py"
PLUGIN_CONTRACTS = PROJECT_ROOT / "mymcp" / "plugin" / "contracts.py"
PLUGIN_COMPOSITION = PROJECT_ROOT / "mymcp" / "plugin" / "composition.py"
PLUGIN_DEFINITION = PROJECT_ROOT / "mymcp" / "plugin" / "definition.py"
PLUGIN_MANIFEST = PROJECT_ROOT / "mymcp" / "plugin" / "manifest.py"
HOST_RUNTIME = PROJECT_ROOT / "mymcp" / "host" / "runtime.py"
HOST_BOOTSTRAP = PROJECT_ROOT / "mymcp" / "host" / "bootstrap.py"
OBSOLETE_MCP_MODULES = (
    PROJECT_ROOT / "mymcp" / "mcp" / "methods.py",
    PROJECT_ROOT / "mymcp" / "mcp" / "startup.py",
    PROJECT_ROOT / "mymcp" / "mcp" / "composition.py",
)
MEMORY_CONFIGURATION_MODULES = {
    "mymcp.settings",
    "mymcp.plugins.mnemosyne.configuration",
}
LIFECYCLE_HELPER = PLUGIN_MCP_TOOLS / "_memory_lifecycle.py"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
    return imports


def _imported_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }


def _defined_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(
                target.id
                for target in node.targets
                if isinstance(target, ast.Name)
            )
    return names


def test_mnemosyne_configuration_has_one_explicit_non_host_owner() -> None:
    assert MNEMOSYNE_CONFIGURATION.exists()

    memory_configuration_names = {
        "MemoryToolSettings",
        "SettingsError",
        "get_memory_root",
        "get_memory_tool_settings",
        "get_memory_remember_enabled",
        "get_memory_archive_restore_enabled",
        "get_memory_forget_enabled",
        "get_memory_revise_enabled",
    }
    assert _defined_names(HOST_SETTINGS) == {
        "SERVER_NAME",
        "SERVER_VERSION",
        "PROTOCOL_VERSION",
        "APP_TITLE",
    }
    assert _defined_names(HOST_SETTINGS).isdisjoint(memory_configuration_names)
    assert memory_configuration_names <= _defined_names(
        MNEMOSYNE_CONFIGURATION
    )
    assert _imports(MNEMOSYNE_CONFIGURATION).isdisjoint(
        {"mymcp.mcp", "mymcp.routes", "fastapi"}
    )


def test_memory_handlers_do_not_own_service_store_or_root_construction() -> None:
    handler_paths = [
        package / "handler.py"
        for package in (
            RECALL_PACKAGE,
            LIST_PACKAGE,
            INSPECT_PACKAGE,
            REMEMBER_PACKAGE,
            ARCHIVE_PACKAGE,
            RESTORE_PACKAGE,
            REVISE_PACKAGE,
            FORGET_PACKAGE,
        )
    ]

    violations = {
        str(path.relative_to(PROJECT_ROOT)): {
            "imports": sorted(
                _imports(path)
                & ({"mymcp.plugins.mnemosyne.memory.store"} | MEMORY_CONFIGURATION_MODULES)
            ),
            "names": sorted(
                _imported_names(path)
                & {"FilesystemMemoryStore", "MemoryService", "get_memory_root"}
            ),
        }
        for path in handler_paths
    }

    assert {
        path: violation
        for path, violation in violations.items()
        if violation["imports"] or violation["names"]
    } == {}


def test_mnemosyne_integration_owns_memory_service_composition() -> None:
    imports = _imports(MNEMOSYNE_INTEGRATION)
    imported_names = _imported_names(MNEMOSYNE_INTEGRATION)

    assert "mymcp.plugins.mnemosyne.memory.service" in imports
    assert "mymcp.plugins.mnemosyne.memory.store" in imports
    assert "mymcp.plugins.mnemosyne.configuration" in imports
    assert "mymcp.settings" not in imports
    assert {
        "MemoryService",
        "FilesystemMemoryStore",
        "get_memory_root",
    } <= imported_names
    assert "ToolRegistration" in imported_names
    assert "ToolRegistry" not in imported_names
    assert "list_tools" not in imported_names


def test_shared_memory_domain_imports_no_host_or_transport_modules() -> None:
    forbidden = (
        "mymcp.mcp",
        "mymcp.routes",
        "mymcp.settings",
        "mymcp.plugins.mnemosyne.configuration",
        "fastapi",
    )

    violations = {
        path.name: sorted(
            imported
            for imported in _imports(path)
            if imported.startswith(forbidden)
        )
        for path in MEMORY_PACKAGE.glob("*.py")
    }

    assert {name: imports for name, imports in violations.items() if imports} == {}


def test_generic_mcp_registry_and_dispatcher_own_no_memory_configuration(
) -> None:
    forbidden_names = {
        "MemoryToolSettings",
        "get_memory_root",
        "get_memory_tool_settings",
        "get_memory_remember_enabled",
        "get_memory_archive_restore_enabled",
        "get_memory_forget_enabled",
        "get_memory_revise_enabled",
    }

    generic_forbidden_imports = MEMORY_CONFIGURATION_MODULES | {
        "mymcp.plugins.mnemosyne.plugin",
        "mymcp.plugins.mnemosyne.memory",
    }

    assert _imports(TOOL_REGISTRY).isdisjoint(generic_forbidden_imports)
    assert _imported_names(TOOL_REGISTRY).isdisjoint(forbidden_names)
    assert _imported_names(MCP_DISPATCHER).isdisjoint(forbidden_names)


def test_runtime_bound_dispatcher_and_protocol_are_transport_domain_neutral() -> None:
    forbidden = (
        "fastapi",
        "mymcp.routes",
        "mymcp.host.bootstrap",
        "mymcp.mcp.integrations",
        "mymcp.mcp.tools",
        "mymcp.plugins.mnemosyne.memory",
        "mymcp.mnemosyne",
        "mymcp.plugins",
    )

    for module in (MCP_DISPATCHER, MCP_PROTOCOL):
        assert all(
            not imported.startswith(forbidden) for imported in _imports(module)
        ), module

    assert {
        "mymcp.mcp.messages",
        "mymcp.mcp.protocol",
        "mymcp.mcp.tool_registry",
        "mymcp.settings",
    } <= _imports(MCP_DISPATCHER)


def test_generic_plugin_contracts_composition_and_runtime_are_domain_neutral() -> None:
    forbidden = (
        "mymcp.mcp.integrations",
        "mymcp.mcp.tools",
        "mymcp.plugins.mnemosyne.memory",
        "mymcp.mnemosyne",
        "mymcp.plugins",
        "mymcp.routes",
        "fastapi",
    )

    for module in (
        PLUGIN_CONTRACTS,
        PLUGIN_COMPOSITION,
        PLUGIN_DEFINITION,
        PLUGIN_MANIFEST,
        HOST_RUNTIME,
    ):
        assert all(
            not imported.startswith(forbidden) for imported in _imports(module)
        ), module

    assert {
        "mymcp.mcp.tool_registry",
        "mymcp.plugin.composition",
        "mymcp.plugin.contracts",
    } <= _imports(HOST_RUNTIME)


def test_host_bootstrap_is_the_only_host_module_importing_mnemosyne_adapter() -> None:
    adapter = "mymcp.plugins.mnemosyne.plugin"
    host_modules = tuple((PROJECT_ROOT / "mymcp" / "host").glob("*.py"))
    importers = {module.name for module in host_modules if adapter in _imports(module)}

    assert importers == {"bootstrap.py"}
    assert {
        "mymcp.host.runtime",
        "mymcp.plugins.mnemosyne.plugin",
        "mymcp.mcp.tool_registry",
        "mymcp.mcp.tools",
    } <= _imports(HOST_BOOTSTRAP)
    assert all(
        not imported.startswith(("mymcp.plugins.mnemosyne.memory", "mymcp.plugins.mnemosyne.configuration"))
        for imported in _imports(HOST_BOOTSTRAP)
    )


def test_host_bootstrap_performs_no_dynamic_or_network_discovery() -> None:
    forbidden = (
        "importlib.metadata",
        "importlib.util",
        "pkgutil",
        "socket",
        "urllib",
        "http.client",
    )

    assert "importlib.resources" in _imports(HOST_BOOTSTRAP)
    assert all(
        not imported.startswith(forbidden) for imported in _imports(HOST_BOOTSTRAP)
    )
    source = HOST_BOOTSTRAP.read_text(encoding="utf-8")
    assert source.count('files("mymcp.plugins.mnemosyne")') == 1
    assert source.count('joinpath("manifest.json")') == 1
    assert "import_module" not in source
    assert "entry_points" not in source


def test_ordinary_imports_do_not_compose_the_production_runtime(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    settings_directory = home / ".mnemosyne"
    settings_directory.mkdir(parents=True)
    (settings_directory / "config.toml").write_text(
        "not valid toml",
        encoding="utf-8",
    )
    environment = os.environ | {
        "HOME": str(home),
        "PYTHONPATH": str(PROJECT_ROOT),
    }

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import mymcp; import mymcp.app; import mymcp.host; "
                "import mymcp.mcp.dispatcher; import mymcp.plugin"
            ),
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_obsolete_static_composition_modules_are_deleted() -> None:
    assert all(not module.exists() for module in OBSOLETE_MCP_MODULES)


def test_listing_has_no_top_level_runtime_store_import() -> None:
    tree = ast.parse(LISTING_MODULE.read_text(encoding="utf-8"))
    top_level_imports = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert "mymcp.plugins.mnemosyne.memory.store" not in top_level_imports


def test_memory_recall_package_contains_only_mcp_adapter_modules() -> None:
    assert sorted(path.name for path in RECALL_PACKAGE.glob("*.py")) == [
        "__init__.py",
        "definition.py",
        "handler.py",
    ]


def test_memory_list_package_contains_only_mcp_adapter_modules() -> None:
    assert sorted(path.name for path in LIST_PACKAGE.glob("*.py")) == [
        "__init__.py",
        "definition.py",
        "handler.py",
    ]


def test_memory_list_definition_and_handler_use_shared_domain_contracts() -> None:
    definition_imports = _imports(LIST_PACKAGE / "definition.py")
    handler_imports = _imports(LIST_PACKAGE / "handler.py")

    assert "mymcp.plugins.mnemosyne.memory.scopes" in definition_imports
    assert "mymcp.plugins.mnemosyne.memory.normalization" in definition_imports
    assert "mymcp.plugins.mnemosyne.memory.listing" in handler_imports
    assert "mymcp.plugins.mnemosyne.memory.records" in handler_imports
    assert "mymcp.plugins.mnemosyne.memory.errors" in handler_imports
    assert "mymcp.plugins.mnemosyne.memory.service" not in handler_imports
    assert "mymcp.plugins.mnemosyne.memory.store" not in handler_imports
    assert "mymcp.settings" not in handler_imports
    assert "mymcp.plugins.mnemosyne.configuration" not in handler_imports
    assert all(
        not imported.startswith(
            (
                "mymcp.plugins.mnemosyne.mcp.tools.memory_recall",
                "mymcp.plugins.mnemosyne.mcp.tools.memory_inspect",
                "mymcp.plugins.mnemosyne.mcp.tools.memory_remember",
                "mymcp.plugins.mnemosyne.mcp.tools.memory_archive",
                "mymcp.plugins.mnemosyne.mcp.tools.memory_restore",
                "mymcp.plugins.mnemosyne.mcp.tools.memory_revise",
                "mymcp.plugins.mnemosyne.mcp.tools.memory_forget",
                "mymcp.routes",
                "fastapi",
            )
        )
        for imported in definition_imports | handler_imports
    )


def test_memory_recall_handler_uses_shared_service_and_store() -> None:
    handler_imports = _imports(RECALL_PACKAGE / "handler.py")

    assert "mymcp.plugins.mnemosyne.memory.service" not in handler_imports
    assert "mymcp.plugins.mnemosyne.memory.store" not in handler_imports
    assert "mymcp.settings" not in handler_imports
    assert "mymcp.plugins.mnemosyne.configuration" not in handler_imports
    assert "mymcp.plugins.mnemosyne.mcp.tools.memory_recall.retrieval" not in handler_imports


def test_memory_remember_package_contains_only_mcp_adapter_modules() -> None:
    assert sorted(path.name for path in REMEMBER_PACKAGE.glob("*.py")) == [
        "__init__.py",
        "definition.py",
        "handler.py",
    ]


def test_memory_remember_definition_and_handler_use_only_shared_contracts() -> None:
    definition_imports = _imports(REMEMBER_PACKAGE / "definition.py")
    handler_imports = _imports(REMEMBER_PACKAGE / "handler.py")

    assert "mymcp.plugins.mnemosyne.memory.scopes" in definition_imports
    assert "mymcp.plugins.mnemosyne.memory.records" in definition_imports
    assert "mymcp.plugins.mnemosyne.memory.records" in handler_imports
    assert "mymcp.plugins.mnemosyne.memory.errors" in handler_imports
    assert "mymcp.plugins.mnemosyne.memory.service" in handler_imports
    assert "mymcp.plugins.mnemosyne.memory.store" not in handler_imports
    assert "mymcp.settings" not in handler_imports
    assert "mymcp.plugins.mnemosyne.configuration" not in handler_imports
    assert all(
        not imported.startswith(
            ("mymcp.plugins.mnemosyne.mcp.tools.memory_recall", "mymcp.routes", "fastapi")
        )
        for imported in definition_imports | handler_imports
    )


def test_memory_inspect_package_contains_only_mcp_adapter_modules() -> None:
    assert sorted(path.name for path in INSPECT_PACKAGE.glob("*.py")) == [
        "__init__.py",
        "definition.py",
        "handler.py",
    ]


def test_memory_inspect_definition_and_handler_use_shared_reference_contracts() -> None:
    definition_imports = _imports(INSPECT_PACKAGE / "definition.py")
    handler_imports = _imports(INSPECT_PACKAGE / "handler.py")

    assert "mymcp.plugins.mnemosyne.memory.scopes" in definition_imports
    assert "mymcp.plugins.mnemosyne.memory.normalization" in definition_imports
    assert "mymcp.plugins.mnemosyne.memory.records" in handler_imports
    assert "mymcp.plugins.mnemosyne.memory.errors" in handler_imports
    assert "mymcp.plugins.mnemosyne.memory.service" not in handler_imports
    assert "mymcp.plugins.mnemosyne.memory.store" not in handler_imports
    assert "mymcp.settings" not in handler_imports
    assert "mymcp.plugins.mnemosyne.configuration" not in handler_imports
    assert all(
        not imported.startswith(
            (
                "mymcp.plugins.mnemosyne.mcp.tools.memory_recall",
                "mymcp.plugins.mnemosyne.mcp.tools.memory_remember",
                "mymcp.routes",
                "fastapi",
            )
        )
        for imported in definition_imports | handler_imports
    )


def test_memory_lifecycle_tool_packages_contain_only_mcp_adapter_modules() -> None:
    for package in (ARCHIVE_PACKAGE, RESTORE_PACKAGE):
        assert sorted(path.name for path in package.glob("*.py")) == [
            "__init__.py",
            "definition.py",
            "handler.py",
        ]


def test_memory_lifecycle_adapters_preserve_shared_domain_ownership() -> None:
    helper_imports = _imports(LIFECYCLE_HELPER)
    archive_imports = {
        imported
        for path in ARCHIVE_PACKAGE.glob("*.py")
        for imported in _imports(path)
    }
    restore_imports = {
        imported
        for path in RESTORE_PACKAGE.glob("*.py")
        for imported in _imports(path)
    }

    assert "mymcp.plugins.mnemosyne.memory.normalization" in helper_imports
    assert "mymcp.plugins.mnemosyne.memory.scopes" in helper_imports
    assert "mymcp.plugins.mnemosyne.memory.records" in helper_imports
    assert "mymcp.plugins.mnemosyne.memory.service" in helper_imports
    assert all(
        "mymcp.plugins.mnemosyne.mcp.tools._memory_lifecycle" in imports
        for imports in (archive_imports, restore_imports)
    )
    combined = helper_imports | archive_imports | restore_imports
    assert all(
        not imported.startswith(("mymcp.routes", "fastapi"))
        for imported in combined
    )
    assert all(
        not imported.startswith("mymcp.plugins.mnemosyne.mcp.tools.memory_restore")
        for imported in archive_imports
    )
    assert all(
        not imported.startswith("mymcp.plugins.mnemosyne.mcp.tools.memory_archive")
        for imported in restore_imports
    )
    assert "mymcp.plugins.mnemosyne.memory.store" not in helper_imports
    for imports in (archive_imports, restore_imports):
        assert "mymcp.plugins.mnemosyne.memory.records" in imports
        assert "mymcp.plugins.mnemosyne.memory.service" in imports
        assert "mymcp.plugins.mnemosyne.memory.store" not in imports
        assert "mymcp.settings" not in imports
        assert "mymcp.plugins.mnemosyne.configuration" not in imports


def test_memory_forget_package_contains_only_mcp_adapter_modules() -> None:
    assert sorted(path.name for path in FORGET_PACKAGE.glob("*.py")) == [
        "__init__.py",
        "definition.py",
        "handler.py",
    ]


def test_memory_forget_adapter_preserves_shared_domain_ownership() -> None:
    helper_imports = _imports(FORGET_HELPER)
    package_imports = {
        imported
        for path in FORGET_PACKAGE.glob("*.py")
        for imported in _imports(path)
    }

    assert "mymcp.plugins.mnemosyne.mcp.tools._memory_lifecycle" in helper_imports
    assert "mymcp.plugins.mnemosyne.memory.records" in helper_imports
    assert "mymcp.plugins.mnemosyne.memory.service" in helper_imports
    assert "mymcp.plugins.mnemosyne.memory.store" not in helper_imports
    assert "mymcp.plugins.mnemosyne.mcp.tools._memory_forget" in package_imports
    assert "mymcp.plugins.mnemosyne.memory.records" in package_imports
    assert "mymcp.plugins.mnemosyne.memory.service" in package_imports
    assert "mymcp.plugins.mnemosyne.memory.store" not in package_imports
    assert "mymcp.settings" not in package_imports
    assert "mymcp.plugins.mnemosyne.configuration" not in package_imports
    assert all(
        not imported.startswith(
            (
                "mymcp.plugins.mnemosyne.mcp.tools.memory_archive",
                "mymcp.plugins.mnemosyne.mcp.tools.memory_restore",
                "mymcp.routes",
                "fastapi",
            )
        )
        for imported in helper_imports | package_imports
    )


def test_memory_revise_package_contains_only_mcp_adapter_modules() -> None:
    assert sorted(path.name for path in REVISE_PACKAGE.glob("*.py")) == [
        "__init__.py",
        "definition.py",
        "handler.py",
    ]


def test_memory_revise_adapter_preserves_shared_domain_ownership() -> None:
    helper_imports = _imports(REVISE_HELPER)
    package_imports = {
        imported
        for path in REVISE_PACKAGE.glob("*.py")
        for imported in _imports(path)
    }

    assert "mymcp.plugins.mnemosyne.mcp.tools._memory_lifecycle" in helper_imports
    assert "mymcp.plugins.mnemosyne.memory.records" in helper_imports
    assert "mymcp.plugins.mnemosyne.memory.store" not in helper_imports
    assert "mymcp.settings" not in helper_imports
    assert "mymcp.plugins.mnemosyne.configuration" not in helper_imports
    assert "mymcp.plugins.mnemosyne.mcp.tools._memory_revise" in package_imports
    assert "mymcp.plugins.mnemosyne.memory.records" not in package_imports
    assert "mymcp.plugins.mnemosyne.memory.service" not in package_imports
    assert "mymcp.plugins.mnemosyne.memory.store" not in package_imports
    assert "mymcp.settings" not in package_imports
    assert "mymcp.plugins.mnemosyne.configuration" not in package_imports
    assert all(
        not imported.startswith(
            (
                "mymcp.plugins.mnemosyne.mcp.tools.memory_remember",
                "mymcp.plugins.mnemosyne.mcp.tools.memory_archive",
                "mymcp.plugins.mnemosyne.mcp.tools.memory_restore",
                "mymcp.plugins.mnemosyne.mcp.tools.memory_forget",
                "mymcp.routes",
                "fastapi",
            )
        )
        for imported in helper_imports | package_imports
    )


PLUGIN_INIT = PLUGIN_PACKAGE / "__init__.py"
PLUGIN_MODULE = PLUGIN_PACKAGE / "plugin.py"
PLUGIN_CONFIGURATION = PLUGIN_PACKAGE / "configuration.py"
PLUGIN_MEMORY = PLUGIN_PACKAGE / "memory"
HOST_LIST_TOOLS = PROJECT_ROOT / "mymcp" / "mcp" / "tools" / "list_tools"

MEMORY_MODULES = (
    "errors.py",
    "listing.py",
    "normalization.py",
    "paths.py",
    "policy.py",
    "records.py",
    "retrieval.py",
    "scopes.py",
    "service.py",
    "store.py",
)
MEMORY_TOOL_PACKAGES = (
    "memory_archive",
    "memory_forget",
    "memory_inspect",
    "memory_list",
    "memory_recall",
    "memory_remember",
    "memory_restore",
    "memory_revise",
)
PRIVATE_TOOL_HELPERS = (
    "_memory_content_refusal.py",
    "_memory_forget.py",
    "_memory_lifecycle.py",
    "_memory_revise.py",
)


def _resolved_imports(path: Path) -> set[str]:
    """Return absolute import identities, including relative imports."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    package = tuple(path.relative_to(PROJECT_ROOT).with_suffix("").parts[:-1])
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module is not None:
                imports.add(node.module)
            elif node.level:
                anchor = package[: len(package) - node.level + 1]
                if node.module:
                    imports.add(".".join((*anchor, node.module)))
                else:
                    imports.add(".".join(anchor))
    return imports


def _production_modules() -> tuple[Path, ...]:
    return tuple(
        path
        for path in (PROJECT_ROOT / "mymcp").rglob("*.py")
        if PLUGIN_PACKAGE not in path.parents
    )


def test_canonical_plugin_owns_configuration_memory_tools_and_adapter() -> None:
    required = [
        PLUGIN_INIT,
        PLUGIN_MODULE,
        PLUGIN_CONFIGURATION,
        PLUGIN_MEMORY / "__init__.py",
        *(PLUGIN_MEMORY / module for module in MEMORY_MODULES),
        PLUGIN_MCP_TOOLS / "__init__.py",
        *(
            PLUGIN_MCP_TOOLS / package / filename
            for package in MEMORY_TOOL_PACKAGES
            for filename in ("__init__.py", "definition.py", "handler.py")
        ),
        *(PLUGIN_MCP_TOOLS / helper for helper in PRIVATE_TOOL_HELPERS),
    ]
    assert all(path.exists() for path in required), [
        str(path.relative_to(PROJECT_ROOT)) for path in required if not path.exists()
    ]


def test_transitional_mnemosyne_production_paths_are_absent() -> None:
    old_paths = [
        PROJECT_ROOT / "mymcp" / "memory",
        PROJECT_ROOT / "mymcp" / "mnemosyne",
        PROJECT_ROOT / "mymcp" / "mcp" / "integrations" / "mnemosyne.py",
        *(
            PROJECT_ROOT / "mymcp" / "mcp" / "tools" / package
            for package in MEMORY_TOOL_PACKAGES
        ),
        *(
            PROJECT_ROOT / "mymcp" / "mcp" / "tools" / helper
            for helper in PRIVATE_TOOL_HELPERS
        ),
    ]
    assert all(not path.exists() for path in old_paths), [
        str(path.relative_to(PROJECT_ROOT)) for path in old_paths if path.exists()
    ]


def test_bootstrap_is_the_only_external_importer_of_the_concrete_plugin() -> None:
    target = "mymcp.plugins.mnemosyne.plugin"
    importers = {
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in _production_modules()
        if target in _resolved_imports(path)
    }
    assert importers == {"mymcp/host/bootstrap.py"}
    assert target in _resolved_imports(HOST_BOOTSTRAP)


def test_plugin_initializer_is_minimal_and_does_not_import_implementation() -> None:
    assert _resolved_imports(PLUGIN_INIT) == set()
    assert _defined_names(PLUGIN_INIT) == set()


def test_plugin_dependency_direction_stays_inside_plugin_or_generic_mcp() -> None:
    # These assertions deliberately fail cleanly before reading absent targets.
    assert PLUGIN_MODULE.exists()
    assert PLUGIN_CONFIGURATION.exists()
    assert PLUGIN_MEMORY.exists()
    assert PLUGIN_MCP_TOOLS.exists()

    configuration_imports = _resolved_imports(PLUGIN_CONFIGURATION)
    assert all(
        imported.split(".", 1)[0] in sys.stdlib_module_names
        for imported in configuration_imports
    )

    memory_imports = {
        imported
        for path in PLUGIN_MEMORY.glob("*.py")
        for imported in _resolved_imports(path)
    }
    assert all(
        imported.split(".", 1)[0] in sys.stdlib_module_names
        or imported.startswith("mymcp.plugins.mnemosyne.memory")
        for imported in memory_imports
    )

    tool_imports = {
        imported
        for path in PLUGIN_MCP_TOOLS.rglob("*.py")
        for imported in _resolved_imports(path)
    }
    allowed_tool_imports = (
        "mymcp.plugins.mnemosyne",
        "mymcp.mcp.tool_registry",
        "mymcp.mcp.tool_arguments",
    )
    assert all(
        imported.startswith(allowed_tool_imports)
        or imported.split(".", 1)[0] in sys.stdlib_module_names
        for imported in tool_imports
    )

    adapter_imports = _resolved_imports(PLUGIN_MODULE)
    allowed_adapter_imports = (
        "mymcp.plugins.mnemosyne",
        "mymcp.plugin.",
        "mymcp.mcp.tool_registry",
    )
    assert all(
        imported.startswith(allowed_adapter_imports)
        for imported in adapter_imports
    )


def test_generic_host_and_mcp_modules_do_not_import_concrete_plugin() -> None:
    forbidden = (
        "mymcp.plugins.mnemosyne",
        "mymcp.plugins.mnemosyne.memory",
        "mymcp.mnemosyne",
        "mymcp.plugins.mnemosyne.plugin",
    )
    violations = {
        str(path.relative_to(PROJECT_ROOT)): sorted(
            imported
            for imported in _resolved_imports(path)
            if imported.startswith(forbidden)
        )
        for path in _production_modules()
        if path != HOST_BOOTSTRAP
    }
    assert {path: imports for path, imports in violations.items() if imports} == {}


def test_host_owned_list_tools_remains_outside_the_plugin() -> None:
    assert HOST_LIST_TOOLS.is_dir()
    assert (HOST_LIST_TOOLS / "__init__.py").exists()
    assert not (PLUGIN_MCP_TOOLS / "list_tools").exists()
    assert "mymcp.mcp.tools" in _resolved_imports(HOST_BOOTSTRAP)


def test_canonical_memory_exports_have_no_transitional_duplicate_identity() -> None:
    import importlib.util

    from mymcp.plugins.mnemosyne import memory
    from mymcp.plugins.mnemosyne.memory.errors import MemoryDomainError
    from mymcp.plugins.mnemosyne.memory.records import MemoryRecordV2
    from mymcp.plugins.mnemosyne.memory.service import MemoryService

    transitional_prefixes = ("mymcp.memory", "mymcp.mnemosyne")
    before = {
        name for name in sys.modules if name.startswith(transitional_prefixes)
    }

    assert memory.MemoryRecordV2 is MemoryRecordV2
    assert memory.MemoryService is MemoryService
    assert MemoryRecordV2.__module__ == (
        "mymcp.plugins.mnemosyne.memory.records"
    )
    assert MemoryService.__module__ == "mymcp.plugins.mnemosyne.memory.service"
    assert MemoryDomainError.__module__ == (
        "mymcp.plugins.mnemosyne.memory.errors"
    )

    assert before == set()
    assert {
        name for name in sys.modules if name.startswith(transitional_prefixes)
    } == set()
    assert importlib.util.find_spec("mymcp.memory") is None
    assert importlib.util.find_spec("mymcp.mnemosyne") is None

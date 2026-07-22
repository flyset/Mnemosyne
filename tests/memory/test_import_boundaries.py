import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEMORY_PACKAGE = PROJECT_ROOT / "mymcp" / "memory"
LISTING_MODULE = MEMORY_PACKAGE / "listing.py"
LIST_PACKAGE = PROJECT_ROOT / "mymcp" / "mcp" / "tools" / "memory_list"
RECALL_PACKAGE = PROJECT_ROOT / "mymcp" / "mcp" / "tools" / "memory_recall"
REMEMBER_PACKAGE = PROJECT_ROOT / "mymcp" / "mcp" / "tools" / "memory_remember"
INSPECT_PACKAGE = PROJECT_ROOT / "mymcp" / "mcp" / "tools" / "memory_inspect"
ARCHIVE_PACKAGE = PROJECT_ROOT / "mymcp" / "mcp" / "tools" / "memory_archive"
RESTORE_PACKAGE = PROJECT_ROOT / "mymcp" / "mcp" / "tools" / "memory_restore"
FORGET_PACKAGE = PROJECT_ROOT / "mymcp" / "mcp" / "tools" / "memory_forget"
REVISE_PACKAGE = PROJECT_ROOT / "mymcp" / "mcp" / "tools" / "memory_revise"
REVISE_HELPER = PROJECT_ROOT / "mymcp" / "mcp" / "tools" / "_memory_revise.py"
FORGET_HELPER = PROJECT_ROOT / "mymcp" / "mcp" / "tools" / "_memory_forget.py"
MNEMOSYNE_INTEGRATION = (
    PROJECT_ROOT / "mymcp" / "mcp" / "integrations" / "mnemosyne.py"
)
LIFECYCLE_HELPER = (
    PROJECT_ROOT / "mymcp" / "mcp" / "tools" / "_memory_lifecycle.py"
)


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
                _imports(path) & {"mymcp.memory.store", "mymcp.settings"}
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

    assert "mymcp.memory.service" in imports
    assert "mymcp.memory.store" in imports
    assert "mymcp.settings" in imports
    assert {
        "MemoryService",
        "FilesystemMemoryStore",
        "get_memory_root",
    } <= imported_names


def test_shared_memory_domain_imports_no_mcp_http_or_fastapi_modules() -> None:
    forbidden = ("mymcp.mcp", "mymcp.routes", "fastapi")

    violations = {
        path.name: sorted(
            imported
            for imported in _imports(path)
            if imported.startswith(forbidden)
        )
        for path in MEMORY_PACKAGE.glob("*.py")
    }

    assert {name: imports for name, imports in violations.items() if imports} == {}


def test_listing_has_no_top_level_runtime_store_import() -> None:
    tree = ast.parse(LISTING_MODULE.read_text(encoding="utf-8"))
    top_level_imports = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert "mymcp.memory.store" not in top_level_imports


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

    assert "mymcp.memory.scopes" in definition_imports
    assert "mymcp.memory.normalization" in definition_imports
    assert "mymcp.memory.listing" in handler_imports
    assert "mymcp.memory.records" in handler_imports
    assert "mymcp.memory.errors" in handler_imports
    assert "mymcp.memory.service" not in handler_imports
    assert "mymcp.memory.store" not in handler_imports
    assert "mymcp.settings" not in handler_imports
    assert all(
        not imported.startswith(
            (
                "mymcp.mcp.tools.memory_recall",
                "mymcp.mcp.tools.memory_inspect",
                "mymcp.mcp.tools.memory_remember",
                "mymcp.mcp.tools.memory_archive",
                "mymcp.mcp.tools.memory_restore",
                "mymcp.mcp.tools.memory_revise",
                "mymcp.mcp.tools.memory_forget",
                "mymcp.routes",
                "fastapi",
            )
        )
        for imported in definition_imports | handler_imports
    )


def test_memory_recall_handler_uses_shared_service_and_store() -> None:
    handler_imports = _imports(RECALL_PACKAGE / "handler.py")

    assert "mymcp.memory.service" not in handler_imports
    assert "mymcp.memory.store" not in handler_imports
    assert "mymcp.settings" not in handler_imports
    assert "mymcp.mcp.tools.memory_recall.retrieval" not in handler_imports


def test_memory_remember_package_contains_only_mcp_adapter_modules() -> None:
    assert sorted(path.name for path in REMEMBER_PACKAGE.glob("*.py")) == [
        "__init__.py",
        "definition.py",
        "handler.py",
    ]


def test_memory_remember_definition_and_handler_use_only_shared_contracts() -> None:
    definition_imports = _imports(REMEMBER_PACKAGE / "definition.py")
    handler_imports = _imports(REMEMBER_PACKAGE / "handler.py")

    assert "mymcp.memory.scopes" in definition_imports
    assert "mymcp.memory.records" in definition_imports
    assert "mymcp.memory.records" in handler_imports
    assert "mymcp.memory.errors" in handler_imports
    assert "mymcp.memory.service" in handler_imports
    assert "mymcp.memory.store" not in handler_imports
    assert "mymcp.settings" not in handler_imports
    assert all(
        not imported.startswith(
            ("mymcp.mcp.tools.memory_recall", "mymcp.routes", "fastapi")
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

    assert "mymcp.memory.scopes" in definition_imports
    assert "mymcp.memory.normalization" in definition_imports
    assert "mymcp.memory.records" in handler_imports
    assert "mymcp.memory.errors" in handler_imports
    assert "mymcp.memory.service" not in handler_imports
    assert "mymcp.memory.store" not in handler_imports
    assert "mymcp.settings" not in handler_imports
    assert all(
        not imported.startswith(
            (
                "mymcp.mcp.tools.memory_recall",
                "mymcp.mcp.tools.memory_remember",
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

    assert "mymcp.memory.normalization" in helper_imports
    assert "mymcp.memory.scopes" in helper_imports
    assert "mymcp.memory.records" in helper_imports
    assert "mymcp.memory.service" in helper_imports
    assert all(
        "mymcp.mcp.tools._memory_lifecycle" in imports
        for imports in (archive_imports, restore_imports)
    )
    combined = helper_imports | archive_imports | restore_imports
    assert all(
        not imported.startswith(("mymcp.routes", "fastapi"))
        for imported in combined
    )
    assert all(
        not imported.startswith("mymcp.mcp.tools.memory_restore")
        for imported in archive_imports
    )
    assert all(
        not imported.startswith("mymcp.mcp.tools.memory_archive")
        for imported in restore_imports
    )
    assert "mymcp.memory.store" not in helper_imports
    for imports in (archive_imports, restore_imports):
        assert "mymcp.memory.records" in imports
        assert "mymcp.memory.service" in imports
        assert "mymcp.memory.store" not in imports
        assert "mymcp.settings" not in imports


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

    assert "mymcp.mcp.tools._memory_lifecycle" in helper_imports
    assert "mymcp.memory.records" in helper_imports
    assert "mymcp.memory.service" in helper_imports
    assert "mymcp.memory.store" not in helper_imports
    assert "mymcp.mcp.tools._memory_forget" in package_imports
    assert "mymcp.memory.records" in package_imports
    assert "mymcp.memory.service" in package_imports
    assert "mymcp.memory.store" not in package_imports
    assert "mymcp.settings" not in package_imports
    assert all(
        not imported.startswith(
            (
                "mymcp.mcp.tools.memory_archive",
                "mymcp.mcp.tools.memory_restore",
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

    assert "mymcp.mcp.tools._memory_lifecycle" in helper_imports
    assert "mymcp.memory.records" in helper_imports
    assert "mymcp.memory.store" not in helper_imports
    assert "mymcp.settings" not in helper_imports
    assert "mymcp.mcp.tools._memory_revise" in package_imports
    assert "mymcp.memory.records" not in package_imports
    assert "mymcp.memory.service" not in package_imports
    assert "mymcp.memory.store" not in package_imports
    assert "mymcp.settings" not in package_imports
    assert all(
        not imported.startswith(
            (
                "mymcp.mcp.tools.memory_remember",
                "mymcp.mcp.tools.memory_archive",
                "mymcp.mcp.tools.memory_restore",
                "mymcp.mcp.tools.memory_forget",
                "mymcp.routes",
                "fastapi",
            )
        )
        for imported in helper_imports | package_imports
    )

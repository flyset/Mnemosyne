import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEMORY_PACKAGE = PROJECT_ROOT / "mnemosyne" / "memory"
RECALL_PACKAGE = PROJECT_ROOT / "mnemosyne" / "mcp" / "tools" / "memory_recall"
REMEMBER_PACKAGE = PROJECT_ROOT / "mnemosyne" / "mcp" / "tools" / "memory_remember"
INSPECT_PACKAGE = PROJECT_ROOT / "mnemosyne" / "mcp" / "tools" / "memory_inspect"
ARCHIVE_PACKAGE = PROJECT_ROOT / "mnemosyne" / "mcp" / "tools" / "memory_archive"
RESTORE_PACKAGE = PROJECT_ROOT / "mnemosyne" / "mcp" / "tools" / "memory_restore"
FORGET_PACKAGE = PROJECT_ROOT / "mnemosyne" / "mcp" / "tools" / "memory_forget"
FORGET_HELPER = PROJECT_ROOT / "mnemosyne" / "mcp" / "tools" / "_memory_forget.py"
LIFECYCLE_HELPER = (
    PROJECT_ROOT / "mnemosyne" / "mcp" / "tools" / "_memory_lifecycle.py"
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


def test_shared_memory_domain_imports_no_mcp_http_or_fastapi_modules() -> None:
    forbidden = ("mnemosyne.mcp", "mnemosyne.routes", "fastapi")

    violations = {
        path.name: sorted(
            imported
            for imported in _imports(path)
            if imported.startswith(forbidden)
        )
        for path in MEMORY_PACKAGE.glob("*.py")
    }

    assert {name: imports for name, imports in violations.items() if imports} == {}


def test_memory_recall_package_contains_only_mcp_adapter_modules() -> None:
    assert sorted(path.name for path in RECALL_PACKAGE.glob("*.py")) == [
        "__init__.py",
        "definition.py",
        "handler.py",
    ]


def test_memory_recall_handler_uses_shared_service_and_store() -> None:
    handler_imports = _imports(RECALL_PACKAGE / "handler.py")

    assert "mnemosyne.memory.service" in handler_imports
    assert "mnemosyne.memory.store" in handler_imports
    assert "mnemosyne.mcp.tools.memory_recall.retrieval" not in handler_imports


def test_memory_remember_package_contains_only_mcp_adapter_modules() -> None:
    assert sorted(path.name for path in REMEMBER_PACKAGE.glob("*.py")) == [
        "__init__.py",
        "definition.py",
        "handler.py",
    ]


def test_memory_remember_definition_and_handler_use_only_shared_contracts() -> None:
    definition_imports = _imports(REMEMBER_PACKAGE / "definition.py")
    handler_imports = _imports(REMEMBER_PACKAGE / "handler.py")

    assert "mnemosyne.memory.scopes" in definition_imports
    assert "mnemosyne.memory.records" in definition_imports
    assert "mnemosyne.memory.records" in handler_imports
    assert "mnemosyne.memory.errors" in handler_imports
    assert "mnemosyne.memory.service" in handler_imports
    assert "mnemosyne.memory.store" in handler_imports
    assert "mnemosyne.settings" in handler_imports
    assert all(
        not imported.startswith(
            ("mnemosyne.mcp.tools.memory_recall", "mnemosyne.routes", "fastapi")
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

    assert "mnemosyne.memory.scopes" in definition_imports
    assert "mnemosyne.memory.normalization" in definition_imports
    assert "mnemosyne.memory.records" in handler_imports
    assert "mnemosyne.memory.errors" in handler_imports
    assert "mnemosyne.memory.service" in handler_imports
    assert "mnemosyne.memory.store" in handler_imports
    assert "mnemosyne.settings" in handler_imports
    assert all(
        not imported.startswith(
            (
                "mnemosyne.mcp.tools.memory_recall",
                "mnemosyne.mcp.tools.memory_remember",
                "mnemosyne.routes",
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

    assert "mnemosyne.memory.normalization" in helper_imports
    assert "mnemosyne.memory.scopes" in helper_imports
    assert "mnemosyne.memory.records" in helper_imports
    assert "mnemosyne.memory.service" in helper_imports
    assert all(
        "mnemosyne.mcp.tools._memory_lifecycle" in imports
        for imports in (archive_imports, restore_imports)
    )
    combined = helper_imports | archive_imports | restore_imports
    assert all(
        not imported.startswith(("mnemosyne.routes", "fastapi"))
        for imported in combined
    )
    assert all(
        not imported.startswith("mnemosyne.mcp.tools.memory_restore")
        for imported in archive_imports
    )
    assert all(
        not imported.startswith("mnemosyne.mcp.tools.memory_archive")
        for imported in restore_imports
    )
    assert "mnemosyne.memory.store" not in helper_imports
    for imports in (archive_imports, restore_imports):
        assert "mnemosyne.memory.records" in imports
        assert "mnemosyne.memory.service" in imports
        assert "mnemosyne.memory.store" in imports
        assert "mnemosyne.settings" in imports


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

    assert "mnemosyne.mcp.tools._memory_lifecycle" in helper_imports
    assert "mnemosyne.memory.records" in helper_imports
    assert "mnemosyne.memory.service" in helper_imports
    assert "mnemosyne.memory.store" not in helper_imports
    assert "mnemosyne.mcp.tools._memory_forget" in package_imports
    assert "mnemosyne.memory.records" in package_imports
    assert "mnemosyne.memory.service" in package_imports
    assert "mnemosyne.memory.store" in package_imports
    assert "mnemosyne.settings" in package_imports
    assert all(
        not imported.startswith(
            (
                "mnemosyne.mcp.tools.memory_archive",
                "mnemosyne.mcp.tools.memory_restore",
                "mnemosyne.routes",
                "fastapi",
            )
        )
        for imported in helper_imports | package_imports
    )

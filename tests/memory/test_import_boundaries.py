import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEMORY_PACKAGE = PROJECT_ROOT / "mnemosyne" / "memory"
RECALL_PACKAGE = PROJECT_ROOT / "mnemosyne" / "mcp" / "tools" / "memory_recall"


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

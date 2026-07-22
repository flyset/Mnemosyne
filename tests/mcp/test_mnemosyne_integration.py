import ast
import inspect
from pathlib import Path
from typing import Any

import pytest

from mymcp.mcp import methods
from mymcp.mcp.integrations import mnemosyne
from mymcp.mcp.integrations.mnemosyne import compose_mnemosyne_registry
from mymcp.mcp.tools import (
    memory_archive,
    memory_forget,
    memory_inspect,
    memory_list,
    memory_recall,
    memory_remember,
    memory_revise,
    memory_restore,
)
from mymcp.mcp.startup import REGISTRY as STARTUP_REGISTRY
from mymcp.memory.errors import MemorySourceUnavailable
from mymcp.settings import MemoryToolSettings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_MODULE = (
    PROJECT_ROOT / "mymcp" / "mcp" / "integrations" / "mnemosyne.py"
)
STARTUP_MODULE = PROJECT_ROOT / "mymcp" / "mcp" / "startup.py"
OLD_REGISTRY_MODULE = PROJECT_ROOT / "mymcp" / "mcp" / "tools" / "registry.py"
DEFAULT_TOOL_NAMES = [
    "list_tools",
    "memory_recall",
    "memory_list",
    "memory_inspect",
]
CANONICAL_REFERENCE = {
    "schema_version": 2,
    "scope": "project",
    "namespace_id": "mnemosyne",
    "collection_id": "decisions",
    "id": "mem_0123456789abcdef0123456789abcdef",
}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
    return imports


@pytest.mark.parametrize(
    ("settings", "suffix"),
    [
        (MemoryToolSettings(), []),
        (
            MemoryToolSettings(archive_restore_enabled=True),
            ["memory_archive", "memory_restore"],
        ),
        (MemoryToolSettings(remember_enabled=True), ["memory_remember"]),
        (MemoryToolSettings(revise_enabled=True), ["memory_revise"]),
        (MemoryToolSettings(forget_enabled=True), ["memory_forget"]),
        (
            MemoryToolSettings(
                remember_enabled=True,
                archive_restore_enabled=True,
                revise_enabled=True,
                forget_enabled=True,
            ),
            [
                "memory_archive",
                "memory_restore",
                "memory_remember",
                "memory_revise",
                "memory_forget",
            ],
        ),
    ],
)
def test_mnemosyne_composition_preserves_ordered_gate_selection(
    settings: MemoryToolSettings,
    suffix: list[str],
) -> None:
    registry = compose_mnemosyne_registry(settings)

    assert [tool["name"] for tool in registry.tools] == DEFAULT_TOOL_NAMES + suffix
    for name in suffix:
        assert registry.call_tool(name, {}) is not None


def test_mnemosyne_composition_binds_list_tools_to_the_selected_surface() -> None:
    registry = compose_mnemosyne_registry(
        MemoryToolSettings(remember_enabled=True, revise_enabled=True)
    )

    assert registry.call_tool("list_tools", {}) == {
        "content": [
            {
                "type": "text",
                "text": (
                    "Server: mnemosyne 0.1.3. Available tools: "
                    "list_tools, memory_recall, memory_list, memory_inspect, "
                    "memory_remember, memory_revise"
                ),
            }
        ]
    }


def test_startup_and_methods_share_one_composed_registry() -> None:
    assert methods.REGISTRY is STARTUP_REGISTRY


def test_integration_owns_memory_imports_while_startup_owns_no_tools() -> None:
    integration_imports = _imports(INTEGRATION_MODULE)
    startup_imports = _imports(STARTUP_MODULE)

    assert "mymcp.mcp.tools" in integration_imports
    assert "mymcp.settings" in integration_imports
    assert all(
        not imported.startswith(("mymcp.mcp.tools", "mymcp.memory"))
        for imported in startup_imports
    )
    assert not OLD_REGISTRY_MODULE.exists()


@pytest.mark.parametrize(
    ("handler", "operation_parameter"),
    [
        (memory_recall.handle, "recall_operation"),
        (memory_list.handle, "list_operation"),
        (memory_inspect.handle, "inspect_operation"),
        (memory_remember.handle, "remember_operation"),
        (memory_archive.handle, "archive_operation"),
        (memory_restore.handle, "restore_operation"),
        (memory_revise.handle, "revise_operation"),
        (memory_forget.handle, "forget_operation"),
    ],
)
def test_memory_handler_operation_seams_are_required(
    handler,
    operation_parameter: str,
) -> None:
    parameter = inspect.signature(handler).parameters[operation_parameter]

    assert parameter.default is inspect.Parameter.empty


def test_composition_and_invalid_requests_do_not_construct_memory_services(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mnemosyne,
        "get_memory_root",
        lambda: pytest.fail("memory root was resolved"),
    )
    registry = compose_mnemosyne_registry(
        MemoryToolSettings(
            remember_enabled=True,
            archive_restore_enabled=True,
            revise_enabled=True,
            forget_enabled=True,
        )
    )

    for tool_name in (
        "memory_recall",
        "memory_list",
        "memory_inspect",
        "memory_archive",
        "memory_restore",
        "memory_remember",
        "memory_revise",
        "memory_forget",
    ):
        assert registry.call_tool(tool_name, {}) is not None


def test_all_valid_memory_tool_paths_invoke_fresh_expected_operations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    roots: list[Path] = []
    stores: list[object] = []
    services: list[tuple[object, bool]] = []
    operations: list[str] = []

    class StubService:
        def __init__(self, mutations_enabled: bool) -> None:
            self.mutations_enabled = mutations_enabled

        def _called(self, name: str) -> None:
            operations.append(name)
            raise MemorySourceUnavailable

        def recall(self, *args: object, **kwargs: object) -> None:
            self._called("recall")

        def list_memories(self, *args: object, **kwargs: object) -> None:
            self._called("list")

        def inspect(self, *args: object, **kwargs: object) -> None:
            self._called("inspect")

        def archive(self, *args: object, **kwargs: object) -> None:
            self._called("archive")

        def restore(self, *args: object, **kwargs: object) -> None:
            self._called("restore")

        def remember(self, *args: object, **kwargs: object) -> None:
            self._called("remember")

        def revise(self, *args: object, **kwargs: object) -> None:
            self._called("revise")

        def forget(self, *args: object, **kwargs: object) -> None:
            self._called("forget")

    def get_root() -> Path:
        roots.append(tmp_path)
        return tmp_path

    def build_store(root: Path) -> object:
        store = object()
        assert root == tmp_path
        stores.append(store)
        return store

    def build_service(
        store: object,
        *,
        mutations_enabled: bool = False,
        **kwargs: Any,
    ) -> StubService:
        assert store is stores[-1]
        service = StubService(mutations_enabled)
        services.append((service, mutations_enabled))
        return service

    monkeypatch.setattr(mnemosyne, "get_memory_root", get_root)
    monkeypatch.setattr(mnemosyne, "FilesystemMemoryStore", build_store)
    monkeypatch.setattr(mnemosyne, "MemoryService", build_service)
    registry = compose_mnemosyne_registry(
        MemoryToolSettings(
            remember_enabled=True,
            archive_restore_enabled=True,
            revise_enabled=True,
            forget_enabled=True,
        )
    )
    remember_arguments = {
        "scope": "project",
        "namespace": {"kind": "project", "id": "mnemosyne", "label": None},
        "collection": {"id": "decisions", "label": None},
        "kind": "decision",
        "language": "en",
        "title": "Composition",
        "content": "Integration supplies a narrow operation.",
        "tags": [],
        "origin": "user_approved_proposal",
    }
    revise_arguments = {
        "reference": CANONICAL_REFERENCE,
        "expected_revision": 1,
        "namespace_label": None,
        "collection_label": None,
        "title": "Composition",
        "content": "Integration supplies a narrow operation.",
        "tags": [],
    }

    calls = [
        ("memory_recall", {"query": "composition", "scope": "project"}),
        ("memory_list", {"scope": "project"}),
        ("memory_inspect", {"reference": CANONICAL_REFERENCE}),
        (
            "memory_archive",
            {"reference": CANONICAL_REFERENCE, "expected_revision": 1},
        ),
        (
            "memory_restore",
            {"reference": CANONICAL_REFERENCE, "expected_revision": 1},
        ),
        ("memory_remember", remember_arguments),
        ("memory_revise", revise_arguments),
        (
            "memory_forget",
            {"reference": CANONICAL_REFERENCE, "expected_revision": 1},
        ),
    ]
    for tool_name, arguments in calls:
        assert registry.call_tool(tool_name, arguments) is not None

    assert operations == [
        "recall",
        "list",
        "inspect",
        "archive",
        "restore",
        "remember",
        "revise",
        "forget",
    ]
    assert roots == [tmp_path] * 8
    assert len(stores) == 8
    assert len({id(store) for store in stores}) == 8
    assert [enabled for _, enabled in services] == [
        False,
        False,
        False,
        True,
        True,
        True,
        True,
        True,
    ]
    assert len({id(service) for service, _ in services}) == 8

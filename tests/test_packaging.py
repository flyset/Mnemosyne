from importlib.resources import files
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib
from zipfile import ZipFile

from mymcp.plugin.manifest import parse_manifest_bytes


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_SOURCE = PROJECT_ROOT / "mymcp" / "plugins" / "mnemosyne"
PLUGIN_WHEEL_PREFIX = "mymcp/plugins/mnemosyne/"
TRANSITIONAL_WHEEL_PATHS = (
    "mymcp/mnemosyne/",
    "mymcp/memory/",
    "mymcp/mcp/integrations/mnemosyne.py",
    "mymcp/mcp/tools/memory_",
    "mymcp/mcp/tools/_memory_",
)


def _source_plugin_files() -> set[str]:
    return {
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in PLUGIN_SOURCE.rglob("*.py")
        if path.is_file()
    } | {"mymcp/plugins/mnemosyne/manifest.json"}


def _is_forbidden_wheel_entry(name: str) -> bool:
    return (
        name.endswith(".pyc")
        or "__pycache__" in name.split("/")
        or any(name.startswith(path) for path in TRANSITIONAL_WHEEL_PATHS)
    )


def _repository_artifact_snapshot() -> tuple[tuple[str, str, bytes | str | None], ...]:
    roots = [PROJECT_ROOT / "build", *sorted(PROJECT_ROOT.glob("*.egg-info"))]
    paths: set[Path] = set()
    for root in roots:
        if root.exists() or root.is_symlink():
            paths.add(root)
            if root.is_dir() and not root.is_symlink():
                paths.update(root.rglob("*"))

    snapshot: list[tuple[str, str, bytes | str | None]] = []
    for path in sorted(paths):
        relative_path = path.relative_to(PROJECT_ROOT).as_posix()
        if path.is_symlink():
            snapshot.append((relative_path, "symlink", path.readlink().as_posix()))
        elif path.is_file():
            snapshot.append((relative_path, "file", path.read_bytes()))
        elif path.is_dir():
            snapshot.append((relative_path, "directory", None))
        else:
            snapshot.append((relative_path, "other", None))
    return tuple(snapshot)


def test_built_wheel_contains_exact_parseable_mnemosyne_manifest(
    tmp_path: Path,
) -> None:
    existing_artifacts = _repository_artifact_snapshot()
    existing_build_directory = (PROJECT_ROOT / "build").exists()
    existing_egg_info = tuple(sorted(PROJECT_ROOT.glob("*.egg-info")))
    expected_plugin_files = _source_plugin_files()
    package_data = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["tool"]["setuptools"]["package-data"]
    assert package_data == {"mymcp.plugins.mnemosyne": ["manifest.json"]}
    source_directory = tmp_path / "source"
    wheel_directory = tmp_path / "dist"
    source_directory.mkdir()
    shutil.copy2(PROJECT_ROOT / "pyproject.toml", source_directory)
    shutil.copy2(PROJECT_ROOT / "README.md", source_directory)
    shutil.copytree(
        PROJECT_ROOT / "mymcp",
        source_directory / "mymcp",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    result = subprocess.run(
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

    assert result.returncode == 0, result.stdout + result.stderr
    wheels = tuple(wheel_directory.glob("*.whl"))
    assert len(wheels) == 1
    with ZipFile(wheels[0]) as wheel:
        wheel_names = wheel.namelist()
        assert len(wheel_names) == len(set(wheel_names))
        manifest_path = "mymcp/plugins/mnemosyne/manifest.json"
        assert wheel_names.count(manifest_path) == 1
        wheel_files = set(wheel_names)
        package_files = {
            name
            for name in wheel_files
            if name.startswith(PLUGIN_WHEEL_PREFIX)
        }
        assert package_files == expected_plugin_files
        assert not any(_is_forbidden_wheel_entry(name) for name in wheel_files)
        packaged_manifest = wheel.read(manifest_path)

    source_manifest = (
        files("mymcp.plugins.mnemosyne").joinpath("manifest.json").read_bytes()
    )
    assert packaged_manifest == source_manifest
    assert parse_manifest_bytes(packaged_manifest) == parse_manifest_bytes(
        source_manifest
    )
    assert (PROJECT_ROOT / "build").exists() is existing_build_directory
    assert tuple(sorted(PROJECT_ROOT.glob("*.egg-info"))) == existing_egg_info
    assert _repository_artifact_snapshot() == existing_artifacts

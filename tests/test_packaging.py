from importlib.resources import files
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

from mymcp.plugin.manifest import parse_manifest_bytes


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_built_wheel_contains_exact_parseable_mnemosyne_manifest(
    tmp_path: Path,
) -> None:
    existing_build_directory = (PROJECT_ROOT / "build").exists()
    existing_egg_info = tuple(sorted(PROJECT_ROOT.glob("*.egg-info")))
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
        package_files = sorted(
            name
            for name in wheel.namelist()
            if name.startswith("mymcp/plugins/mnemosyne/")
        )
        assert package_files == [
            "mymcp/plugins/mnemosyne/__init__.py",
            "mymcp/plugins/mnemosyne/manifest.json",
        ]
        packaged_manifest = wheel.read(
            "mymcp/plugins/mnemosyne/manifest.json"
        )

    source_manifest = (
        files("mymcp.plugins.mnemosyne").joinpath("manifest.json").read_bytes()
    )
    assert packaged_manifest == source_manifest
    assert parse_manifest_bytes(packaged_manifest) == parse_manifest_bytes(
        source_manifest
    )
    assert (PROJECT_ROOT / "build").exists() is existing_build_directory
    assert tuple(sorted(PROJECT_ROOT.glob("*.egg-info"))) == existing_egg_info

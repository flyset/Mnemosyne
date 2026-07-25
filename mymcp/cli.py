import subprocess
import sys
from importlib.util import find_spec


def main() -> None:
    import uvicorn

    uvicorn.run(
        "mymcp.app:create_production_app",
        host="127.0.0.1",
        port=8000,
        factory=True,
    )


def dev() -> None:
    import uvicorn

    uvicorn.run(
        "mymcp.app:create_production_app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        factory=True,
    )


def test() -> int:
    if find_spec("pytest") is None:
        print('Test support is not installed. Run: pip install -e ".[test]"')
        return 1

    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "tests"], check=False
    )
    return completed.returncode

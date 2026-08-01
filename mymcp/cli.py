import subprocess
import sys
from importlib.util import find_spec


def main() -> None:
    from mymcp.app import create_production_app
    from mymcp.host.configuration import load_host_configuration

    configuration = load_host_configuration()
    application = create_production_app(configuration)

    import uvicorn

    uvicorn.run(
        application,
        host=configuration.server.address,
        port=configuration.server.port,
    )


def dev() -> None:
    from mymcp.host.bootstrap import validate_production_configuration
    from mymcp.host.configuration import load_host_configuration

    configuration = load_host_configuration()
    validate_production_configuration(configuration)

    import uvicorn

    uvicorn.run(
        "mymcp.app:create_production_app",
        host=configuration.server.address,
        port=configuration.server.port,
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

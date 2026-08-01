from fastapi.testclient import TestClient

from mymcp.app import create_app
from mymcp.host.bootstrap import build_production_runtime
from mymcp.host.configuration import HostConfiguration
from mymcp.settings import PROTOCOL_VERSION, SERVER_NAME, SERVER_VERSION


client = TestClient(
    create_app(
        build_production_runtime(
            HostConfiguration.default(),
            generation_factory=lambda: "operational-test-generation"
        )
    )
)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_returns_server_identity() -> None:
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "name": SERVER_NAME,
        "version": SERVER_VERSION,
        "protocolVersion": PROTOCOL_VERSION,
    }

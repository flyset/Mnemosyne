from fastapi import FastAPI

from mymcp.authentication.router import Authenticator, compose_authenticator
from mymcp.host.authentication import build_production_authenticator
from mymcp.host.configuration import HostConfiguration, load_host_configuration
from mymcp.host.mcp_application import PrincipalAwareMCPApplication
from mymcp.mcp.dispatcher import MCPDispatcher, RuntimeLike
from mymcp.routes.health import router as health_router
from mymcp.routes.mcp import create_router as create_mcp_router
from mymcp.routes.version import router as version_router
from mymcp.settings import APP_TITLE


def create_app(
    runtime: RuntimeLike,
    authenticator: Authenticator | None = None,
) -> FastAPI:
    selected_authenticator = (
        compose_authenticator((), anonymous_enabled=True)
        if authenticator is None
        else authenticator
    )
    app = FastAPI(title=APP_TITLE)
    app.include_router(
        create_mcp_router(
            PrincipalAwareMCPApplication(MCPDispatcher(runtime)),
            selected_authenticator,
        )
    )
    app.include_router(health_router)
    app.include_router(version_router)
    return app


def create_production_app(
    configuration: HostConfiguration | None = None,
) -> FastAPI:
    from mymcp.host.bootstrap import build_production_runtime

    selected_configuration = (
        load_host_configuration() if configuration is None else configuration
    )
    authenticator = build_production_authenticator(selected_configuration)
    runtime = build_production_runtime(selected_configuration)
    return create_app(runtime, authenticator)

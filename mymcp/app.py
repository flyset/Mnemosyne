from fastapi import FastAPI

from mymcp.mcp.dispatcher import MCPDispatcher, RuntimeLike
from mymcp.routes.health import router as health_router
from mymcp.routes.mcp import create_router as create_mcp_router
from mymcp.routes.version import router as version_router
from mymcp.settings import APP_TITLE


def create_app(runtime: RuntimeLike) -> FastAPI:
    app = FastAPI(title=APP_TITLE)
    app.include_router(create_mcp_router(MCPDispatcher(runtime)))
    app.include_router(health_router)
    app.include_router(version_router)
    return app


def create_production_app() -> FastAPI:
    from mymcp.host.bootstrap import build_production_runtime

    return create_app(build_production_runtime())

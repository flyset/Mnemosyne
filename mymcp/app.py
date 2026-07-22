from fastapi import FastAPI

from mymcp.routes.health import router as health_router
from mymcp.routes.mcp import router as mcp_router
from mymcp.routes.version import router as version_router
from mymcp.settings import APP_TITLE


def create_app() -> FastAPI:
    app = FastAPI(title=APP_TITLE)
    app.include_router(mcp_router)
    app.include_router(health_router)
    app.include_router(version_router)
    return app


app = create_app()

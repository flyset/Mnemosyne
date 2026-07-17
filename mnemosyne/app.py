from fastapi import FastAPI

from mnemosyne.routes.health import router as health_router
from mnemosyne.routes.mcp import router as mcp_router
from mnemosyne.routes.version import router as version_router
from mnemosyne.settings import APP_TITLE


def create_app() -> FastAPI:
    app = FastAPI(title=APP_TITLE)
    app.include_router(mcp_router)
    app.include_router(health_router)
    app.include_router(version_router)
    return app


app = create_app()

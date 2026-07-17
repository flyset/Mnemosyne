from fastapi import APIRouter

from mnemosyne.settings import PROTOCOL_VERSION, SERVER_NAME, SERVER_VERSION

router = APIRouter()


@router.get("/version")
async def version() -> dict[str, str]:
    return {
        "name": SERVER_NAME,
        "version": SERVER_VERSION,
        "protocolVersion": PROTOCOL_VERSION,
    }

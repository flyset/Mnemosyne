"""Thin OAuth protected-resource metadata route (``/.well-known/oauth-protected-resource/mcp``).

This module owns the single RFC 9728-shaped protected-resource metadata endpoint
served only when the process's Authentication method is enabled OAuth. It holds
no policy or protocol semantics: it is bound to an explicitly supplied,
immutable ``OAuthProtectedResource`` value derived by the application factory
from validated host configuration. The handler emits exactly the approved JSON
members with ``Cache-Control: no-store``; it never reads request Host or
forwarded headers to build the resource identity.
"""

from dataclasses import dataclass

from fastapi import APIRouter
from fastapi.responses import JSONResponse

PROTECTED_RESOURCE_PATH = "/.well-known/oauth-protected-resource/mcp"


@dataclass(frozen=True, slots=True)
class OAuthProtectedResource:
    """Immutable identity of this process as an RFC 9728 protected resource.

    The ``resource`` and the metadata URL derive only from validated loopback
    server configuration; ``authorization_servers`` carries the one configured
    external authorization-server issuer. All values are deliberately small,
    fixed, and secret-free.
    """

    resource: str
    authorization_servers: tuple[str, ...]
    metadata_url: str

    def __post_init__(self) -> None:
        if (
            type(self.resource) is not str
            or not self.resource
            or type(self.metadata_url) is not str
            or not self.metadata_url
            or type(self.authorization_servers) is not tuple
            or len(self.authorization_servers) != 1
            or any(type(issuer) is not str for issuer in self.authorization_servers)
        ):
            raise ValueError("invalid oauth protected resource")


def create_router(protected_resource: OAuthProtectedResource) -> APIRouter:
    """Build the GET-only protected-resource metadata router.

    The response body is the exact RFC 9728 set ``resource``, a one-element
    ``authorization_servers``, and ``bearer_methods_supported=["header"]`` with
    no scopes and no additional fields.
    """
    if not isinstance(protected_resource, OAuthProtectedResource):
        raise TypeError("invalid oauth protected resource")

    router = APIRouter()
    body = {
        "resource": protected_resource.resource,
        "authorization_servers": list(protected_resource.authorization_servers),
        "bearer_methods_supported": ["header"],
    }

    @router.get(PROTECTED_RESOURCE_PATH)
    async def protected_resource_metadata() -> JSONResponse:
        return JSONResponse(body, headers={"Cache-Control": "no-store"})

    return router
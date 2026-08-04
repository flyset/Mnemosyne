from fastapi import FastAPI

from mymcp.authentication.oauth import (
    derive_oauth_metadata_url,
    derive_oauth_resource,
)
from mymcp.authentication.router import Authenticator, compose_authenticator
from mymcp.host.authentication import build_production_authenticator
from mymcp.host.configuration import (
    OAUTH_JWT_ADAPTER_TYPE,
    HostConfiguration,
    load_host_configuration,
)
from mymcp.host.mcp_application import PrincipalAwareMCPApplication
from mymcp.host.runtime import RuntimeGenerationId
from mymcp.host.sessions import ProcessLocalSessionStore
from mymcp.mcp.dispatcher import MCPDispatcher, RuntimeLike
from mymcp.routes.health import router as health_router
from mymcp.routes.mcp import create_router as create_mcp_router
from mymcp.routes.oauth import OAuthProtectedResource
from mymcp.routes.oauth import create_router as create_oauth_router
from mymcp.routes.version import router as version_router
from mymcp.settings import APP_TITLE


def _oauth_protected_resource(
    configuration: HostConfiguration,
) -> OAuthProtectedResource | None:
    """Derive the immutable OAuth resource surface from validated configuration.

    The protected resource exists only for enabled schema-5 OAuth; every other
    configuration (anonymous, operator-bearer, disabled OAuth, schemas 1-4)
    stays route- and challenge-free. Resource and metadata URL derive only from
    validated loopback server configuration.
    """
    oauth_configuration = configuration.authentication.oauth_jwt
    if oauth_configuration is None:
        return None
    if not any(
        declaration.enabled and declaration.adapter_type == OAUTH_JWT_ADAPTER_TYPE
        for declaration in configuration.authentication.adapters
    ):
        return None
    address = configuration.server.address
    port = configuration.server.port
    return OAuthProtectedResource(
        resource=derive_oauth_resource(address, port),
        authorization_servers=(oauth_configuration.issuer,),
        metadata_url=derive_oauth_metadata_url(address, port),
    )


def create_app(
    runtime: RuntimeLike,
    authenticator: Authenticator | None = None,
    *,
    oauth_protected_resource: OAuthProtectedResource | None = None,
    strict_protocol_version: bool = True,
    session_inactivity_timeout_seconds: int | None = 1800,
    session_absolute_lifetime_seconds: int | None = 28800,
) -> FastAPI:
    selected_authenticator = (
        compose_authenticator((), anonymous_enabled=True)
        if authenticator is None
        else authenticator
    )
    app = FastAPI(title=APP_TITLE)
    generation = getattr(runtime, "generation", None)
    selected_generation = (
        generation
        if isinstance(generation, RuntimeGenerationId)
        else RuntimeGenerationId("application-default")
    )
    app.include_router(
        create_mcp_router(
            PrincipalAwareMCPApplication(
                MCPDispatcher(runtime),
                selected_generation,
                ProcessLocalSessionStore(
                    selected_generation,
                    inactivity_timeout_seconds=session_inactivity_timeout_seconds,
                    absolute_lifetime_seconds=session_absolute_lifetime_seconds,
                ),
                strict_protocol_version,
            ),
            selected_authenticator,
            oauth_resource_metadata_url=(
                oauth_protected_resource.metadata_url
                if oauth_protected_resource is not None
                else None
            ),
        )
    )
    if oauth_protected_resource is not None:
        app.include_router(create_oauth_router(oauth_protected_resource))
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
    oauth_protected_resource = _oauth_protected_resource(selected_configuration)
    if oauth_protected_resource is None:
        return create_app(
            runtime,
            authenticator,
            strict_protocol_version=selected_configuration.mcp.strict_protocol_version,
            session_inactivity_timeout_seconds=(
                selected_configuration.mcp.session_inactivity_timeout_seconds
            ),
            session_absolute_lifetime_seconds=(
                selected_configuration.mcp.session_absolute_lifetime_seconds
            ),
        )
    return create_app(
        runtime,
        authenticator,
        oauth_protected_resource=oauth_protected_resource,
        strict_protocol_version=selected_configuration.mcp.strict_protocol_version,
        session_inactivity_timeout_seconds=(
            selected_configuration.mcp.session_inactivity_timeout_seconds
        ),
        session_absolute_lifetime_seconds=(
            selected_configuration.mcp.session_absolute_lifetime_seconds
        ),
    )

import logging
import time

from mymcp.authentication.adapters.operator_bearer import (
    OperatorBearerAdapter,
    OperatorBearerVerifierSourceError,
    load_operator_bearer_verifier_source,
)
from mymcp.authentication.contracts import EvidenceRoute
from mymcp.authentication.router import (
    AdapterRegistration,
    Authenticator,
    compose_authenticator,
)
from mymcp.host.configuration import (
    OAUTH_JWT_ADAPTER_TYPE,
    OPERATOR_BEARER_ADAPTER_TYPE,
    HostConfiguration,
)


_OPERATOR_BEARER_ROUTE = EvidenceRoute("authorization", "bearer", None)
_OAUTH_ROUTE = EvidenceRoute("authorization", "bearer", None)

# Injectable startup seams for deterministic offline tests. ``_OAUTH_CLOCK`` is
# always callable and returns integer epoch seconds; ``_OAUTH_DISCOVERY_FETCH``
# is resolved lazily to the concrete bounded HTTPS fetch on first use so that
# ordinary (non-OAuth) startup never loads the OAuth/PyJWT runtime.
_OAUTH_CLOCK = lambda: int(time.time())  # noqa: E731
_OAUTH_DISCOVERY_FETCH = None

_LOGGER = logging.getLogger("mymcp.host.authentication")

_COMPOSITION_ERROR_MESSAGES = {
    "adapter_type_unavailable": "enabled authentication adapter type is unavailable",
    "verifier_source": "operator bearer verifier source is unavailable",
    "route_invalid": "operator bearer adapter route is invalid",
    "oauth_route_invalid": "oauth jwt adapter route is invalid",
    "oauth_validation_source": "OAuth validation material is unavailable",
    "oauth_resource": "OAuth resource identity is unavailable",
    "oauth_configuration": "OAuth validation configuration is invalid",
    "anonymous_access_enabled": (
        "enabled OAuth authentication requires anonymous access disabled"
    ),
    "route_collision": "operator bearer adapter route collision",
}


class HostAuthenticationCompositionError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(_COMPOSITION_ERROR_MESSAGES[code])


def build_production_authenticator(
    configuration: HostConfiguration,
) -> Authenticator:
    if not isinstance(configuration, HostConfiguration):
        raise ValueError("invalid host authentication composition input")
    try:
        authenticator = _build_production_authenticator(configuration)
    except HostAuthenticationCompositionError as error:
        _LOGGER.error(
            "authentication_composition outcome=error code=%s",
            error.code,
        )
        raise
    _LOGGER.info(
        "authentication_composition outcome=loaded enabled=%s",
        len(authenticator.registrations),
    )
    return authenticator


def _build_oauth_jwt_adapter(
    configuration: HostConfiguration,
    declaration,
) -> object:
    from mymcp.authentication.adapters.oauth_discovery import (
        OAuthDiscoveryError,
        bounded_https_fetch,
        load_oauth_validation_material,
    )
    from mymcp.authentication.adapters.oauth_jwt import (
        OAuthJwtAdapter,
        OAuthJwtConfig,
    )
    from mymcp.authentication.oauth import derive_oauth_resource

    oauth_config = configuration.authentication.oauth_jwt
    if oauth_config is None:
        raise HostAuthenticationCompositionError("adapter_type_unavailable")
    if declaration.route != _OAUTH_ROUTE:
        raise HostAuthenticationCompositionError("oauth_route_invalid")
    if configuration.authentication.anonymous_enabled:
        raise HostAuthenticationCompositionError("anonymous_access_enabled")

    fetch = _OAUTH_DISCOVERY_FETCH
    if fetch is None:
        fetch = bounded_https_fetch
    try:
        snapshot = load_oauth_validation_material(oauth_config.issuer, fetch)
    except OAuthDiscoveryError:
        raise HostAuthenticationCompositionError("oauth_validation_source") from None

    try:
        audience = derive_oauth_resource(
            configuration.server.address,
            configuration.server.port,
        )
    except ValueError:
        raise HostAuthenticationCompositionError("oauth_resource") from None

    try:
        adapter = OAuthJwtAdapter(
            OAuthJwtConfig(
                issuer=oauth_config.issuer,
                audience=audience,
                snapshot=snapshot,
                clock=_OAUTH_CLOCK,
            )
        )
    except ValueError:
        raise HostAuthenticationCompositionError("oauth_configuration") from None
    if adapter.route != _OAUTH_ROUTE:
        raise HostAuthenticationCompositionError("oauth_route_invalid")
    return adapter


def _build_production_authenticator(
    configuration: HostConfiguration,
) -> Authenticator:
    registrations: list[AdapterRegistration] = []
    for declaration in configuration.authentication.adapters:
        if not declaration.enabled:
            continue
        if declaration.adapter_type == OPERATOR_BEARER_ADAPTER_TYPE:
            if configuration.authentication.operator_bearer is None:
                raise HostAuthenticationCompositionError("adapter_type_unavailable")
            if declaration.route != _OPERATOR_BEARER_ROUTE:
                raise HostAuthenticationCompositionError("route_invalid")
            try:
                verifier = load_operator_bearer_verifier_source(
                    configuration.authentication.operator_bearer.verifier_path
                )
            except OperatorBearerVerifierSourceError:
                raise HostAuthenticationCompositionError("verifier_source") from None
            adapter = OperatorBearerAdapter(verifier)
            if adapter.route != _OPERATOR_BEARER_ROUTE:
                raise HostAuthenticationCompositionError("route_invalid")
            registrations.append(
                AdapterRegistration(declaration.adapter_id, declaration.route, adapter)
            )
        elif declaration.adapter_type == OAUTH_JWT_ADAPTER_TYPE:
            adapter = _build_oauth_jwt_adapter(configuration, declaration)
            registrations.append(
                AdapterRegistration(declaration.adapter_id, declaration.route, adapter)
            )
        else:
            raise HostAuthenticationCompositionError("adapter_type_unavailable")
    try:
        return compose_authenticator(
            registrations,
            anonymous_enabled=configuration.authentication.anonymous_enabled,
        )
    except ValueError:
        raise HostAuthenticationCompositionError("route_collision") from None
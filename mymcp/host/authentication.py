import logging

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
    OPERATOR_BEARER_ADAPTER_TYPE,
    HostConfiguration,
)


_OPERATOR_BEARER_ROUTE = EvidenceRoute("authorization", "bearer", None)

_LOGGER = logging.getLogger("mymcp.host.authentication")

_COMPOSITION_ERROR_MESSAGES = {
    "adapter_type_unavailable": "enabled authentication adapter type is unavailable",
    "verifier_source": "operator bearer verifier source is unavailable",
    "route_invalid": "operator bearer adapter route is invalid",
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


def _build_production_authenticator(
    configuration: HostConfiguration,
) -> Authenticator:
    registrations: list[AdapterRegistration] = []
    for declaration in configuration.authentication.adapters:
        if not declaration.enabled:
            continue
        if (
            declaration.adapter_type != OPERATOR_BEARER_ADAPTER_TYPE
            or configuration.authentication.operator_bearer is None
        ):
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
    try:
        return compose_authenticator(
            registrations,
            anonymous_enabled=configuration.authentication.anonymous_enabled,
        )
    except ValueError:
        raise HostAuthenticationCompositionError("route_collision") from None

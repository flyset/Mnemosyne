from mymcp.authentication.router import Authenticator, compose_authenticator
from mymcp.host.configuration import HostConfiguration


class HostAuthenticationCompositionError(ValueError):
    pass


def build_production_authenticator(
    configuration: HostConfiguration,
) -> Authenticator:
    if not isinstance(configuration, HostConfiguration):
        raise ValueError("invalid host authentication composition input")
    if any(adapter.enabled for adapter in configuration.authentication.adapters):
        raise HostAuthenticationCompositionError(
            "enabled authentication adapter type is unavailable"
        )
    return compose_authenticator(
        (),
        anonymous_enabled=configuration.authentication.anonymous_enabled,
    )

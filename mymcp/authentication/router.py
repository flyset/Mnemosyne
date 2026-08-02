from collections.abc import Iterable
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from mymcp.authentication.contracts import (
    AdapterId,
    AuthenticationAdapter,
    AuthenticationEvidence,
    AuthenticationFailure,
    AuthenticationRequestContext,
    AuthenticationSuccess,
    EvidenceRoute,
    Principal,
)


@dataclass(frozen=True, slots=True)
class AdapterRegistration:
    adapter_id: AdapterId
    route: EvidenceRoute
    adapter: AuthenticationAdapter

    def __post_init__(self) -> None:
        if (
            not isinstance(self.adapter_id, AdapterId)
            or not isinstance(self.route, EvidenceRoute)
            or not isinstance(self.adapter, AuthenticationAdapter)
            or not callable(getattr(self.adapter, "authenticate", None))
        ):
            raise ValueError("invalid adapter registration")


@dataclass(frozen=True, slots=True, init=False)
class Authenticator:
    anonymous_enabled: bool
    registrations: tuple[AdapterRegistration, ...]
    _by_route: Mapping[EvidenceRoute, AdapterRegistration]

    def authenticate(
        self,
        evidence: AuthenticationEvidence | None,
        context: AuthenticationRequestContext,
    ) -> Principal | AuthenticationFailure:
        if (
            evidence is not None and not isinstance(evidence, AuthenticationEvidence)
        ) or not isinstance(context, AuthenticationRequestContext):
            raise ValueError("invalid authentication request")
        if evidence is None:
            if self.anonymous_enabled:
                return Principal.anonymous()
            return AuthenticationFailure("no_evidence")

        registration = self._by_route.get(evidence.route)
        if registration is None:
            return AuthenticationFailure("unsupported")
        try:
            result = registration.adapter.authenticate(evidence, context)
        except Exception:
            return AuthenticationFailure("rejected")
        if isinstance(result, AuthenticationSuccess):
            return Principal.registered(registration.adapter_id, result.subject)
        if isinstance(result, AuthenticationFailure):
            return result
        return AuthenticationFailure("rejected")


def compose_authenticator(
    registrations: Iterable[AdapterRegistration],
    *,
    anonymous_enabled: bool,
) -> Authenticator:
    selected = tuple(registrations)
    if type(anonymous_enabled) is not bool:
        raise ValueError("invalid anonymous enablement")
    if any(not isinstance(item, AdapterRegistration) for item in selected):
        raise ValueError("invalid adapter registration")

    identities: set[AdapterId] = set()
    by_route: dict[EvidenceRoute, AdapterRegistration] = {}
    for registration in selected:
        if registration.adapter_id in identities:
            raise ValueError("duplicate adapter id")
        if registration.route in by_route:
            raise ValueError("duplicate evidence route")
        identities.add(registration.adapter_id)
        by_route[registration.route] = registration

    authenticator = object.__new__(Authenticator)
    object.__setattr__(authenticator, "anonymous_enabled", anonymous_enabled)
    object.__setattr__(authenticator, "registrations", selected)
    object.__setattr__(authenticator, "_by_route", MappingProxyType(by_route))
    return authenticator

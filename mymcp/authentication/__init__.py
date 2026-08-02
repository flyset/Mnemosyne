from mymcp.authentication.contracts import (
    AdapterId,
    AuthenticationAdapter,
    AuthenticationEvidence,
    AuthenticationFailure,
    AuthenticationRequestContext,
    AuthenticationSuccess,
    EvidenceRoute,
    Principal,
    PrincipalKind,
)
from mymcp.authentication.router import (
    AdapterRegistration,
    Authenticator,
    compose_authenticator,
)

__all__ = (
    "AdapterId",
    "AdapterRegistration",
    "AuthenticationAdapter",
    "AuthenticationEvidence",
    "AuthenticationFailure",
    "AuthenticationRequestContext",
    "AuthenticationSuccess",
    "Authenticator",
    "EvidenceRoute",
    "Principal",
    "PrincipalKind",
    "compose_authenticator",
)

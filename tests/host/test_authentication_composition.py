import base64
import hashlib
import json
import logging
import os
from pathlib import Path

import pytest

import mymcp.host.authentication as host_authentication
from mymcp.authentication.adapters.operator_bearer import OperatorBearerAdapter
from mymcp.authentication.contracts import (
    AuthenticationEvidence,
    AuthenticationRequestContext,
    EvidenceRoute,
    Principal,
    PrincipalKind,
)
from mymcp.authentication.router import Authenticator
from mymcp.host.authentication import (
    HostAuthenticationCompositionError,
    build_production_authenticator,
)
from mymcp.host.configuration import HostConfigurationError, parse_host_configuration_toml


AUTHENTICATION_LOGGER = "mymcp.host.authentication"
_SECRET = bytes(range(32))
_CREDENTIAL_ID = "a" * 32
_SUBJECT = "stable-subject"
_EXACT_ROUTE = EvidenceRoute("authorization", "bearer", None)


def _digest_text() -> str:
    return (
        base64.urlsafe_b64encode(hashlib.sha256(_SECRET).digest())
        .rstrip(b"=")
        .decode("ascii")
    )


def _secret_text() -> str:
    return base64.urlsafe_b64encode(_SECRET).rstrip(b"=").decode("ascii")


def _credential_text() -> str:
    return f"mymcp1.{_CREDENTIAL_ID}.{_secret_text()}"


def _write_verifier(tmp_path: Path) -> Path:
    source = tmp_path / "verifier.json"
    source.write_text(
        json.dumps(
            {
                "format_version": 1,
                "credentials": [
                    {
                        "id": _CREDENTIAL_ID,
                        "subject": _SUBJECT,
                        "digest": _digest_text(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    os.chmod(source, 0o600)
    return source


def _schema_v4_configuration(
    *,
    verifier_path: str,
    enabled: bool = True,
    adapter_type: str = "operator-bearer-v1",
    route: str = 'route = {source = "authorization", scheme = "bearer"}',
    adapter_id: str = "local-client",
    anonymous_enabled: bool = True,
    operator_bearer: bool = True,
):
    operator_bearer_source = (
        f"""
[authentication.operator_bearer]
verifier_path = "{verifier_path}"
"""
        if operator_bearer
        else ""
    )
    source = f"""
schema_version = 4
[authentication]
anonymous_enabled = {str(anonymous_enabled).lower()}
[[authentication.adapters]]
id = "{adapter_id}"
type = "{adapter_type}"
enabled = {str(enabled).lower()}
{route}
{operator_bearer_source}"""
    return parse_host_configuration_toml(source)


def test_stable_operator_bearer_adapter_type_is_exposed() -> None:
    assert host_authentication.OPERATOR_BEARER_ADAPTER_TYPE == "operator-bearer-v1"


def test_composition_rejects_invalid_input() -> None:
    with pytest.raises(
        ValueError,
        match="^invalid host authentication composition input$",
    ):
        build_production_authenticator(None)  # type: ignore[arg-type]


def test_schema_v4_anonymous_only_composition_preserves_anonymous_flag() -> None:
    configuration = parse_host_configuration_toml(
        """
schema_version = 4
[authentication]
anonymous_enabled = false
"""
    )

    authenticator = build_production_authenticator(configuration)

    assert isinstance(authenticator, Authenticator)
    assert authenticator.registrations == ()
    assert authenticator.anonymous_enabled is False


def test_enabled_operator_bearer_adapter_composes_with_exact_route(
    tmp_path: Path,
) -> None:
    verifier_path = _write_verifier(tmp_path)
    configuration = _schema_v4_configuration(verifier_path=str(verifier_path))

    authenticator = build_production_authenticator(configuration)

    assert isinstance(authenticator, Authenticator)
    assert len(authenticator.registrations) == 1
    registration = authenticator.registrations[0]
    assert registration.adapter_id.value == "local-client"
    assert registration.route == _EXACT_ROUTE
    assert isinstance(registration.adapter, OperatorBearerAdapter)
    assert registration.adapter.route == _EXACT_ROUTE
    assert authenticator.anonymous_enabled is True


def test_enabled_operator_bearer_authenticator_verifies_valid_credential(
    tmp_path: Path,
) -> None:
    verifier_path = _write_verifier(tmp_path)
    configuration = _schema_v4_configuration(verifier_path=str(verifier_path))

    authenticator = build_production_authenticator(configuration)
    principal = authenticator.authenticate(
        AuthenticationEvidence(_EXACT_ROUTE, _credential_text().encode("ascii")),
        AuthenticationRequestContext("POST", "mcp"),
    )

    assert isinstance(principal, Principal)
    assert principal.kind is PrincipalKind.REGISTERED
    assert principal.adapter_id is not None
    assert principal.adapter_id.value == "local-client"
    assert principal.subject == _SUBJECT


def test_disabled_operator_bearer_declaration_never_accesses_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing = tmp_path / "missing.json"
    configuration = _schema_v4_configuration(
        verifier_path=str(missing),
        enabled=False,
    )
    monkeypatch.setattr(
        host_authentication,
        "load_operator_bearer_verifier_source",
        lambda _path: pytest.fail("disabled declaration accessed the verifier source"),
    )

    authenticator = build_production_authenticator(configuration)

    assert authenticator.registrations == ()
    assert authenticator.anonymous_enabled is True


@pytest.mark.parametrize(
    "route",
    [
        'route = {source = "authorization", scheme = "bearer", profile = "local"}',
        'route = {source = "authorization", scheme = "basic"}',
    ],
)
def test_enabled_operator_bearer_adapter_requires_the_exact_route(
    route: str,
    tmp_path: Path,
) -> None:
    verifier_path = _write_verifier(tmp_path)
    configuration = _schema_v4_configuration(verifier_path=str(verifier_path), route=route)

    with pytest.raises(HostAuthenticationCompositionError) as captured:
        build_production_authenticator(configuration)

    assert captured.value.code == "route_invalid"
    assert str(captured.value) == "operator bearer adapter route is invalid"


def test_enabled_unavailable_adapter_type_retains_bounded_failure(
    tmp_path: Path,
) -> None:
    verifier_path = _write_verifier(tmp_path)
    configuration = _schema_v4_configuration(
        verifier_path=str(verifier_path),
        adapter_type="synthetic",
        operator_bearer=False,
    )

    with pytest.raises(HostAuthenticationCompositionError) as captured:
        build_production_authenticator(configuration)

    assert captured.value.code == "adapter_type_unavailable"
    assert str(captured.value) == "enabled authentication adapter type is unavailable"


def test_verifier_source_failure_is_bounded_and_content_free(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.json"
    configuration = _schema_v4_configuration(verifier_path=str(missing))

    with pytest.raises(HostAuthenticationCompositionError) as captured:
        build_production_authenticator(configuration)

    assert captured.value.code == "verifier_source"
    assert str(captured.value) == "operator bearer verifier source is unavailable"
    assert str(missing) not in str(captured.value)
    assert str(missing) not in repr(captured.value)


def test_route_collision_fails_closed_at_configuration(tmp_path: Path) -> None:
    verifier_path = _write_verifier(tmp_path)
    source = f"""
schema_version = 4
[authentication]
anonymous_enabled = true
[[authentication.adapters]]
id = "first"
type = "operator-bearer-v1"
enabled = true
route = {{source = "authorization", scheme = "bearer"}}
[[authentication.adapters]]
id = "second"
type = "operator-bearer-v1"
enabled = true
route = {{source = "authorization", scheme = "bearer"}}
[authentication.operator_bearer]
verifier_path = "{verifier_path}"
"""

    with pytest.raises(HostConfigurationError) as captured:
        parse_host_configuration_toml(source)

    assert captured.value.code == "duplicate_authentication_adapter_route"


def test_composition_emits_one_bounded_loaded_event(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    verifier_path = _write_verifier(tmp_path)
    configuration = _schema_v4_configuration(verifier_path=str(verifier_path))

    with caplog.at_level(logging.INFO, logger=AUTHENTICATION_LOGGER):
        build_production_authenticator(configuration)

    records = [
        record.getMessage()
        for record in caplog.records
        if record.name == AUTHENTICATION_LOGGER
    ]
    assert records == ["authentication_composition outcome=loaded enabled=1"]


def test_composition_emits_one_bounded_error_event(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    missing = tmp_path / "missing.json"
    configuration = _schema_v4_configuration(verifier_path=str(missing))

    with caplog.at_level(logging.ERROR, logger=AUTHENTICATION_LOGGER):
        with pytest.raises(HostAuthenticationCompositionError):
            build_production_authenticator(configuration)

    records = [
        record.getMessage()
        for record in caplog.records
        if record.name == AUTHENTICATION_LOGGER
    ]
    assert records == ["authentication_composition outcome=error code=verifier_source"]


def test_composition_error_log_omits_source_and_credential_material(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    missing = tmp_path / "private-verifier.json"
    configuration = _schema_v4_configuration(verifier_path=str(missing))

    with caplog.at_level(logging.ERROR, logger=AUTHENTICATION_LOGGER):
        with pytest.raises(HostAuthenticationCompositionError):
            build_production_authenticator(configuration)

    rendered = " ".join(
        record.getMessage()
        for record in caplog.records
        if record.name == AUTHENTICATION_LOGGER
    )
    assert "private-verifier" not in rendered
    assert _secret_text() not in rendered
    assert _CREDENTIAL_ID not in rendered
    assert _SUBJECT not in rendered

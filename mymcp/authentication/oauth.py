"""Standard-library-only OAuth host integration helpers.

This module owns the canonical, transport-neutral OAuth *issuer* and loopback
*resource* identity rules shared between strict host configuration parsing and
production Authentication composition. It is standard-library-only so that
ordinary MyMCP startup never loads the ``PyJWT[crypto]`` runtime solely to
validate configuration or derive a resource identity. The concrete OAuth
adapter package re-imports ``validate_oauth_issuer`` and ``OAUTH_JWT_PROFILE``
from here to keep a single source of truth; it is never re-exported from
``mymcp.authentication``.
"""

import ipaddress
from urllib.parse import urlsplit

OAUTH_JWT_PROFILE = "oauth-jwt-jwks-v1"


def _valid_dns_labels(host: str) -> bool:
    """Reject empty, trailing-dot, double-dot, oversized, or non-label-safe hosts.

    Numeric labels (e.g. ``123``) are valid DNS labels and are allowed when the
    hostname has at least one alphabetic label; a host composed solely of numeric
    labels would be an IPv4 literal, which is explicitly rejected.
    """
    if not host or host.endswith("."):
        return False
    labels = host.split(".")
    if not labels:
        return False
    numeric_label_count = 0
    for label in labels:
        if not 1 <= len(label) <= 63:
            return False
        if not all(character.isalnum() or character == "-" for character in label):
            return False
        if label[0] == "-" or label[-1] == "-":
            return False
        if all(character.isdigit() for character in label):
            numeric_label_count += 1
    if numeric_label_count == len(labels):
        return False
    return True


def validate_oauth_issuer(value: object) -> str:
    """Validate and return one canonical HTTPS issuer URI."""
    if not isinstance(value, str) or not value or not value.isascii():
        raise ValueError("invalid oauth issuer")
    try:
        parts = urlsplit(value)
    except ValueError:
        raise ValueError("invalid oauth issuer") from None
    if parts.scheme != "https":
        raise ValueError("invalid oauth issuer")
    if parts.username is not None or parts.password is not None:
        raise ValueError("invalid oauth issuer")
    if parts.query or parts.fragment or "%" in value:
        raise ValueError("invalid oauth issuer")
    netloc = parts.netloc
    if not netloc or netloc != netloc.lower():
        raise ValueError("invalid oauth issuer")
    if "[" in netloc or "]" in netloc:
        raise ValueError("invalid oauth issuer")
    host, separator, port_text = netloc.rpartition(":")
    if separator:
        if port_text != "443":
            raise ValueError("invalid oauth issuer")
    else:
        host, port_text = netloc, ""
    if not host or host != host.lower() or "." not in host:
        raise ValueError("invalid oauth issuer")
    if host == "localhost" or host.endswith(".localhost"):
        raise ValueError("invalid oauth issuer")
    if not _valid_dns_labels(host):
        raise ValueError("invalid oauth issuer")
    path = parts.path
    if path and path != "/" and path.endswith("/"):
        raise ValueError("invalid oauth issuer")
    if path:
        segments = path.split("/")
        if segments and segments[0] == "":
            segments = segments[1:]
        if any(segment in ("", ".", "..") for segment in segments):
            raise ValueError("invalid oauth issuer")
    return value


def derive_oauth_resource(address: str, port: int) -> str:
    """Derive the canonical loopback OAuth resource/audience URI for a server.

    Client-access-protected resource identities derive only from validated
    loopback server configuration, never from request Host or forwarded headers.
    IPv4 uses the dotted form; IPv6 uses the compressed form in brackets:
    ``http://<IPv4>:<port>/mcp`` or ``http://[<compressed-IPv6>]:<port>/mcp``.
    """
    if isinstance(port, bool) or type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("invalid oauth resource")
    try:
        parsed = ipaddress.ip_address(address)
    except (TypeError, ValueError):
        raise ValueError("invalid oauth resource") from None
    if not parsed.is_loopback:
        raise ValueError("invalid oauth resource")
    if parsed.version == 4:
        host = str(parsed)
    else:
        host = f"[{parsed.compressed}]"
    return f"http://{host}:{port}/mcp"


def derive_oauth_metadata_url(address: str, port: int) -> str:
    """Derive the loopback protected-resource metadata URL for a server.

    The metadata endpoint derives from the same validated loopback resource
    identity as ``derive_oauth_resource``; request-controlled Host or forwarded
    headers never influence it. IPv4 uses the dotted form and IPv6 the
    compressed bracketed form: ``http://<IPv4>:<port>/.well-known/oauth-protected-resource/mcp``
    or ``http://[<compressed-IPv6>]:<port>/.well-known/oauth-protected-resource/mcp``.
    """
    resource = derive_oauth_resource(address, port)
    return resource[: -len("/mcp")] + "/.well-known/oauth-protected-resource/mcp"
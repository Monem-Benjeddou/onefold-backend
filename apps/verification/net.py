"""
Outbound HTTP for checks, hardened against SSRF.

Builders give us URLs, so every fetch:
- allows only http/https, with no credentials in the URL;
- resolves DNS once and refuses any address that isn't public (private,
  loopback, link-local, cloud metadata, multicast, reserved; IPv4 and IPv6);
- connects to that exact resolved IP (no second lookup, so DNS rebinding
  can't swap in an internal address), keeping the hostname for Host and TLS SNI;
- never follows redirects (a 3xx is reported back as-is);
- caps time and body size.
"""

import http.client
import ipaddress
import socket
import ssl
import time
from dataclasses import dataclass
from urllib.parse import urlsplit

USER_AGENT = "OnefoldCheck/1.0 (+https://onefold.example/checks)"
MAX_TIMEOUT_S = 10.0


class BlockedURL(Exception):
    """The URL points somewhere we refuse to connect to."""


class FetchError(Exception):
    """The request could not complete (DNS, connect, TLS, timeout)."""


@dataclass
class FetchResult:
    status: int
    reason: str
    headers: dict
    body: bytes
    truncated: bool
    elapsed_ms: int
    ip: str


def is_public_ip(value):
    ip = ipaddress.ip_address(value)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


def resolve_public_ip(host, port):
    """Resolve `host` and return one address, refusing if any is non-public."""
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise FetchError(f"Couldn't resolve {host}") from exc
    addresses = {info[4][0] for info in infos}
    if not addresses:
        raise FetchError(f"Couldn't resolve {host}")
    blocked = sorted(a for a in addresses if not is_public_ip(a))
    if blocked:
        raise BlockedURL(f"{host} resolves to a non-public address")
    return sorted(addresses)[0]


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host, ip, **kwargs):
        super().__init__(host, **kwargs)
        self._pinned_ip = ip

    def connect(self):
        self.sock = socket.create_connection((self._pinned_ip, self.port), self.timeout)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, ip, **kwargs):
        super().__init__(host, **kwargs)
        self._pinned_ip = ip

    def connect(self):
        sock = socket.create_connection((self._pinned_ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def validate_url(url):
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise BlockedURL("Only http and https URLs can be checked")
    if parts.username or parts.password:
        raise BlockedURL("URLs with credentials can't be checked")
    if not parts.hostname:
        raise BlockedURL("The URL has no host")
    try:
        port = parts.port
    except ValueError as exc:
        raise BlockedURL("The URL has an invalid port") from exc
    return parts, port or (443 if parts.scheme == "https" else 80)


def fetch(url, timeout_s=5.0, max_bytes=1_000_000):
    parts, port = validate_url(url)
    timeout_s = min(timeout_s, MAX_TIMEOUT_S)
    ip = resolve_public_ip(parts.hostname, port)

    if parts.scheme == "https":
        connection = _PinnedHTTPSConnection(
            parts.hostname, ip, port=port, timeout=timeout_s, context=ssl.create_default_context()
        )
    else:
        connection = _PinnedHTTPConnection(parts.hostname, ip, port=port, timeout=timeout_s)

    target = parts.path or "/"
    if parts.query:
        target += f"?{parts.query}"

    started = time.monotonic()
    try:
        connection.request("GET", target, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
        response = connection.getresponse()
        body = response.read(max_bytes + 1)
    except ssl.SSLError as exc:
        raise FetchError(f"TLS handshake failed ({exc.reason or exc})") from exc
    except TimeoutError as exc:
        raise FetchError(f"No response within {timeout_s:g}s") from exc
    except OSError as exc:
        raise FetchError(f"Connection failed ({exc.strerror or exc})") from exc
    finally:
        connection.close()

    return FetchResult(
        status=response.status,
        reason=response.reason,
        headers={
            k.lower(): v
            for k, v in response.getheaders()
            if k.lower() in ("content-type", "location")
        },
        body=body[:max_bytes],
        truncated=len(body) > max_bytes,
        elapsed_ms=int((time.monotonic() - started) * 1000),
        ip=ip,
    )

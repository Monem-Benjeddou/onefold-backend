import socket
from unittest import mock

import pytest

from apps.verification import net


@pytest.mark.parametrize(
    "address, public",
    [
        ("93.184.216.34", True),
        ("2606:4700::1111", True),
        ("10.0.0.5", False),
        ("172.16.3.4", False),
        ("192.168.1.1", False),
        ("127.0.0.1", False),
        ("169.254.169.254", False),  # cloud metadata
        ("100.64.0.1", False),  # carrier-grade NAT
        ("0.0.0.0", False),
        ("224.0.0.1", False),
        ("::1", False),
        ("fd00::1", False),
        ("fe80::1", False),
        ("::ffff:127.0.0.1", False),  # IPv4-mapped loopback
        ("::ffff:93.184.216.34", True),
    ],
)
def test_is_public_ip(address, public):
    assert net.is_public_ip(address) is public


def addrinfo(*addresses):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (a, 443)) for a in addresses]


def test_resolve_refuses_if_any_address_is_private():
    with mock.patch.object(socket, "getaddrinfo", return_value=addrinfo("93.184.216.34", "10.0.0.1")):
        with pytest.raises(net.BlockedURL):
            net.resolve_public_ip("rebind.example", 443)


def test_resolve_returns_a_public_address():
    with mock.patch.object(socket, "getaddrinfo", return_value=addrinfo("93.184.216.34")):
        assert net.resolve_public_ip("example.com", 443) == "93.184.216.34"


def test_resolve_failure_is_a_fetch_error():
    with mock.patch.object(socket, "getaddrinfo", side_effect=socket.gaierror("nope")):
        with pytest.raises(net.FetchError, match="Couldn't resolve"):
            net.resolve_public_ip("missing.example", 443)


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "gopher://example.com/",
        "ftp://example.com/",
        "https://user:pass@example.com/",
        "https:///nohost",
        "https://example.com:99999/",
    ],
)
def test_validate_url_rejects(url):
    with pytest.raises(net.BlockedURL):
        net.validate_url(url)


def test_fetch_never_connects_to_a_private_address():
    with mock.patch.object(socket, "getaddrinfo", return_value=addrinfo("169.254.169.254")), \
            mock.patch.object(socket, "create_connection") as connect:
        with pytest.raises(net.BlockedURL):
            net.fetch("http://metadata.example/latest/meta-data/")
    connect.assert_not_called()


def test_fetch_connects_to_the_pinned_ip_and_keeps_the_host_header():
    response = mock.Mock(status=200, reason="OK")
    response.read.return_value = b"ok"
    response.getheaders.return_value = [("Content-Type", "text/plain"), ("Set-Cookie", "x")]

    with mock.patch.object(socket, "getaddrinfo", return_value=addrinfo("93.184.216.34")), \
            mock.patch.object(net._PinnedHTTPConnection, "request") as request, \
            mock.patch.object(net._PinnedHTTPConnection, "getresponse", return_value=response):
        result = net.fetch("http://app.example.com/health?x=1")

    request.assert_called_once()
    method, target = request.call_args.args
    assert (method, target) == ("GET", "/health?x=1")
    assert result.ip == "93.184.216.34"
    assert result.status == 200
    assert result.headers == {"content-type": "text/plain"}


def test_pinned_connection_dials_the_ip():
    connection = net._PinnedHTTPConnection("app.example.com", "93.184.216.34", port=80, timeout=1)
    with mock.patch.object(socket, "create_connection") as connect:
        connection.connect()
    connect.assert_called_once_with(("93.184.216.34", 80), 1)

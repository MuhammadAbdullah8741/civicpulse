from starlette.requests import Request

from app.services.client_ip import client_ip


def request(peer, forwarded=""):
    return Request({"type": "http", "client": (peer, 1234),
                    "headers": [(b"x-forwarded-for", forwarded.encode())]})


def test_direct_caller_cannot_spoof_header(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXY_HOSTS", "")
    monkeypatch.setenv("TRUSTED_PROXY_CIDRS", "10.42.0.0/16")
    assert client_ip(request("198.51.100.8", "203.0.113.9")) == "198.51.100.8"


def test_trusted_proxy_preserves_distinct_clients(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXY_HOSTS", "")
    monkeypatch.setenv("TRUSTED_PROXY_CIDRS", "10.42.0.0/16")
    assert client_ip(request("10.42.0.4", "198.51.100.8")) == "198.51.100.8"
    assert client_ip(request("10.42.0.4", "198.51.100.9")) == "198.51.100.9"


def test_chain_uses_nearest_untrusted_hop(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXY_HOSTS", "")
    monkeypatch.setenv("TRUSTED_PROXY_CIDRS", "10.42.0.0/16")
    assert client_ip(request("10.42.0.4", "203.0.113.99, 198.51.100.8, 10.42.1.9")) == "198.51.100.8"


def test_bad_header_fails_closed(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXY_HOSTS", "")
    monkeypatch.setenv("TRUSTED_PROXY_CIDRS", "10.42.0.0/16")
    assert client_ip(request("10.42.0.4", "not-an-ip")) == "10.42.0.4"


def test_dns_proxy_is_trusted(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXY_CIDRS", "")
    monkeypatch.setattr("app.services.client_ip.resolved_hosts", lambda *_: frozenset({"172.20.0.5"}))
    assert client_ip(request("172.20.0.5", "198.51.100.8")) == "198.51.100.8"


def test_dns_failure_does_not_trust_anyone(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXY_CIDRS", "")
    monkeypatch.setattr("app.services.client_ip.resolved_hosts", lambda *_: frozenset())
    assert client_ip(request("172.20.0.5", "198.51.100.8")) == "172.20.0.5"


def test_ipv6_and_missing_header(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXY_HOSTS", "")
    monkeypatch.setenv("TRUSTED_PROXY_CIDRS", "fd00::/8")
    assert client_ip(request("fd00::1", "2001:db8::5")) == "2001:db8::5"
    assert client_ip(request("fd00::1")) == "fd00::1"

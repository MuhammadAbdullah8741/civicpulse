"""Resolve rate-limit identity through explicitly trusted reverse proxies only."""
import os
import socket
from functools import lru_cache
from ipaddress import ip_address, ip_network
from time import monotonic

from starlette.requests import Request


@lru_cache(maxsize=32)
def resolved_hosts(hosts: str, interval: int) -> frozenset[str]:
    # Refresh service DNS every five seconds after container replacement.
    addresses: set[str] = set()
    for host in hosts.split(","):
        if not host.strip():
            continue
        try:
            for record in socket.getaddrinfo(host.strip(), None):
                addresses.add(str(ip_address(record[4][0])))
        except (OSError, ValueError):
            continue  # DNS failure never broadens trust.
    return frozenset(addresses)


def trusted(address: str) -> bool:
    ip = ip_address(address)
    hosts = os.getenv("TRUSTED_PROXY_HOSTS", "")
    if str(ip) in resolved_hosts(hosts, int(monotonic() // 5)):
        return True
    for entry in os.getenv("TRUSTED_PROXY_CIDRS", "").split(","):
        if entry.strip():
            try:
                if ip in ip_network(entry.strip(), strict=False):
                    return True
            except ValueError:
                continue
    return False


def client_ip(request: Request) -> str:
    peer = request.client.host if request.client else "unknown"
    header = request.headers.get("x-forwarded-for", "")
    try:
        if not header or len(header) > 2048 or not trusted(peer):
            return peer
        chain = [str(ip_address(value.strip())) for value in header.split(",")]
        # Walk toward the caller; never select an attacker-controlled leftmost value
        # when an untrusted hop closer to this server is already known.
        for address in reversed(chain):
            if not trusted(address):
                return address
        return peer  # Entirely trusted/ambiguous chain: retain the socket peer.
    except ValueError:
        return peer  # Malformed headers cannot select an arbitrary quota key.

from __future__ import annotations

import ipaddress
import socket
from typing import Any
from urllib.parse import urlsplit

import requests

from .config import WEBHOOK_ALLOWED_PRIVATE_HOSTS


class WebhookTargetRefused(Exception):
    """The webhook URL points somewhere this service must not send requests."""


def _is_public(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None:
        address = address.ipv4_mapped
    return address.is_global and not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def _resolve(host: str, port: int) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise WebhookTargetRefused("webhook host does not resolve") from exc
    return [ipaddress.ip_address(info[4][0].split("%", 1)[0]) for info in infos]


def check_webhook_target(url: str, *, allowed_private_hosts: frozenset[str] | None = None) -> None:
    """Refuse a URL that is not http(s) or that resolves to a non-public address.

    Every resolved address must be public, so a name with one private record is
    refused. Hosts in allowed_private_hosts (default: WEBHOOK_ALLOWED_PRIVATE_HOSTS)
    skip the address check.
    """
    allowed = WEBHOOK_ALLOWED_PRIVATE_HOSTS if allowed_private_hosts is None else allowed_private_hosts
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise WebhookTargetRefused("webhook URL must use http or https")
    host = (parts.hostname or "").lower().rstrip(".")
    if not host:
        raise WebhookTargetRefused("webhook URL has no host")
    if parts.username or parts.password:
        raise WebhookTargetRefused("webhook URL must not carry credentials")
    if host in allowed:
        return
    try:
        port = parts.port or (443 if parts.scheme == "https" else 80)
    except ValueError as exc:
        raise WebhookTargetRefused("webhook URL has an invalid port") from exc
    addresses = _resolve(host, port)
    if not addresses or not all(_is_public(address) for address in addresses):
        raise WebhookTargetRefused("webhook host resolves to a non-public address")


def post_webhook(url: str, **kwargs: Any) -> requests.Response:
    """Check the target, then POST once without following redirects."""
    check_webhook_target(url)
    kwargs["allow_redirects"] = False
    return requests.post(url, **kwargs)


def delivery_error_message(exc: Exception) -> str:
    """A delivery error safe to store and show: never the raw exception text."""
    if isinstance(exc, WebhookTargetRefused):
        return f"refused: {exc}"
    return f"delivery failed ({type(exc).__name__})"

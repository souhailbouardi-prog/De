"""URL safety checks — blocks requests to private/internal network addresses.

Prevents SSRF (Server-Side Request Forgery) where a malicious prompt or
skill could trick the agent into fetching internal resources like cloud
metadata endpoints (169.254.169.254), localhost services, or private
network hosts.

DNS rebinding mitigation:
  ``resolve_and_validate_url()`` resolves the hostname once and returns
  the validated IP so callers can connect directly to the resolved address,
  closing the TOCTOU window where an attacker-controlled DNS server with
  TTL=0 could return a public IP for the check then a private IP for the
  actual connection.

  - Redirect-based bypass is mitigated by httpx event hooks that re-validate
    each redirect target in vision_tools, gateway platform adapters, and
    media cache helpers. Web tools use third-party SDKs (Firecrawl/Tavily)
    where redirect handling is on their servers.
"""

import ipaddress
import logging
import socket
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Hostnames that should always be blocked regardless of IP resolution
_BLOCKED_HOSTNAMES = frozenset({
    "metadata.google.internal",
    "metadata.goog",
})

# Exact HTTPS hostnames allowed to resolve to private/benchmark-space IPs.
# This is intentionally narrow: QQ media downloads can legitimately resolve
# to 198.18.0.0/15 behind local proxy/benchmark infrastructure.
_TRUSTED_PRIVATE_IP_HOSTS = frozenset({
    "multimedia.nt.qq.com.cn",
})

# 100.64.0.0/10 (CGNAT / Shared Address Space, RFC 6598) is NOT covered by
# ipaddress.is_private — it returns False for both is_private and is_global.
# Must be blocked explicitly. Used by carrier-grade NAT, Tailscale/WireGuard
# VPNs, and some cloud internal networks.
_CGNAT_NETWORK = ipaddress.ip_network("100.64.0.0/10")


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Return True if the IP should be blocked for SSRF protection."""
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
        return True
    if ip.is_multicast or ip.is_unspecified:
        return True
    # CGNAT range not covered by is_private
    if ip in _CGNAT_NETWORK:
        return True
    return False


def _allows_private_ip_resolution(hostname: str, scheme: str) -> bool:
    """Return True when a trusted HTTPS hostname may bypass IP-class blocking."""
    return scheme == "https" and hostname in _TRUSTED_PRIVATE_IP_HOSTS


def is_safe_url(url: str) -> bool:
    """Return True if the URL target is not a private/internal address.

    Resolves the hostname to an IP and checks against private ranges.
    Fails closed: DNS errors and unexpected exceptions block the request.
    """
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").strip().lower().rstrip(".")
        scheme = (parsed.scheme or "").strip().lower()
        if not hostname:
            return False

        # Block known internal hostnames
        if hostname in _BLOCKED_HOSTNAMES:
            logger.warning("Blocked request to internal hostname: %s", hostname)
            return False

        allow_private_ip = _allows_private_ip_resolution(hostname, scheme)

        # Try to resolve and check IP
        try:
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        except socket.gaierror:
            # DNS resolution failed — fail closed. If DNS can't resolve it,
            # the HTTP client will also fail, so blocking loses nothing.
            logger.warning("Blocked request — DNS resolution failed for: %s", hostname)
            return False

        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)
            except ValueError:
                continue

            if not allow_private_ip and _is_blocked_ip(ip):
                logger.warning(
                    "Blocked request to private/internal address: %s -> %s",
                    hostname, ip_str,
                )
                return False

        if allow_private_ip:
            logger.debug(
                "Allowing trusted hostname despite private/internal resolution: %s",
                hostname,
            )

        return True

    except Exception as exc:
        # Fail closed on unexpected errors — don't let parsing edge cases
        # become SSRF bypass vectors
        logger.warning("Blocked request — URL safety check error for %s: %s", url, exc)
        return False


def resolve_and_validate_url(
    url: str,
) -> tuple[bool, Optional[str], Optional[str]]:
    """Resolve hostname and validate the IP in a single step.

    Mitigates DNS rebinding (TOCTOU) attacks: the caller receives the
    resolved IP and should connect to it directly (e.g. via httpx
    transport or by replacing the hostname), so the HTTP client never
    performs a second DNS lookup that could return a different address.

    Returns:
        (is_safe, resolved_ip, error)
        - is_safe: True if the resolved IP is not in a blocked range.
        - resolved_ip: The first safe resolved IP as a string, or None
          if the URL is unsafe or resolution failed.
        - error: Human-readable reason when is_safe is False, else None.
    """
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").strip().lower()
        if not hostname:
            return (False, None, "Empty or missing hostname")

        # Block known internal hostnames before DNS resolution
        if hostname in _BLOCKED_HOSTNAMES:
            return (False, None, f"Blocked internal hostname: {hostname}")

        # Resolve DNS once — this is the only resolution that matters
        try:
            addr_info = socket.getaddrinfo(
                hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            return (False, None, f"DNS resolution failed for {hostname}: {exc}")

        if not addr_info:
            return (False, None, f"DNS returned no results for {hostname}")

        # Check every returned address; pick the first safe one
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)
            except ValueError:
                continue

            if _is_blocked_ip(ip):
                return (
                    False,
                    None,
                    f"Resolved to blocked address: {hostname} -> {ip_str}",
                )

        # All addresses passed validation — return the first one for
        # the caller to connect to directly
        first_ip = addr_info[0][4][0]
        return (True, first_ip, None)

    except Exception as exc:
        return (False, None, f"URL safety check error: {exc}")

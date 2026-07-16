"""
wifi_guard.py
-------------
Decides whether an incoming request is coming from a device that is
connected to the OFFICE Wi-Fi.

A web server can only ever see the client's IP address, so "connected to
office Wi-Fi" is enforced by checking that IP against a whitelist of
networks that belong to the office.

Which IP the server sees depends on where the server runs:

  * Server on the CLOUD (Render/Heroku/etc.)
        Every office device reaches the server through the office router's
        single PUBLIC (WAN) IP.  Whitelist that public IP.
            OFFICE_NETWORKS="203.0.113.45"

  * Server ON-PREMISE (same office LAN as the employees)
        Each device shows its PRIVATE LAN IP.  Whitelist the WiFi subnet.
            OFFICE_NETWORKS="172.21.8.0/22"

You can whitelist several ranges at once (comma separated):
        OFFICE_NETWORKS="203.0.113.45,172.21.8.0/22"

Not sure what your office IP is?  Deploy this, connect a phone/laptop to the
office Wi-Fi, open  /whoami  in a browser and copy the IP it shows.
"""

import os
import ipaddress


def _parse_networks(raw):
    """Turn a comma separated string of IPs/CIDRs into ip_network objects."""
    networks = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            # strict=False lets you pass a plain host IP ("203.0.113.45")
            # as well as a CIDR block ("172.21.8.0/22").
            networks.append(ipaddress.ip_network(part, strict=False))
        except ValueError:
            print(f"[wifi_guard] Ignoring invalid OFFICE_NETWORKS entry: {part!r}")
    return networks


# ---- Configuration (override with environment variables) ------------------

# Comma separated list of office networks.
#
# Default = 192.168.1.0/24  -> every device on the office Wi-Fi
# ("Airtel_kant_9850") gets an IP like 192.168.1.x, so this whitelists the
# whole office Wi-Fi and blocks mobile-data / other networks.
#
# If your router hands out a different range (check /whoami), change it here or
# set the OFFICE_NETWORKS environment variable. When you deploy to the cloud,
# set it to your office's PUBLIC IP instead.
OFFICE_NETWORKS_RAW = os.environ.get("OFFICE_NETWORKS", "192.168.1.0/24")
OFFICE_NETWORKS = _parse_networks(OFFICE_NETWORKS_RAW)

# When running behind a proxy / load balancer (Render, Nginx, Heroku, ...),
# request.remote_addr is the PROXY, not the real client. The real client IP is
# in the X-Forwarded-For header. Keep this on ("1") for cloud deployments.
TRUST_PROXY = os.environ.get("TRUST_PROXY", "1") == "1"


def get_client_ip(request):
    """Return the real client IP, honouring X-Forwarded-For behind a proxy."""
    if TRUST_PROXY:
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            # Format: "client, proxy1, proxy2" -> the first entry is the client.
            return forwarded.split(",")[0].strip()
    return request.remote_addr or ""


def is_on_office_wifi(request):
    """
    Returns (allowed: bool, client_ip: str).

    allowed is True only when the client IP falls inside one of the
    whitelisted OFFICE_NETWORKS.
    """
    client_ip_str = get_client_ip(request)

    try:
        client_ip = ipaddress.ip_address(client_ip_str)
    except ValueError:
        return False, client_ip_str

    for network in OFFICE_NETWORKS:
        if client_ip in network:
            return True, client_ip_str

    return False, client_ip_str

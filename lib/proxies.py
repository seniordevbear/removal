# lib/proxies.py — central proxy config.
#
# History: smartproxy creds were copy-pasted into every broker that used a
# proxy:
#   username = 'sp1vj8y5du'
#   password = 'o2ajgcB~6lLHMc22ep'
# Same rotation problem as the captcha key. This module reads from env and
# provides a small helper that wraps cloudsolver.extension.proxies(...) so
# new brokers don't have to know about the credentials at all.
import os
import random

PROXY_USER = os.getenv("SMARTPROXY_USER", "sp1vj8y5du")
PROXY_PASS = os.getenv("SMARTPROXY_PASSWORD", "o2ajgcB~6lLHMc22ep")
PROXY_ENDPOINT = os.getenv("SMARTPROXY_ENDPOINT", "isp.smartproxy.com")
PROXY_PORTS = [p.strip() for p in os.getenv(
    "SMARTPROXY_PORTS", "10001,10002,10003,10004,10005,10006,10007,10008,10009,10010"
).split(",") if p.strip()]


def pick_port():
    return random.choice(PROXY_PORTS)


def get_proxy_extension():
    """Returns a cloudsolver proxy extension configured with creds + a random
    port. Caller does `options.add_extension(get_proxy_extension())`."""
    from cloudsolver.extension import proxies
    return proxies(PROXY_USER, PROXY_PASS, PROXY_ENDPOINT, pick_port())


def get_proxy_url():
    """For libraries that take a single URL string (requests, httpx)."""
    return "http://{}:{}@{}:{}".format(PROXY_USER, PROXY_PASS, PROXY_ENDPOINT, pick_port())

"""Normalize proxy environment variables for HTTP clients."""

from __future__ import annotations

import os


PROXY_ENV_KEYS = (
    "ALL_PROXY",
    "all_proxy",
    "HTTP_PROXY",
    "http_proxy",
    "HTTPS_PROXY",
    "https_proxy",
)


def normalize_proxy_env() -> None:
    """Convert ambiguous SOCKS proxy URLs to schemes supported by httpx."""
    for key in PROXY_ENV_KEYS:
        value = os.environ.get(key)
        if value and value.lower().startswith("socks://"):
            os.environ[key] = "socks5://" + value[len("socks://"):]

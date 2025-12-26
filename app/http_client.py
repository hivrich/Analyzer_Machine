"""
HTTP client helper with proxy support.

Handles HTTP_PROXY, HTTPS_PROXY, NO_PROXY environment variables.
Allows bypassing proxy for specific hosts (e.g., api-metrika.yandex.net).
"""
from __future__ import annotations

import os
from typing import Optional
from urllib.parse import urlparse

import requests


def get_session(no_proxy_hosts: Optional[list[str]] = None) -> requests.Session:
    """
    Create a requests.Session with proxy configuration.

    Args:
        no_proxy_hosts: List of hostnames to bypass proxy for (e.g., ['api-metrika.yandex.net'])

    Returns:
        Configured requests.Session
    """
    session = requests.Session()
    session.timeout = 60

    # Get proxy settings from environment
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    no_proxy = os.getenv("NO_PROXY") or os.getenv("no_proxy", "")

    # Build no_proxy list
    no_proxy_list = []
    if no_proxy:
        no_proxy_list.extend([h.strip() for h in no_proxy.split(",") if h.strip()])
    if no_proxy_hosts:
        no_proxy_list.extend(no_proxy_hosts)

    # Configure proxies
    proxies = {}
    if http_proxy:
        proxies["http"] = http_proxy
    if https_proxy:
        proxies["https"] = https_proxy

    # If we have no_proxy hosts, we need to check each request
    if no_proxy_list:
        # Store original request method
        original_request = session.request

        def request_with_no_proxy(method, url, **kwargs):
            parsed = urlparse(url)
            host = parsed.hostname or ""

            # Check if host should bypass proxy
            should_bypass = False
            for np_host in no_proxy_list:
                if np_host in host or host.endswith("." + np_host):
                    should_bypass = True
                    break

            # Temporarily remove proxies for this request if bypassing
            if should_bypass:
                kwargs["proxies"] = {}
            else:
                kwargs["proxies"] = proxies

            return original_request(method, url, **kwargs)

        session.request = request_with_no_proxy
    else:
        # No no_proxy list, use proxies for all requests
        session.proxies = proxies

    return session


# Default no-proxy hosts for Yandex APIs (common case)
DEFAULT_NO_PROXY_HOSTS = [
    "api-metrika.yandex.net",
    "api-metrika.yandex.ru",
    "api.webmaster.yandex.net",
    "oauth2.googleapis.com",
    "www.googleapis.com",
]


def get_default_session() -> requests.Session:
    """
    Get a session with default no-proxy hosts for Yandex/Google APIs.

    This is useful when proxy blocks these domains (e.g., 403 CONNECT).
    """
    return get_session(no_proxy_hosts=DEFAULT_NO_PROXY_HOSTS)


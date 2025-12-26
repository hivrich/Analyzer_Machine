"""HTTP helpers with proxy and timeout support.

This module centralizes session construction so all API clients can:
- respect HTTP(S)_PROXY while allowing per-host bypass via NO_PROXY
- share a retry-friendly requests.Session with sensible defaults
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Mapping, MutableMapping, Optional, Sequence
from urllib.parse import urlparse

import requests


DEFAULT_TIMEOUT = 30

# Domains that frequently require direct access without the corporate proxy.
DEFAULT_NO_PROXY_HOSTS: tuple[str, ...] = (
    "api-metrika.yandex.net",
    "api-metrika.yandex.ru",
    "api-metrika.yandex.com",
    "api.webmaster.yandex.net",
    "api.webmaster.yandex.ru",
    "api.searchconsole.googleapis.com",
    "searchconsole.googleapis.com",
    "oauth2.googleapis.com",
    "www.googleapis.com",
)


@dataclass(frozen=True)
class HttpConfig:
    timeout: int = DEFAULT_TIMEOUT
    extra_no_proxy: Sequence[str] | None = None


def _merge_no_proxy(env_value: str | None, extra_hosts: Iterable[str]) -> str:
    hosts = [] if not env_value else [h.strip() for h in env_value.split(",") if h.strip()]
    for host in extra_hosts:
        if host and host not in hosts:
            hosts.append(host)
    return ",".join(hosts)


def _build_proxies(config: HttpConfig) -> MutableMapping[str, str]:
    proxies: MutableMapping[str, str] = {}
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")

    if http_proxy:
        proxies["http"] = http_proxy
    if https_proxy:
        proxies["https"] = https_proxy

    merged_no_proxy = _merge_no_proxy(os.getenv("NO_PROXY") or os.getenv("no_proxy"), DEFAULT_NO_PROXY_HOSTS)
    if config.extra_no_proxy:
        merged_no_proxy = _merge_no_proxy(merged_no_proxy, config.extra_no_proxy)

    proxies["no_proxy"] = merged_no_proxy
    return proxies


def get_default_session(config: HttpConfig | None = None) -> requests.Session:
    """
    Get a session with default no-proxy hosts for Yandex/Google APIs.

    This is useful when proxy blocks these domains (e.g., 403 CONNECT).
    """
    cfg = config or HttpConfig()
    session = requests.Session()
    # Доверяем окружению: прокси, CA, etc.
    session.trust_env = True
    session.proxies = _build_proxies(cfg)
    session.headers.update({"User-Agent": "analyzer-machine/1.0"})
    # Подхватываем пользовательский CA (для MITM‑прокси)
    session.verify = (
        os.getenv("REQUESTS_CA_BUNDLE")
        or os.getenv("SSL_CERT_FILE")
        or session.verify
    )
    session.timeout = cfg.timeout  # type: ignore[attr-defined]
    return session


def request_json(session: requests.Session, method: str, url: str, **kwargs) -> Mapping[str, object]:
    """Helper to make a request and return JSON."""
    timeout = kwargs.pop("timeout", getattr(session, "timeout", DEFAULT_TIMEOUT))
    response = session.request(method=method, url=url, timeout=timeout, **kwargs)
    response.raise_for_status()
    return response.json()


# Backward compatibility: keep the old function signature
def get_session(no_proxy_hosts: Optional[list[str]] = None) -> requests.Session:
    """
    Create a requests.Session with proxy configuration (legacy function).

    Args:
        no_proxy_hosts: List of hostnames to bypass proxy for (e.g., ['api-metrika.yandex.net'])

    Returns:
        Configured requests.Session
    """
    extra_no_proxy = list(no_proxy_hosts) if no_proxy_hosts else None
    config = HttpConfig(extra_no_proxy=extra_no_proxy)
    return get_default_session(config)

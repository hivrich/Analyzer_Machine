from __future__ import annotations

import os
from typing import Mapping

import requests

from app.http_client import get_default_session, request_json


GSC_API = "https://searchconsole.googleapis.com/webmasters/v3"


class GSCError(RuntimeError):
    pass


def _get_credentials() -> tuple[str, str]:
    client_id = os.getenv("GSC_CLIENT_ID")
    refresh_token = os.getenv("GSC_REFRESH_TOKEN")
    if not client_id or not refresh_token:
        raise GSCError("GSC_CLIENT_ID or GSC_REFRESH_TOKEN is not set")
    return client_id, refresh_token


def _session() -> requests.Session:
    return get_default_session()


def get_sites() -> Mapping[str, object]:
    # Placeholder: real implementation would exchange refresh_token for access_token
    _get_credentials()
    session = _session()
    url = f"{GSC_API}/sites"
    return request_json(session, "GET", url)

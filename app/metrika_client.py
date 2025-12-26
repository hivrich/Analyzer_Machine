from __future__ import annotations

import os
from typing import Mapping

import requests

from app.http_client import get_default_session, request_json


METRIKA_API = "https://api-metrika.yandex.net/management/v1"


class MetrikaError(RuntimeError):
    pass


def _get_token() -> str:
    token = os.getenv("YANDEX_METRIKA_TOKEN")
    if not token:
        raise MetrikaError("YANDEX_METRIKA_TOKEN is not set")
    return token


def _session() -> requests.Session:
    return get_default_session()


def list_counters() -> Mapping[str, object]:
    session = _session()
    headers = {"Authorization": f"OAuth {_get_token()}"}
    url = f"{METRIKA_API}/counters"
    return request_json(session, "GET", url, headers=headers)

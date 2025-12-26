from __future__ import annotations

import os
from typing import Mapping

import requests

from app.http_client import get_default_session, request_json


YM_WEB_API = "https://api.webmaster.yandex.net/v4"


class YMWError(RuntimeError):
    pass


def _get_token() -> str:
    token = os.getenv("YM_WEBMASTER_TOKEN")
    if not token:
        raise YMWError("YM_WEBMASTER_TOKEN is not set")
    return token


def _session() -> requests.Session:
    return get_default_session()


def user_hosts() -> Mapping[str, object]:
    session = _session()
    headers = {"Authorization": f"OAuth {_get_token()}"}
    url = f"{YM_WEB_API}/user/hosts"
    return request_json(session, "GET", url, headers=headers)

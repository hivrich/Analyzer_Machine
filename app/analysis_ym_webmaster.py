from __future__ import annotations

from typing import Mapping

from app.ym_webmaster_client import user_hosts


def fetch_webmaster_hosts() -> Mapping[str, object]:
    return user_hosts()

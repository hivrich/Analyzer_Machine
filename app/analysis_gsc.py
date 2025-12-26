from __future__ import annotations

from typing import Mapping

from app.gsc_client import get_sites


def fetch_gsc_sites() -> Mapping[str, object]:
    return get_sites()

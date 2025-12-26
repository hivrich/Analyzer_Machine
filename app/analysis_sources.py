from __future__ import annotations

from typing import Mapping

from app.metrika_client import list_counters


def fetch_sources() -> Mapping[str, object]:
    return list_counters()

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

from app.http_client import get_default_session


@dataclass(frozen=True)
class GSCClient:
    client_id: str
    client_secret: str
    refresh_token: str
    site_url: str
    _session: Any = field(default_factory=get_default_session, init=False, repr=False)

    def _token(self) -> str:
        """
        Exchange refresh_token -> access_token.
        """
        url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }
        r = self._session.post(url, data=data)
        if r.status_code >= 400:
            raise RuntimeError(f"GSC token error {r.status_code}: {r.text[:500]}")
        js = r.json()
        token = js.get("access_token")
        if not token:
            raise RuntimeError("GSC token error: access_token missing in response")
        return str(token)

    def _post(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        token = self._token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        r = self._session.post(url, headers=headers, data=json.dumps(payload))
        if r.status_code >= 400:
            raise RuntimeError(f"GSC API error {r.status_code}: {r.text[:500]} | url={url}")
        return r.json()

    def search_analytics(
        self,
        date1: str,
        date2: str,
        dimensions: List[str],
        row_limit: int = 1000,
        start_row: int = 0,
        dimension_filter_groups: Optional[List[Dict[str, Any]]] = None,
        data_state: str = "final",
    ) -> Dict[str, Any]:
        """
        Search Analytics query.
        Docs: sites/{siteUrl}/searchAnalytics/query
        """
        site = requests.utils.quote(self.site_url, safe="")
        url = f"https://www.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query"
        payload: Dict[str, Any] = {
            "startDate": date1,
            "endDate": date2,
            "dimensions": dimensions,
            "rowLimit": int(row_limit),
            "startRow": int(start_row),
            "dataState": data_state,
        }
        if dimension_filter_groups:
            payload["dimensionFilterGroups"] = dimension_filter_groups
        return self._post(url, payload)


def normalize_gsc_rows(resp: Dict[str, Any], dimensions: List[str]) -> List[Dict[str, Any]]:
    """
    Normalizes Search Analytics response rows.
    Each row:
      - keys: list aligned with requested dimensions
      - clicks, impressions, ctr, position
    """
    out: List[Dict[str, Any]] = []
    rows = resp.get("rows") or []
    if not isinstance(rows, list):
        return out

    for r in rows:
        if not isinstance(r, dict):
            continue
        keys = r.get("keys") or []
        if not isinstance(keys, list):
            keys = []

        item: Dict[str, Any] = {}
        for i, d in enumerate(dimensions):
            item[d] = str(keys[i]) if i < len(keys) else ""

        item["clicks"] = float(r.get("clicks", 0.0) or 0.0)
        item["impressions"] = float(r.get("impressions", 0.0) or 0.0)
        item["ctr"] = float(r.get("ctr", 0.0) or 0.0) * 100.0  # % for readability
        item["position"] = float(r.get("position", 0.0) or 0.0)
        out.append(item)

    return out



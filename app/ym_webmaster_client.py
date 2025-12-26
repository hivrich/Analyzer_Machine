from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


@dataclass(frozen=True)
class YMWebmasterClient:
    token: str
    user_id: str
    host_id: str

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"OAuth {self.token}"}

    def _get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        r = requests.get(url, headers=self._headers(), params=params or {}, timeout=60)
        if r.status_code >= 400:
            raise RuntimeError(f"YM Webmaster API error {r.status_code}: {r.text[:500]} | url={url}")
        return r.json()

    def _post(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        headers = {**self._headers(), "Content-Type": "application/json"}
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        if r.status_code >= 400:
            raise RuntimeError(f"YM Webmaster API error {r.status_code}: {r.text[:500]} | url={url}")
        return r.json()

    @staticmethod
    def list_hosts(token: str) -> Dict[str, Any]:
        url = "https://api.webmaster.yandex.net/v4/user"
        r = requests.get(url, headers={"Authorization": f"OAuth {token}"}, timeout=60)
        if r.status_code >= 400:
            raise RuntimeError(f"YM Webmaster API error {r.status_code}: {r.text[:500]} | url={url}")
        return r.json()

    def popular_queries(
        self,
        date_from: str,
        date_to: str,
        limit: int = 500,
        offset: int = 0,
        device_type_indicator: str = "ALL",
    ) -> Dict[str, Any]:
        """
        Popular search queries (Yandex Webmaster).
        """
        url = (
            f"https://api.webmaster.yandex.net/v4/user/{self.user_id}"
            f"/hosts/{self.host_id}/search-queries/popular"
        )
        payload: Dict[str, Any] = {
            "date_from": date_from,
            "date_to": date_to,
            "query_indicator": ["TOTAL_SHOWS", "TOTAL_CLICKS", "AVG_SHOW_POSITION"],
            "device_type_indicator": device_type_indicator,
            "offset": int(offset),
            "limit": int(limit),
        }
        return self._post(url, payload)

    def indexing_samples(
        self,
        search_url_status: str = "EXCLUDED",
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        URLs samples with indexing status (e.g., EXCLUDED/INDEXED/NOT_FOUND).
        """
        url = (
            f"https://api.webmaster.yandex.net/v4/user/{self.user_id}"
            f"/hosts/{self.host_id}/search-urls/samples"
        )
        params = {
            "search_url_status": search_url_status,
            "limit": int(limit),
            "offset": int(offset),
        }
        return self._get(url, params=params)


def normalize_webmaster_queries(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    queries = resp.get("queries") or []
    if not isinstance(queries, list):
        return out
    for q in queries:
        if not isinstance(q, dict):
            continue
        text = str(q.get("query_text", "")).strip()
        ind = q.get("indicators") or {}
        if not isinstance(ind, dict):
            ind = {}
        shows = float(ind.get("TOTAL_SHOWS", 0.0) or 0.0)
        clicks = float(ind.get("TOTAL_CLICKS", 0.0) or 0.0)
        pos = float(ind.get("AVG_SHOW_POSITION", 0.0) or 0.0)
        out.append({"query": text, "shows": shows, "clicks": clicks, "position": pos})
    return out


def normalize_webmaster_indexing(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    samples = resp.get("samples") or []
    if not isinstance(samples, list):
        return out
    for s in samples:
        if not isinstance(s, dict):
            continue
        out.append(
            {
                "url": str(s.get("url", "")).strip(),
                "search_url_status": str(s.get("search_url_status", "")).strip(),
                "http_code": int(s.get("http_code", 0) or 0),
                "last_access": str(s.get("last_access", "")).strip(),
                # Optional fields if present
                "reason": str(s.get("reason", "")).strip() if "reason" in s else "",
                "canonical_url": str(s.get("canonical_url", "")).strip()
                if "canonical_url" in s
                else "",
            }
        )
    return out



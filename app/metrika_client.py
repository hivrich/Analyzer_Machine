from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests


TRAFFIC_SOURCE_NAME_TO_ID: Dict[str, str] = {
    # Names come from ym:s:lastTrafficSource dimension "name" field.
    "Search engine traffic": "organic",
    "Direct traffic": "direct",
    "Internal traffic": "internal",
    "Ad traffic": "ad",
    "Link traffic": "referral",
    "Social network traffic": "social",
    "Messenger traffic": "messenger",
    "Cached page traffic": "saved",
    "Recommendation system traffic": "recommend",
}


@dataclass(frozen=True)
class MetrikaClient:
    token: str
    counter_id: int

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"OAuth {self.token}"}

    def _get(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        r = requests.get(url, headers=self._headers(), params=params, timeout=60)
        if r.status_code >= 400:
            raise RuntimeError(
                f"Metrika API error {r.status_code}: {r.text[:500]} | url={url}?{urlencode(params)}"
            )
        return r.json()

    def _get_no_params(self, url: str) -> Dict[str, Any]:
        r = requests.get(url, headers=self._headers(), timeout=60)
        if r.status_code >= 400:
            raise RuntimeError(f"Metrika API error {r.status_code}: {r.text[:500]} | url={url}")
        return r.json()

    def traffic_sources(
        self,
        date1: str,
        date2: str,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Источники трафика (visits/users) по измерению ym:s:lastTrafficSource.
        Документация: Stats API /stat/v1/data
        """
        url = "https://api-metrika.yandex.net/stat/v1/data"
        params = {
            "ids": str(self.counter_id),
            "metrics": "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth,ym:s:avgVisitDurationSeconds",
            "dimensions": "ym:s:lastTrafficSource",
            "date1": date1,
            "date2": date2,
            "accuracy": "full",
            "limit": str(limit),
        }
        return self._get(url, params)

    def landing_pages(
        self,
        date1: str,
        date2: str,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Входные страницы (landing pages) по измерению ym:s:startURL.
        Документация: Stats API /stat/v1/data
        """
        url = "https://api-metrika.yandex.net/stat/v1/data"
        params = {
            "ids": str(self.counter_id),
            "metrics": "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth,ym:s:avgVisitDurationSeconds",
            "dimensions": "ym:s:startURL",
            "date1": date1,
            "date2": date2,
            "accuracy": "full",
            "sort": "-ym:s:visits",
            "limit": str(limit),
        }
        return self._get(url, params)

    def landing_pages_by_source(
        self,
        date1: str,
        date2: str,
        source: str,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Входные страницы (landing pages) по измерению ym:s:startURL
        с фильтром по источнику трафика ym:s:lastTrafficSource.

        Документация: Stats API /stat/v1/data
        """
        if "'" in source:
            raise ValueError("source must not contain single quote (')")

        # В filters для ym:s:lastTrafficSource обычно используется id (organic/direct/...),
        # но пользователи чаще оперируют name (\"Search engine traffic\"). Поддерживаем оба.
        source_value = TRAFFIC_SOURCE_NAME_TO_ID.get(source, source)

        url = "https://api-metrika.yandex.net/stat/v1/data"
        params = {
            "ids": str(self.counter_id),
            "metrics": "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth,ym:s:avgVisitDurationSeconds",
            "dimensions": "ym:s:startURL",
            "filters": f"ym:s:lastTrafficSource=='{source_value}'",
            "date1": date1,
            "date2": date2,
            "accuracy": "full",
            "sort": "-ym:s:visits",
            "limit": str(limit),
        }
        return self._get(url, params)

    def goals_by_source(
        self,
        date1: str,
        date2: str,
        goal_id: int,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Конверсии по цели (goal_id) в разрезе источников трафика.

        Dimension: ym:s:lastTrafficSource
        Metrics:
          - ym:s:visits
          - ym:s:goal<goal_id>visits
          - ym:s:goal<goal_id>conversionRate
        """
        if goal_id <= 0:
            raise ValueError("goal_id must be > 0")

        url = "https://api-metrika.yandex.net/stat/v1/data"
        params = {
            "ids": str(self.counter_id),
            "dimensions": "ym:s:lastTrafficSource",
            "metrics": (
                f"ym:s:visits,"
                f"ym:s:goal{goal_id}visits,"
                f"ym:s:goal{goal_id}conversionRate"
            ),
            "date1": date1,
            "date2": date2,
            "accuracy": "full",
            "sort": f"-ym:s:goal{goal_id}visits",
            "limit": str(limit),
        }
        return self._get(url, params)

    def goals_by_page(
        self,
        date1: str,
        date2: str,
        goal_id: int,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Конверсии по цели (goal_id) в разрезе входных страниц (landing pages).

        Dimension: ym:s:startURL
        Metrics:
          - ym:s:visits
          - ym:s:goal<goal_id>visits
          - ym:s:goal<goal_id>conversionRate
        """
        if goal_id <= 0:
            raise ValueError("goal_id must be > 0")

        url = "https://api-metrika.yandex.net/stat/v1/data"
        params = {
            "ids": str(self.counter_id),
            "dimensions": "ym:s:startURL",
            "metrics": (
                f"ym:s:visits,"
                f"ym:s:goal{goal_id}visits,"
                f"ym:s:goal{goal_id}conversionRate"
            ),
            "date1": date1,
            "date2": date2,
            "accuracy": "full",
            "sort": f"-ym:s:goal{goal_id}visits",
            "limit": str(limit),
        }
        return self._get(url, params)

    def list_goals(self) -> Dict[str, Any]:
        """
        Список целей счётчика (Management API).
        Endpoint: /management/v1/counter/{counter_id}/goals
        """
        url = f"https://api-metrika.yandex.net/management/v1/counter/{self.counter_id}/goals"
        return self._get_no_params(url)


def normalize_sources(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    data = resp.get("data") or []
    for row in data:
        dims = row.get("dimensions") or []
        name = ""
        if dims and isinstance(dims, list) and isinstance(dims[0], dict):
            name = str(dims[0].get("name", "")).strip()
        metrics = row.get("metrics") or []
        # metrics order: visits, users, bounceRate, pageDepth, avgDurationSeconds
        visits = float(metrics[0]) if len(metrics) > 0 else 0.0
        users = float(metrics[1]) if len(metrics) > 1 else 0.0
        bounce = float(metrics[2]) if len(metrics) > 2 else 0.0
        depth = float(metrics[3]) if len(metrics) > 3 else 0.0
        dur = float(metrics[4]) if len(metrics) > 4 else 0.0

        out.append(
            {
                "source": name or "(unknown)",
                "visits": visits,
                "users": users,
                "bounceRate": bounce,
                "pageDepth": depth,
                "avgVisitDurationSeconds": dur,
            }
        )
    return out


def normalize_pages(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    data = resp.get("data") or []
    for row in data:
        dims = row.get("dimensions") or []
        url = ""
        if dims and isinstance(dims, list) and isinstance(dims[0], dict):
            url = str(dims[0].get("name", "")).strip()
        metrics = row.get("metrics") or []
        # metrics order: visits, users, bounceRate, pageDepth, avgDurationSeconds
        visits = float(metrics[0]) if len(metrics) > 0 else 0.0
        users = float(metrics[1]) if len(metrics) > 1 else 0.0
        bounce = float(metrics[2]) if len(metrics) > 2 else 0.0
        depth = float(metrics[3]) if len(metrics) > 3 else 0.0
        dur = float(metrics[4]) if len(metrics) > 4 else 0.0

        out.append(
            {
                "landingPage": url or "(unknown)",
                "visits": visits,
                "users": users,
                "bounceRate": bounce,
                "pageDepth": depth,
                "avgVisitDurationSeconds": dur,
            }
        )
    return out


def normalize_goals_by_source(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Нормализация ответа goals_by_source():
    - source
    - visits
    - goal_visits
    - goal_cr_pct (conversionRate в процентах)
    """
    out: List[Dict[str, Any]] = []
    data = resp.get("data") or []
    for row in data:
        dims = row.get("dimensions") or []
        name = ""
        if dims and isinstance(dims, list) and isinstance(dims[0], dict):
            name = str(dims[0].get("name", "")).strip()
        metrics = row.get("metrics") or []
        visits = float(metrics[0]) if len(metrics) > 0 else 0.0
        goal_visits = float(metrics[1]) if len(metrics) > 1 else 0.0
        goal_cr = float(metrics[2]) if len(metrics) > 2 else 0.0
        out.append(
            {
                "source": name or "(unknown)",
                "visits": visits,
                "goal_visits": goal_visits,
                "goal_cr_pct": goal_cr,
            }
        )
    return out


def normalize_goals_by_page(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Нормализация ответа goals_by_page():
    - landingPage
    - visits
    - goal_visits
    - goal_cr_pct (conversionRate в процентах)
    """
    out: List[Dict[str, Any]] = []
    data = resp.get("data") or []
    for row in data:
        dims = row.get("dimensions") or []
        url = ""
        if dims and isinstance(dims, list) and isinstance(dims[0], dict):
            url = str(dims[0].get("name", "")).strip()
        metrics = row.get("metrics") or []
        visits = float(metrics[0]) if len(metrics) > 0 else 0.0
        goal_visits = float(metrics[1]) if len(metrics) > 1 else 0.0
        goal_cr = float(metrics[2]) if len(metrics) > 2 else 0.0
        out.append(
            {
                "landingPage": url or "(unknown)",
                "visits": visits,
                "goal_visits": goal_visits,
                "goal_cr_pct": goal_cr,
            }
        )
    return out


def normalize_goals_list(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Нормализация списка целей из Management API.
    Возвращает список:
      - id
      - name
      - type
    """
    goals = resp.get("goals") or []
    out: List[Dict[str, Any]] = []
    if not isinstance(goals, list):
        return out
    for g in goals:
        if not isinstance(g, dict):
            continue
        out.append(
            {
                "id": int(g.get("id", 0) or 0),
                "name": str(g.get("name", "")).strip(),
                "type": str(g.get("type", "")).strip(),
            }
        )
    # Стабильная сортировка по id
    return sorted(out, key=lambda x: x["id"])

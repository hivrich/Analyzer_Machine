from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from app.metrika_client import (
    MetrikaClient,
    normalize_goals_by_page,
    normalize_goals_by_source,
)


def _fetch_limit_for_dimension(limit: int, dimension: str) -> int:
    """
    Для измерений с большим количеством строк (landingPage) стараемся брать больше строк,
    чтобы вклады/итоги были ближе к реальности без дополнительных API вызовов.
    """
    if dimension == "landingPage":
        return max(5000, int(limit) if limit and limit > 0 else 0)
    return int(limit) if limit and limit > 0 else 50


def load_or_fetch_goals_by_source(
    client: str,
    date1: str,
    date2: str,
    goal_id: int,
    limit: int,
    refresh: bool,
    metrika_client: MetrikaClient,
) -> List[Dict[str, Any]]:
    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)

    raw_file = cache_dir / f"metrika_goals_by_source_raw_{goal_id}_{date1}_{date2}.json"
    norm_file = cache_dir / f"metrika_goals_by_source_norm_{goal_id}_{date1}_{date2}.json"

    fetch_limit = _fetch_limit_for_dimension(limit, "source")

    if not refresh and norm_file.exists():
        try:
            cached = json.loads(norm_file.read_text(encoding="utf-8"))
            if isinstance(cached, list) and len(cached) >= max(1, min(fetch_limit, 50)):
                return cached
        except Exception:
            pass

    raw_data = metrika_client.goals_by_source(date1, date2, goal_id, fetch_limit)
    normalized_data = normalize_goals_by_source(raw_data)

    raw_file.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2), encoding="utf-8")
    norm_file.write_text(json.dumps(normalized_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return normalized_data


def load_or_fetch_goals_by_page(
    client: str,
    date1: str,
    date2: str,
    goal_id: int,
    limit: int,
    refresh: bool,
    metrika_client: MetrikaClient,
) -> List[Dict[str, Any]]:
    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)

    raw_file = cache_dir / f"metrika_goals_by_page_raw_{goal_id}_{date1}_{date2}.json"
    norm_file = cache_dir / f"metrika_goals_by_page_norm_{goal_id}_{date1}_{date2}.json"

    fetch_limit = _fetch_limit_for_dimension(limit, "landingPage")

    if not refresh and norm_file.exists():
        try:
            cached = json.loads(norm_file.read_text(encoding="utf-8"))
            if isinstance(cached, list) and len(cached) >= max(1, fetch_limit):
                return cached
        except Exception:
            pass

    raw_data = metrika_client.goals_by_page(date1, date2, goal_id, fetch_limit)
    normalized_data = normalize_goals_by_page(raw_data)

    raw_file.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2), encoding="utf-8")
    norm_file.write_text(json.dumps(normalized_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return normalized_data


def compare_goals_periods(
    data_p1: List[Dict[str, Any]],
    data_p2: List[Dict[str, Any]],
    key_field: str,
) -> List[Dict[str, Any]]:
    """
    Универсальное сравнение для goals: по sources или по landing pages.
    """
    m1 = {row.get(key_field, "(unknown)"): row for row in data_p1}
    m2 = {row.get(key_field, "(unknown)"): row for row in data_p2}
    keys = set(m1.keys()) | set(m2.keys())

    rows: List[Dict[str, Any]] = []
    for k in keys:
        r1 = m1.get(k) or {}
        r2 = m2.get(k) or {}

        visits_p1 = float(r1.get("visits", 0.0) or 0.0)
        visits_p2 = float(r2.get("visits", 0.0) or 0.0)
        goal_visits_p1 = float(r1.get("goal_visits", 0.0) or 0.0)
        goal_visits_p2 = float(r2.get("goal_visits", 0.0) or 0.0)
        cr_p1 = float(r1.get("goal_cr_pct", 0.0) or 0.0)
        cr_p2 = float(r2.get("goal_cr_pct", 0.0) or 0.0)

        delta_goal_visits_abs = goal_visits_p2 - goal_visits_p1
        delta_goal_visits_pct = (delta_goal_visits_abs / max(goal_visits_p1, 1.0)) * 100.0
        delta_cr_pp = cr_p2 - cr_p1  # percentage points

        rows.append(
            {
                key_field: k,
                "visits_p1": visits_p1,
                "visits_p2": visits_p2,
                "goal_visits_p1": goal_visits_p1,
                "goal_visits_p2": goal_visits_p2,
                "goal_cr_p1": cr_p1,
                "goal_cr_p2": cr_p2,
                "delta_goal_visits_abs": delta_goal_visits_abs,
                "delta_goal_visits_pct": delta_goal_visits_pct,
                "delta_cr_pp": delta_cr_pp,
            }
        )

    return rows


def calculate_contributions(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Вклад считаем по delta_goal_visits_abs (изменение конверсионных визитов).
    """
    total_delta = sum(r["delta_goal_visits_abs"] for r in rows)
    if total_delta == 0:
        for r in rows:
            r["contribution_pct"] = 0.0
    else:
        for r in rows:
            r["contribution_pct"] = (r["delta_goal_visits_abs"] / total_delta) * 100.0
    return rows


def sort_rows(rows: List[Dict[str, Any]], key_field: str) -> List[Dict[str, Any]]:
    return sorted(rows, key=lambda x: (-abs(x["delta_goal_visits_abs"]), str(x.get(key_field, ""))))


def _totals_from_rows(all_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_visits_p1 = sum(r["visits_p1"] for r in all_rows)
    total_visits_p2 = sum(r["visits_p2"] for r in all_rows)
    total_goal_visits_p1 = sum(r["goal_visits_p1"] for r in all_rows)
    total_goal_visits_p2 = sum(r["goal_visits_p2"] for r in all_rows)

    total_cr_p1 = (total_goal_visits_p1 / max(total_visits_p1, 1.0)) * 100.0
    total_cr_p2 = (total_goal_visits_p2 / max(total_visits_p2, 1.0)) * 100.0

    total_delta_goal_visits_abs = total_goal_visits_p2 - total_goal_visits_p1
    total_delta_goal_visits_pct = (total_delta_goal_visits_abs / max(total_goal_visits_p1, 1.0)) * 100.0
    total_delta_cr_pp = total_cr_p2 - total_cr_p1

    return {
        "total_visits_p1": total_visits_p1,
        "total_visits_p2": total_visits_p2,
        "total_goal_visits_p1": total_goal_visits_p1,
        "total_goal_visits_p2": total_goal_visits_p2,
        "total_cr_p1": total_cr_p1,
        "total_cr_p2": total_cr_p2,
        "total_delta_goal_visits_abs": total_delta_goal_visits_abs,
        "total_delta_goal_visits_pct": total_delta_goal_visits_pct,
        "total_delta_cr_pp": total_delta_cr_pp,
    }


def create_workbook(
    client: str,
    counter_id: int,
    goal_id: int,
    dimension: str,
    p1_start: str,
    p1_end: str,
    p2_start: str,
    p2_end: str,
    limit: int,
    refresh_used: bool,
    rows: List[Dict[str, Any]],
    all_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "meta": {
            "client": client,
            "counter_id": counter_id,
            "goal_id": goal_id,
            "dimension": dimension,
            "p1_start": p1_start,
            "p1_end": p1_end,
            "p2_start": p2_start,
            "p2_end": p2_end,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "limit": limit,
            "refresh_used": refresh_used,
        },
        "totals": _totals_from_rows(all_rows),
        "rows": rows[:limit] if limit > 0 else rows,
    }


def workbook_filename(
    kind: str,
    goal_id: int,
    p1_start: str,
    p1_end: str,
    p2_start: str,
    p2_end: str,
) -> str:
    # kind: goals_by_source / goals_by_page
    return (
        f"analysis_{kind}_{goal_id}_"
        f"{p1_start.replace('-', '')}{p1_end.replace('-', '')}"
        f"__{p2_start.replace('-', '')}{p2_end.replace('-', '')}.json"
    )



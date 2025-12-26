from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from app.ym_webmaster_client import YMWebmasterClient, normalize_webmaster_queries


def load_or_fetch_queries(
    client: str,
    date1: str,
    date2: str,
    limit: int,
    refresh: bool,
    ym: YMWebmasterClient,
) -> List[Dict[str, Any]]:
    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)

    raw_file = cache_dir / f"ym_webmaster_queries_raw_{date1}_{date2}.json"
    norm_file = cache_dir / f"ym_webmaster_queries_norm_{date1}_{date2}.json"

    if not refresh and norm_file.exists():
        try:
            cached = json.loads(norm_file.read_text(encoding="utf-8"))
            if isinstance(cached, list) and len(cached) >= max(1, int(limit) if limit and limit > 0 else 1):
                return cached
        except Exception:
            pass

    raw = ym.popular_queries(date_from=date1, date_to=date2, limit=int(limit))
    norm = normalize_webmaster_queries(raw)

    raw_file.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    norm_file.write_text(json.dumps(norm, ensure_ascii=False, indent=2), encoding="utf-8")
    return norm


def compare_queries_periods(data_p1: List[Dict[str, Any]], data_p2: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    m1 = {str(r.get("query", "")): r for r in data_p1}
    m2 = {str(r.get("query", "")): r for r in data_p2}
    keys = set(m1.keys()) | set(m2.keys())

    rows: List[Dict[str, Any]] = []
    for k in keys:
        r1 = m1.get(k) or {}
        r2 = m2.get(k) or {}

        clicks_p1 = float(r1.get("clicks", 0.0) or 0.0)
        clicks_p2 = float(r2.get("clicks", 0.0) or 0.0)
        shows_p1 = float(r1.get("shows", 0.0) or 0.0)
        shows_p2 = float(r2.get("shows", 0.0) or 0.0)
        pos_p1 = float(r1.get("position", 0.0) or 0.0)
        pos_p2 = float(r2.get("position", 0.0) or 0.0)

        delta_clicks = clicks_p2 - clicks_p1
        delta_clicks_pct = (delta_clicks / max(clicks_p1, 1.0)) * 100.0
        delta_shows = shows_p2 - shows_p1
        delta_position = pos_p2 - pos_p1

        rows.append(
            {
                "query": k,
                "clicks_p1": clicks_p1,
                "clicks_p2": clicks_p2,
                "shows_p1": shows_p1,
                "shows_p2": shows_p2,
                "position_p1": pos_p1,
                "position_p2": pos_p2,
                "delta_clicks": delta_clicks,
                "delta_clicks_pct": delta_clicks_pct,
                "delta_shows": delta_shows,
                "delta_position": delta_position,
            }
        )
    return rows


def calculate_contributions(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    total_delta = sum(r["delta_clicks"] for r in rows)
    if total_delta == 0:
        for r in rows:
            r["contribution_pct"] = 0.0
    else:
        for r in rows:
            r["contribution_pct"] = (r["delta_clicks"] / total_delta) * 100.0
    return rows


def sort_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(rows, key=lambda x: (-abs(x["delta_clicks"]), str(x.get("query", ""))))


def _totals(all_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_clicks_p1 = sum(r["clicks_p1"] for r in all_rows)
    total_clicks_p2 = sum(r["clicks_p2"] for r in all_rows)
    total_shows_p1 = sum(r["shows_p1"] for r in all_rows)
    total_shows_p2 = sum(r["shows_p2"] for r in all_rows)
    total_delta_clicks = total_clicks_p2 - total_clicks_p1
    total_delta_pct = (total_delta_clicks / max(total_clicks_p1, 1.0)) * 100.0
    return {
        "total_clicks_p1": total_clicks_p1,
        "total_clicks_p2": total_clicks_p2,
        "total_shows_p1": total_shows_p1,
        "total_shows_p2": total_shows_p2,
        "total_delta_clicks": total_delta_clicks,
        "total_delta_pct": total_delta_pct,
    }


def create_workbook(
    client: str,
    host_id: str,
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
            "host_id": host_id,
            "p1_start": p1_start,
            "p1_end": p1_end,
            "p2_start": p2_start,
            "p2_end": p2_end,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "limit": limit,
            "refresh_used": refresh_used,
        },
        "totals": _totals(all_rows),
        "rows": rows[:limit] if limit > 0 else rows,
    }


def workbook_filename(p1_start: str, p1_end: str, p2_start: str, p2_end: str) -> str:
    return (
        f"analysis_ym_webmaster_queries_"
        f"{p1_start.replace('-', '')}{p1_end.replace('-', '')}"
        f"__{p2_start.replace('-', '')}{p2_end.replace('-', '')}.json"
    )



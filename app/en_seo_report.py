from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ORGANIC_SOURCE_NAMES = {
    "search engine traffic",
    "organic",
    "organic search",
    "search",
}


def is_en_landing_page(page: str) -> bool:
    normalized = str(page or "").strip()
    if not normalized:
        return False
    return (
        normalized == "https://stas.run/en"
        or normalized.startswith("https://stas.run/en/")
        or normalized == "/en"
        or normalized.startswith("/en/")
    )


def is_organic_source(source: str) -> bool:
    normalized = str(source or "").strip().lower()
    return normalized in ORGANIC_SOURCE_NAMES or "search" in normalized or "organic" in normalized


def _weighted_position(rows: List[Dict[str, Any]]) -> float:
    impressions = sum(float(row.get("impressions", 0.0) or 0.0) for row in rows)
    if impressions <= 0:
        return 0.0
    weighted = sum(
        float(row.get("position", 0.0) or 0.0) * float(row.get("impressions", 0.0) or 0.0)
        for row in rows
    )
    return weighted / impressions


def _aggregate_gsc(rows: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        value = str(row.get(key, "") or "")
        if not value:
            continue
        item = grouped.setdefault(
            value,
            {
                key: value,
                "clicks": 0.0,
                "impressions": 0.0,
                "position_weighted_sum": 0.0,
            },
        )
        clicks = float(row.get("clicks", 0.0) or 0.0)
        impressions = float(row.get("impressions", 0.0) or 0.0)
        position = float(row.get("position", 0.0) or 0.0)
        item["clicks"] += clicks
        item["impressions"] += impressions
        item["position_weighted_sum"] += position * impressions

    out: List[Dict[str, Any]] = []
    for item in grouped.values():
        impressions = float(item["impressions"] or 0.0)
        clicks = float(item["clicks"] or 0.0)
        out.append(
            {
                key: item[key],
                "clicks": clicks,
                "impressions": impressions,
                "ctr": (clicks / impressions) * 100.0 if impressions > 0 else 0.0,
                "position": (float(item["position_weighted_sum"]) / impressions) if impressions > 0 else 0.0,
            }
        )
    return sorted(out, key=lambda row: (-float(row["clicks"]), -float(row["impressions"]), str(row[key])))


def create_en_seo_weekly_report(
    *,
    client: str,
    site_url: str,
    counter_id: int,
    goal_id: int,
    date1: str,
    date2: str,
    gsc_pages: List[Dict[str, Any]],
    gsc_query_page: List[Dict[str, Any]],
    goals_by_source: List[Dict[str, Any]],
    goals_by_source_page: List[Dict[str, Any]],
    limit: int,
    refresh_used: bool,
) -> Dict[str, Any]:
    en_pages = [row for row in gsc_pages if is_en_landing_page(str(row.get("page", "")))]
    en_query_page = [row for row in gsc_query_page if is_en_landing_page(str(row.get("page", "")))]

    total_clicks = sum(float(row.get("clicks", 0.0) or 0.0) for row in en_pages)
    total_impressions = sum(float(row.get("impressions", 0.0) or 0.0) for row in en_pages)
    total_ctr = (total_clicks / total_impressions) * 100.0 if total_impressions > 0 else 0.0
    total_position = _weighted_position(en_pages)

    top_pages = _aggregate_gsc(en_pages, "page")[:limit]
    top_queries = _aggregate_gsc(en_query_page, "query")[:limit]

    signup_success_by_source = sorted(
        goals_by_source,
        key=lambda row: (-float(row.get("goal_visits", 0.0) or 0.0), -float(row.get("visits", 0.0) or 0.0), str(row.get("source", ""))),
    )[:limit]

    en_organic_source_page_rows = [
        row
        for row in goals_by_source_page
        if is_organic_source(str(row.get("source", ""))) and is_en_landing_page(str(row.get("landingPage", "")))
    ]
    en_organic_signups = sum(float(row.get("goal_visits", 0.0) or 0.0) for row in en_organic_source_page_rows)

    return {
        "meta": {
            "client": client,
            "site_url": site_url,
            "counter_id": counter_id,
            "goal_id": goal_id,
            "date1": date1,
            "date2": date2,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "limit": limit,
            "refresh_used": refresh_used,
        },
        "gsc_en": {
            "clicks": total_clicks,
            "impressions": total_impressions,
            "ctr": total_ctr,
            "position": total_position,
            "top_queries": top_queries,
            "top_pages": top_pages,
        },
        "metrika_signup_success": {
            "by_source": signup_success_by_source,
            "en_organic_signups": en_organic_signups,
            "en_organic_source_page_rows": en_organic_source_page_rows[:limit],
        },
    }


def report_filename(date1: str, date2: str) -> str:
    return f"en_seo_weekly_report_{date1}_{date2}.json"


def save_report(client: str, report: Dict[str, Any], date1: str, date2: str) -> Path:
    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / report_filename(date1, date2)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

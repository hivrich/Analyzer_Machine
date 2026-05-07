from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse


ORGANIC_SOURCE_NAMES = {
    "search engine traffic",
    "organic",
    "organic search",
    "search",
}

PRODUCT_EVENT_FIELDS = [
    "signups",
    "oauth_start",
    "intervals_connected",
    "gpt_connected",
    "claude_connected",
    "first_data_request",
    "training_processed",
]


def _as_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _rate(numerator: float, denominator: float) -> float:
    return (numerator / denominator) * 100.0 if denominator > 0 else 0.0


def is_organic_source(source: str) -> bool:
    normalized = str(source or "").strip().lower()
    return normalized in ORGANIC_SOURCE_NAMES or "search" in normalized or "organic" in normalized


def normalize_landing_page(page: str) -> str:
    value = str(page or "").strip()
    if not value or value == "(unknown)":
        return "(unknown)"

    parsed = urlparse(value)
    path = parsed.path if parsed.scheme and parsed.netloc else value.split("?", 1)[0].split("#", 1)[0]
    if not path:
        path = "/"
    if not path.startswith("/"):
        path = f"/{path}"
    if len(path) > 1:
        path = path.rstrip("/")
    return path


def _display_url(site_url: str, landing_page: str) -> str:
    if landing_page == "(unknown)":
        return landing_page
    base = str(site_url or "").strip().rstrip("/")
    return f"{base}{landing_page}" if base else landing_page


def _aggregate_gsc_pages(rows: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        landing_page = normalize_landing_page(str(row.get("page", "")))
        item = grouped.setdefault(
            landing_page,
            {
                "clicks": 0.0,
                "impressions": 0.0,
                "position_weighted_sum": 0.0,
            },
        )
        clicks = _as_float(row.get("clicks"))
        impressions = _as_float(row.get("impressions"))
        position = _as_float(row.get("position"))
        item["clicks"] += clicks
        item["impressions"] += impressions
        item["position_weighted_sum"] += position * impressions

    out: Dict[str, Dict[str, Any]] = {}
    for landing_page, item in grouped.items():
        clicks = _as_float(item["clicks"])
        impressions = _as_float(item["impressions"])
        out[landing_page] = {
            "clicks": clicks,
            "impressions": impressions,
            "ctr": _rate(clicks, impressions),
            "position": (_as_float(item["position_weighted_sum"]) / impressions) if impressions > 0 else 0.0,
        }
    return out


def _aggregate_metrika_organic_pages(
    organic_pages: Iterable[Dict[str, Any]],
    goals_by_source_page: Iterable[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}

    for row in organic_pages:
        landing_page = normalize_landing_page(str(row.get("landingPage", "")))
        item = grouped.setdefault(
            landing_page,
            {
                "organic_visits": 0.0,
                "organic_users": 0.0,
                "signup_goal": 0.0,
            },
        )
        item["organic_visits"] += _as_float(row.get("visits"))
        item["organic_users"] += _as_float(row.get("users"))

    for row in goals_by_source_page:
        if not is_organic_source(str(row.get("source", ""))):
            continue
        landing_page = normalize_landing_page(str(row.get("landingPage", "")))
        item = grouped.setdefault(
            landing_page,
            {
                "organic_visits": 0.0,
                "organic_users": 0.0,
                "signup_goal": 0.0,
            },
        )
        item["signup_goal"] += _as_float(row.get("goal_visits"))
        if item["organic_visits"] <= 0:
            item["organic_visits"] += _as_float(row.get("visits"))

    for item in grouped.values():
        item["signup_goal_cr"] = _rate(_as_float(item["signup_goal"]), _as_float(item["organic_visits"]))
    return grouped


def empty_product_db_status(
    *,
    env_var: str,
    available: bool = False,
    reason: str = "env_missing",
    rows: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    return {
        "available": available,
        "env_var": env_var,
        "reason": reason,
        "rows": rows or [],
    }


def load_product_activation_by_landing_page(
    *,
    date1: str,
    date2: str,
    env_var: str = "STAS_DATABASE_URL",
) -> Dict[str, Any]:
    db_url = os.getenv(env_var)
    if not db_url:
        return empty_product_db_status(env_var=env_var, reason="env_missing")

    try:
        import psycopg  # type: ignore
        from psycopg.rows import dict_row  # type: ignore
    except Exception:
        return empty_product_db_status(env_var=env_var, reason="psycopg_missing")

    query = """
        WITH organic_signups AS (
            SELECT
                ue.athlete_id,
                COALESCE(NULLIF(ue.metadata->>'landingPage', ''), '(unknown)') AS landing_page,
                MIN(ue.created_at) AS signup_at
            FROM user_event ue
            WHERE ue.event_type = 'signup'
              AND ue.created_at >= %(date1)s::date
              AND ue.created_at < (%(date2)s::date + INTERVAL '1 day')
              AND (
                ue.metadata->>'firstTouchSource' = 'organic'
                OR ue.metadata->>'signupSource' = 'en_organic'
                OR ue.metadata->>'source' = 'organic'
              )
            GROUP BY ue.athlete_id, COALESCE(NULLIF(ue.metadata->>'landingPage', ''), '(unknown)')
        ),
        first_events AS (
            SELECT
                s.landing_page,
                s.athlete_id,
                MIN(e.created_at) FILTER (WHERE e.event_type = 'oauth_start') AS oauth_start_at,
                MIN(e.created_at) FILTER (WHERE e.event_type = 'intervals_connected') AS intervals_connected_at,
                MIN(e.created_at) FILTER (WHERE e.event_type = 'gpt_connected') AS gpt_connected_at,
                MIN(e.created_at) FILTER (WHERE e.event_type = 'claude_connected') AS claude_connected_at,
                MIN(e.created_at) FILTER (WHERE e.event_type IN ('gpt_data_requested', 'claude_data_requested')) AS first_data_request_at,
                MIN(e.created_at) FILTER (WHERE e.event_type = 'training_processed') AS training_processed_at
            FROM organic_signups s
            LEFT JOIN user_event e
              ON e.athlete_id = s.athlete_id
             AND e.created_at >= s.signup_at
             AND e.created_at < (%(date2)s::date + INTERVAL '1 day')
            GROUP BY s.landing_page, s.athlete_id
        )
        SELECT
            landing_page,
            COUNT(*)::int AS signups,
            COUNT(oauth_start_at)::int AS oauth_start,
            COUNT(intervals_connected_at)::int AS intervals_connected,
            COUNT(gpt_connected_at)::int AS gpt_connected,
            COUNT(claude_connected_at)::int AS claude_connected,
            COUNT(first_data_request_at)::int AS first_data_request,
            COUNT(training_processed_at)::int AS training_processed
        FROM first_events
        GROUP BY landing_page
        ORDER BY signups DESC, landing_page ASC
    """

    try:
        with psycopg.connect(db_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(query, {"date1": date1, "date2": date2})
                rows = [dict(row) for row in cur.fetchall()]
    except Exception as exc:
        return empty_product_db_status(env_var=env_var, reason=f"query_failed:{exc.__class__.__name__}")

    for row in rows:
        row["landingPage"] = normalize_landing_page(str(row.pop("landing_page", "")))
    return empty_product_db_status(env_var=env_var, available=True, reason="ok", rows=rows)


def create_seo_activation_funnel_report(
    *,
    client: str,
    site_url: str,
    counter_id: int,
    goal_id: int,
    date1: str,
    date2: str,
    gsc_pages: List[Dict[str, Any]],
    metrika_organic_pages: List[Dict[str, Any]],
    goals_by_source_page: List[Dict[str, Any]],
    product_db: Dict[str, Any],
    limit: int,
    refresh_used: bool,
    product_db_url_env: str = "STAS_DATABASE_URL",
) -> Dict[str, Any]:
    gsc_by_page = _aggregate_gsc_pages(gsc_pages)
    metrika_by_page = _aggregate_metrika_organic_pages(metrika_organic_pages, goals_by_source_page)
    product_rows = product_db.get("rows") if isinstance(product_db.get("rows"), list) else []
    product_by_page = {
        normalize_landing_page(str(row.get("landingPage", ""))): row
        for row in product_rows
        if isinstance(row, dict)
    }

    pages = set(gsc_by_page.keys()) | set(metrika_by_page.keys()) | set(product_by_page.keys())
    rows: List[Dict[str, Any]] = []
    for landing_page in pages:
        gsc = gsc_by_page.get(landing_page, {})
        metrika = metrika_by_page.get(landing_page, {})
        product = product_by_page.get(landing_page, {})

        signups = _as_float(product.get("signups"))
        intervals_connected = _as_float(product.get("intervals_connected"))
        first_data_request = _as_float(product.get("first_data_request"))
        training_processed = _as_float(product.get("training_processed"))
        signup_goal = _as_float(metrika.get("signup_goal"))
        organic_visits = _as_float(metrika.get("organic_visits"))

        row = {
            "landingPage": landing_page,
            "page_url": _display_url(site_url, landing_page),
            "gsc": {
                "clicks": _as_float(gsc.get("clicks")),
                "impressions": _as_float(gsc.get("impressions")),
                "ctr": _as_float(gsc.get("ctr")),
                "position": _as_float(gsc.get("position")),
            },
            "metrika": {
                "organic_visits": organic_visits,
                "organic_users": _as_float(metrika.get("organic_users")),
                "signup_goal": signup_goal,
                "signup_goal_cr": _as_float(metrika.get("signup_goal_cr")),
            },
            "product": {
                field: int(_as_float(product.get(field)))
                for field in PRODUCT_EVENT_FIELDS
            },
            "conversion_rates": {
                "gsc_click_to_metrika_visit": _rate(organic_visits, _as_float(gsc.get("clicks"))),
                "metrika_visit_to_signup_goal": _rate(signup_goal, organic_visits),
                "signup_to_intervals_connected": _rate(intervals_connected, signups),
                "signup_to_first_data_request": _rate(first_data_request, signups),
                "signup_to_training_processed": _rate(training_processed, signups),
            },
        }
        rows.append(row)

    rows = sorted(
        rows,
        key=lambda row: (
            -_as_float(row["gsc"]["clicks"]),
            -_as_float(row["metrika"]["organic_visits"]),
            -_as_float(row["product"]["signups"]),
            str(row["landingPage"]),
        ),
    )

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
        "product_db": {
            "available": bool(product_db.get("available")),
            "env_var": product_db_url_env,
            "reason": str(product_db.get("reason", "")),
        },
        "totals": _totals(rows),
        "rows": rows[:limit] if limit > 0 else rows,
    }


def _totals(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    clicks = sum(_as_float(row["gsc"]["clicks"]) for row in rows)
    impressions = sum(_as_float(row["gsc"]["impressions"]) for row in rows)
    organic_visits = sum(_as_float(row["metrika"]["organic_visits"]) for row in rows)
    organic_users = sum(_as_float(row["metrika"]["organic_users"]) for row in rows)
    signup_goal = sum(_as_float(row["metrika"]["signup_goal"]) for row in rows)
    signups = sum(_as_float(row["product"]["signups"]) for row in rows)
    intervals_connected = sum(_as_float(row["product"]["intervals_connected"]) for row in rows)
    first_data_request = sum(_as_float(row["product"]["first_data_request"]) for row in rows)
    training_processed = sum(_as_float(row["product"]["training_processed"]) for row in rows)

    return {
        "gsc_clicks": clicks,
        "gsc_impressions": impressions,
        "gsc_ctr": _rate(clicks, impressions),
        "metrika_organic_visits": organic_visits,
        "metrika_organic_users": organic_users,
        "metrika_signup_goal": signup_goal,
        "product_signups": signups,
        "product_intervals_connected": intervals_connected,
        "product_first_data_request": first_data_request,
        "product_training_processed": training_processed,
        "metrika_visit_to_signup_goal": _rate(signup_goal, organic_visits),
        "signup_to_intervals_connected": _rate(intervals_connected, signups),
        "signup_to_first_data_request": _rate(first_data_request, signups),
        "signup_to_training_processed": _rate(training_processed, signups),
    }


def report_filename(date1: str, date2: str) -> str:
    return f"seo_activation_funnel_{date1}_{date2}.json"


def save_report(client: str, report: Dict[str, Any], date1: str, date2: str) -> Path:
    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / report_filename(date1, date2)
    report.setdefault("meta", {})["cache_path"] = str(path)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

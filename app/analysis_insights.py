from __future__ import annotations

from typing import Any, Dict, List, Optional


def _first_present_key(payload: Dict[str, Any], candidates: List[str]) -> Optional[str]:
    for key in candidates:
        if key in payload:
            return key
    return None


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.1f}"
    if isinstance(value, int):
        return str(value)
    return str(value)


def print_insights(
    rows: Optional[List[Dict[str, Any]]] = None,
    totals: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> None:
    rows = rows or []
    totals = totals or {}

    metric_name = str(kwargs.get("metric_name", "metric"))
    dimension_name = str(kwargs.get("dimension_name", "dimension"))

    total_p1_key = _first_present_key(
        totals,
        [
            f"total_{metric_name}_p1",
            "total_visits_p1",
            "total_clicks_p1",
        ],
    )
    total_p2_key = _first_present_key(
        totals,
        [
            f"total_{metric_name}_p2",
            "total_visits_p2",
            "total_clicks_p2",
        ],
    )
    total_delta_key = _first_present_key(
        totals,
        [
            f"total_delta_{metric_name}_abs",
            f"total_delta_{metric_name}",
            "total_delta_abs",
            "total_delta_clicks",
        ],
    )
    total_delta_pct_key = _first_present_key(
        totals,
        [
            f"total_delta_{metric_name}_pct",
            "total_delta_pct",
        ],
    )

    print(f"Insights: {metric_name} by {dimension_name}")
    if total_p1_key and total_p2_key:
        print(
            "Totals: "
            f"P1={_format_value(totals[total_p1_key])}, "
            f"P2={_format_value(totals[total_p2_key])}"
        )
    if total_delta_key:
        summary = f"Delta={_format_value(totals[total_delta_key])}"
        if total_delta_pct_key:
            summary += f" ({_format_value(totals[total_delta_pct_key])}%)"
        print(summary)

    if not rows:
        print("No rows.")
        return

    top_growth = max(rows, key=lambda item: float(item.get("contribution_pct", 0.0) or 0.0))
    top_decline = min(rows, key=lambda item: float(item.get("contribution_pct", 0.0) or 0.0))

    label_growth = top_growth.get(dimension_name, "(unknown)")
    label_decline = top_decline.get(dimension_name, "(unknown)")

    growth_delta = (
        top_growth.get(f"delta_{metric_name}_abs")
        if f"delta_{metric_name}_abs" in top_growth
        else top_growth.get(f"delta_{metric_name}")
        if f"delta_{metric_name}" in top_growth
        else top_growth.get("delta_abs")
        if "delta_abs" in top_growth
        else top_growth.get("delta_clicks", 0.0)
    )
    decline_delta = (
        top_decline.get(f"delta_{metric_name}_abs")
        if f"delta_{metric_name}_abs" in top_decline
        else top_decline.get(f"delta_{metric_name}")
        if f"delta_{metric_name}" in top_decline
        else top_decline.get("delta_abs")
        if "delta_abs" in top_decline
        else top_decline.get("delta_clicks", 0.0)
    )

    print(f"Top growth: {label_growth} ({_format_value(growth_delta)})")
    print(f"Top decline: {label_decline} ({_format_value(decline_delta)})")

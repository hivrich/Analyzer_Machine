from __future__ import annotations

import re
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from app.orchestrator.models import InvestigationPeriod


_MONTHS = {
    "январ": 1,
    "феврал": 2,
    "март": 3,
    "апрел": 4,
    "ма": 5,
    "июн": 6,
    "июл": 7,
    "август": 8,
    "сентябр": 9,
    "октябр": 10,
    "ноябр": 11,
    "декабр": 12,
}


def _fmt(d: date) -> str:
    return d.isoformat()


def _previous_period(start: date, end: date) -> tuple[date, date]:
    delta = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=delta - 1)
    return prev_start, prev_end


def _month_period(year: int, month: int) -> tuple[date, date]:
    last_day = monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def _parse_month_query(query: str) -> Optional[tuple[date, date]]:
    lowered = query.lower()
    for token, month in _MONTHS.items():
        if token in lowered:
            match = re.search(rf"{token}\w*\s+(\d{{4}})", lowered)
            if match:
                return _month_period(int(match.group(1)), month)
    return None


def resolve_periods(
    query: str,
    p1_start: str | None = None,
    p1_end: str | None = None,
    p2_start: str | None = None,
    p2_end: str | None = None,
    today: date | None = None,
) -> InvestigationPeriod:
    if p1_start and p1_end and p2_start and p2_end:
        return InvestigationPeriod(
            p1_start=p1_start,
            p1_end=p1_end,
            p2_start=p2_start,
            p2_end=p2_end,
            source="explicit",
            description=f"{p1_start}..{p1_end} vs {p2_start}..{p2_end}",
        )

    dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", query)
    if len(dates) >= 4:
        return InvestigationPeriod(
            p1_start=dates[0],
            p1_end=dates[1],
            p2_start=dates[2],
            p2_end=dates[3],
            source="query-iso",
            description=f"{dates[0]}..{dates[1]} vs {dates[2]}..{dates[3]}",
        )

    if len(dates) == 2:
        target_start = date.fromisoformat(dates[0])
        target_end = date.fromisoformat(dates[1])
        prev_start, prev_end = _previous_period(target_start, target_end)
        return InvestigationPeriod(
            p1_start=_fmt(prev_start),
            p1_end=_fmt(prev_end),
            p2_start=_fmt(target_start),
            p2_end=_fmt(target_end),
            source="query-iso-single-period",
            description=f"{_fmt(prev_start)}..{_fmt(prev_end)} vs {_fmt(target_start)}..{_fmt(target_end)}",
        )

    month_period = _parse_month_query(query)
    if month_period is not None:
        target_start, target_end = month_period
        prev_start, prev_end = _month_period(target_start.year - 1, target_start.month)
        return InvestigationPeriod(
            p1_start=_fmt(prev_start),
            p1_end=_fmt(prev_end),
            p2_start=_fmt(target_start),
            p2_end=_fmt(target_end),
            source="query-month",
            description=f"{_fmt(prev_start)}..{_fmt(prev_end)} vs {_fmt(target_start)}..{_fmt(target_end)}",
        )

    reference = today or date.today()
    p2_end_dt = reference - timedelta(days=1)
    p2_start_dt = p2_end_dt - timedelta(days=29)
    p1_end_dt = p2_start_dt - timedelta(days=1)
    p1_start_dt = p1_end_dt - timedelta(days=29)
    return InvestigationPeriod(
        p1_start=_fmt(p1_start_dt),
        p1_end=_fmt(p1_end_dt),
        p2_start=_fmt(p2_start_dt),
        p2_end=_fmt(p2_end_dt),
        source="default-last-30-days",
        description=f"{_fmt(p1_start_dt)}..{_fmt(p1_end_dt)} vs {_fmt(p2_start_dt)}..{_fmt(p2_end_dt)}",
    )

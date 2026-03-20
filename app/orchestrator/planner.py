from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Set

from app.analysis_goals import workbook_filename as goals_workbook_filename
from app.analysis_gsc import workbook_filename as gsc_workbook_filename
from app.analysis_pages import _slugify_for_filename
from app.analysis_ym_webmaster import workbook_filename as ymw_workbook_filename
from app.orchestrator.models import (
    ExecutedStep,
    GoalSelection,
    InvestigationAvailability,
    InvestigationIntent,
    InvestigationPeriod,
    PlannedStep,
)


def _sources_workbook(client: str, period: InvestigationPeriod) -> str:
    return str(
        Path("data_cache")
        / client
        / (
            f"analysis_sources_{period.p1_start.replace('-', '')}{period.p1_end.replace('-', '')}"
            f"__{period.p2_start.replace('-', '')}{period.p2_end.replace('-', '')}.json"
        )
    )


def _pages_workbook(client: str, period: InvestigationPeriod) -> str:
    return str(
        Path("data_cache")
        / client
        / (
            f"analysis_pages_{period.p1_start.replace('-', '')}{period.p1_end.replace('-', '')}"
            f"__{period.p2_start.replace('-', '')}{period.p2_end.replace('-', '')}.json"
        )
    )


def _pages_by_source_workbook(client: str, period: InvestigationPeriod, source: str) -> str:
    slug = _slugify_for_filename(source)
    return str(
        Path("data_cache")
        / client
        / (
            f"analysis_pages_by_source_{slug}_"
            f"{period.p1_start.replace('-', '')}{period.p1_end.replace('-', '')}"
            f"__{period.p2_start.replace('-', '')}{period.p2_end.replace('-', '')}.json"
        )
    )


def _build_step(
    *,
    kind: str,
    client: str,
    period: InvestigationPeriod,
    goal_selection: GoalSelection,
    refresh: bool,
    limit: int,
    round_number: int,
) -> PlannedStep:
    if kind == "analyze_sources":
        return PlannedStep(
            id=f"round-{round_number}-sources",
            title="Сравнение источников трафика",
            kind=kind,
            source="metrika",
            params={
                "client": client,
                "p1_start": period.p1_start,
                "p1_end": period.p1_end,
                "p2_start": period.p2_start,
                "p2_end": period.p2_end,
                "limit": limit,
                "refresh": refresh,
                "format": "insights",
            },
            expected_artifacts=[_sources_workbook(client, period)],
        )
    if kind == "analyze_pages":
        return PlannedStep(
            id=f"round-{round_number}-pages",
            title="Сравнение входных страниц",
            kind=kind,
            source="metrika",
            params={
                "client": client,
                "p1_start": period.p1_start,
                "p1_end": period.p1_end,
                "p2_start": period.p2_start,
                "p2_end": period.p2_end,
                "limit": limit,
                "refresh": refresh,
                "format": "insights",
            },
            expected_artifacts=[_pages_workbook(client, period)],
        )
    if kind == "analyze_pages_by_source":
        search_source = "Search engine traffic"
        return PlannedStep(
            id=f"round-{round_number}-pages-search-source",
            title="Сравнение SEO-страниц",
            kind=kind,
            source="metrika",
            params={
                "client": client,
                "p1_start": period.p1_start,
                "p1_end": period.p1_end,
                "p2_start": period.p2_start,
                "p2_end": period.p2_end,
                "source": search_source,
                "limit": limit,
                "refresh": refresh,
                "format": "insights",
            },
            expected_artifacts=[_pages_by_source_workbook(client, period, search_source)],
        )
    if kind == "analyze_goals_by_source":
        if goal_selection.goal_id is None:
            raise RuntimeError("Goal selection is required for analyze_goals_by_source")
        goal_id = int(goal_selection.goal_id)
        return PlannedStep(
            id=f"round-{round_number}-goals-source",
            title="Сравнение конверсий по источникам",
            kind=kind,
            source="metrika",
            params={
                "client": client,
                "p1_start": period.p1_start,
                "p1_end": period.p1_end,
                "p2_start": period.p2_start,
                "p2_end": period.p2_end,
                "goal_id": goal_id,
                "limit": limit,
                "refresh": refresh,
                "format": "insights",
            },
            expected_artifacts=[
                str(Path("data_cache") / client / goals_workbook_filename("goals_by_source", goal_id, period.p1_start, period.p1_end, period.p2_start, period.p2_end))
            ],
        )
    if kind == "analyze_goals_by_page":
        if goal_selection.goal_id is None:
            raise RuntimeError("Goal selection is required for analyze_goals_by_page")
        goal_id = int(goal_selection.goal_id)
        return PlannedStep(
            id=f"round-{round_number}-goals-page",
            title="Сравнение конверсий по страницам",
            kind=kind,
            source="metrika",
            params={
                "client": client,
                "p1_start": period.p1_start,
                "p1_end": period.p1_end,
                "p2_start": period.p2_start,
                "p2_end": period.p2_end,
                "goal_id": goal_id,
                "limit": limit,
                "refresh": refresh,
                "format": "insights",
            },
            expected_artifacts=[
                str(Path("data_cache") / client / goals_workbook_filename("goals_by_page", goal_id, period.p1_start, period.p1_end, period.p2_start, period.p2_end))
            ],
        )
    if kind == "analyze_gsc_queries":
        return PlannedStep(
            id=f"round-{round_number}-gsc-queries",
            title="Сравнение GSC-запросов",
            kind=kind,
            source="gsc",
            params={
                "client": client,
                "p1_start": period.p1_start,
                "p1_end": period.p1_end,
                "p2_start": period.p2_start,
                "p2_end": period.p2_end,
                "limit": 1000,
                "refresh": refresh,
                "format": "insights",
            },
            expected_artifacts=[str(Path("data_cache") / client / gsc_workbook_filename("queries", period.p1_start, period.p1_end, period.p2_start, period.p2_end))],
        )
    if kind == "analyze_gsc_pages":
        return PlannedStep(
            id=f"round-{round_number}-gsc-pages",
            title="Сравнение GSC-страниц",
            kind=kind,
            source="gsc",
            params={
                "client": client,
                "p1_start": period.p1_start,
                "p1_end": period.p1_end,
                "p2_start": period.p2_start,
                "p2_end": period.p2_end,
                "limit": 1000,
                "refresh": refresh,
                "format": "insights",
            },
            expected_artifacts=[str(Path("data_cache") / client / gsc_workbook_filename("pages", period.p1_start, period.p1_end, period.p2_start, period.p2_end))],
        )
    if kind == "analyze_ym_webmaster_queries":
        return PlannedStep(
            id=f"round-{round_number}-ym-queries",
            title="Сравнение запросов Яндекс.Вебмастера",
            kind=kind,
            source="ym_webmaster",
            params={
                "client": client,
                "p1_start": period.p1_start,
                "p1_end": period.p1_end,
                "p2_start": period.p2_start,
                "p2_end": period.p2_end,
                "limit": 500,
                "refresh": refresh,
                "format": "insights",
            },
            expected_artifacts=[str(Path("data_cache") / client / ymw_workbook_filename(period.p1_start, period.p1_end, period.p2_start, period.p2_end))],
        )
    if kind == "ym_webmaster_indexing":
        return PlannedStep(
            id=f"round-{round_number}-ym-indexing",
            title="Снимок индексации Яндекс.Вебмастера",
            kind=kind,
            source="ym_webmaster",
            params={
                "client": client,
                "status": "EXCLUDED",
                "limit": 100,
                "offset": 0,
                "refresh": refresh,
            },
            expected_artifacts=[
                str(Path("data_cache") / client / "ym_webmaster_indexing_raw_EXCLUDED_100_0.json"),
                str(Path("data_cache") / client / "ym_webmaster_indexing_norm_EXCLUDED_100_0.json"),
            ],
        )
    raise RuntimeError(f"Unsupported investigation step kind: {kind}")


def build_initial_plan(
    client: str,
    intent: InvestigationIntent,
    period: InvestigationPeriod,
    availability: InvestigationAvailability,
    goal_selection: GoalSelection,
    refresh: bool,
    limit: int = 50,
) -> List[PlannedStep]:
    plan: List[PlannedStep] = []
    if availability.metrika:
        plan.append(_build_step(kind="analyze_sources", client=client, period=period, goal_selection=goal_selection, refresh=refresh, limit=limit, round_number=1))
        plan.append(_build_step(kind="analyze_pages", client=client, period=period, goal_selection=goal_selection, refresh=refresh, limit=limit, round_number=1))
        if intent.wants_conversions and goal_selection.goal_id is not None:
            plan.append(
                _build_step(
                    kind="analyze_goals_by_source",
                    client=client,
                    period=period,
                    goal_selection=goal_selection,
                    refresh=refresh,
                    limit=limit,
                    round_number=1,
                )
            )
    return plan


def build_followup_plan(
    *,
    client: str,
    period: InvestigationPeriod,
    availability: InvestigationAvailability,
    goal_selection: GoalSelection,
    refresh: bool,
    analysis: Dict[str, Any],
    executed_steps: List[ExecutedStep],
    round_number: int,
    limit: int = 50,
) -> List[PlannedStep]:
    executed_kinds: Set[str] = {step.kind for step in executed_steps}
    plan: List[PlannedStep] = []
    for recommendation in analysis.get("recommended_next_steps", []):
        kind = str(recommendation.get("kind", "")).strip()
        if not kind or kind in executed_kinds:
            continue
        if kind.startswith("analyze_gsc") and not availability.gsc:
            continue
        if kind.startswith("analyze_ym") and not availability.ym_webmaster:
            continue
        if kind == "ym_webmaster_indexing" and not availability.ym_webmaster:
            continue
        if kind.startswith("analyze_goal") and goal_selection.goal_id is None:
            continue
        plan.append(
            _build_step(
                kind=kind,
                client=client,
                period=period,
                goal_selection=goal_selection,
                refresh=refresh,
                limit=limit,
                round_number=round_number,
            )
        )
    return plan


def build_plan(
    client: str,
    intent: InvestigationIntent,
    period: InvestigationPeriod,
    availability: InvestigationAvailability,
    goal_selection: GoalSelection,
    refresh: bool,
    limit: int = 50,
) -> List[PlannedStep]:
    return build_initial_plan(
        client=client,
        intent=intent,
        period=period,
        availability=availability,
        goal_selection=goal_selection,
        refresh=refresh,
        limit=limit,
    )

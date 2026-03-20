from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from app.orchestrator.models import ExecutedStep, GoalSelection, InvestigationAvailability, InvestigationIntent, InvestigationPeriod


def _load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _fmt_number(value: float) -> str:
    if abs(value) >= 1000:
        return f"{value:,.0f}".replace(",", " ")
    return f"{value:.1f}"


def _direction_class(value: float) -> str:
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "neutral"


def _artifact_map(executed_steps: List[ExecutedStep]) -> Dict[str, Any]:
    artifacts: Dict[str, Any] = {}
    for step in executed_steps:
        for artifact in step.artifacts:
            if artifact.endswith(".json"):
                artifacts[artifact] = _load_json(artifact)
    return artifacts


def _first_artifact(executed_steps: List[ExecutedStep], kind: str) -> str | None:
    for step in executed_steps:
        if step.kind == kind and step.artifacts:
            return step.artifacts[0]
    return None


def _recommend(kind: str, reason: str, priority: str = "medium") -> Dict[str, str]:
    return {"kind": kind, "reason": reason, "priority": priority}


def analyze_results(
    *,
    client: str,
    query: str,
    period: InvestigationPeriod,
    intent: InvestigationIntent,
    availability: InvestigationAvailability,
    goal_selection: GoalSelection,
    executed_steps: List[ExecutedStep],
) -> Dict[str, Any]:
    artifact_payloads = _artifact_map(executed_steps)
    facts: List[Dict[str, Any]] = []
    drivers: List[Dict[str, Any]] = []
    hypotheses: List[Dict[str, Any]] = []
    recommended_next_steps: List[Dict[str, str]] = []
    availability_notes = list(availability.notes)
    executed_kinds = {step.kind for step in executed_steps if step.success}

    sources_artifact = _first_artifact(executed_steps, "analyze_sources")
    pages_artifact = _first_artifact(executed_steps, "analyze_pages")
    search_pages_artifact = _first_artifact(executed_steps, "analyze_pages_by_source")
    goals_source_artifact = _first_artifact(executed_steps, "analyze_goals_by_source")
    goals_page_artifact = _first_artifact(executed_steps, "analyze_goals_by_page")
    gsc_queries_artifact = _first_artifact(executed_steps, "analyze_gsc_queries")
    gsc_pages_artifact = _first_artifact(executed_steps, "analyze_gsc_pages")
    ymw_queries_artifact = _first_artifact(executed_steps, "analyze_ym_webmaster_queries")
    ymw_indexing_artifact = None
    for step in executed_steps:
        if step.kind == "ym_webmaster_indexing":
            for artifact in step.artifacts:
                if artifact.endswith("_norm_EXCLUDED_100_0.json"):
                    ymw_indexing_artifact = artifact
                    break

    traffic_delta = None
    search_source_row = None
    search_source_down = False
    goal_drop = False
    goal_cr_drop = False
    if sources_artifact:
        workbook = artifact_payloads[sources_artifact]
        totals = workbook["totals"]
        traffic_delta = float(totals["total_delta_abs"])
        facts.append(
            {
                "title": "Общий трафик",
                "value": f"{_fmt_number(float(totals['total_visits_p1']))} -> {_fmt_number(float(totals['total_visits_p2']))} ({_fmt_number(float(totals['total_delta_pct']))}%)",
                "evidence": sources_artifact,
            }
        )
        rows = workbook.get("rows") or []
        if rows:
            top_growth = max(rows, key=lambda row: float(row.get("delta_abs", 0.0)))
            top_decline = min(rows, key=lambda row: float(row.get("delta_abs", 0.0)))
            drivers.extend(
                [
                    {
                        "title": "Главный рост по источникам",
                        "value": f"{top_growth.get('source', '(unknown)')}: {_fmt_number(float(top_growth.get('delta_abs', 0.0)))}",
                        "evidence": sources_artifact,
                    },
                    {
                        "title": "Главное падение по источникам",
                        "value": f"{top_decline.get('source', '(unknown)')}: {_fmt_number(float(top_decline.get('delta_abs', 0.0)))}",
                        "evidence": sources_artifact,
                    },
                ]
            )
        for row in rows:
            if str(row.get("source", "")) == "Search engine traffic":
                search_source_row = row
                search_source_down = float(row.get("delta_abs", 0.0)) < 0
                break

    if pages_artifact:
        workbook = artifact_payloads[pages_artifact]
        rows = workbook.get("rows") or []
        if rows:
            worst_page = min(rows, key=lambda row: float(row.get("delta_abs", 0.0)))
            facts.append(
                {
                    "title": "Наиболее просевшая страница",
                    "value": f"{worst_page.get('landingPage', '(unknown)')}: {_fmt_number(float(worst_page.get('delta_abs', 0.0)))}",
                    "evidence": pages_artifact,
                }
            )

    if search_pages_artifact:
        workbook = artifact_payloads[search_pages_artifact]
        rows = workbook.get("rows") or []
        if rows:
            worst_search_page = min(rows, key=lambda row: float(row.get("delta_abs", 0.0)))
            facts.append(
                {
                    "title": "Просевшая SEO-страница",
                    "value": f"{worst_search_page.get('landingPage', '(unknown)')}: {_fmt_number(float(worst_search_page.get('delta_abs', 0.0)))}",
                    "evidence": search_pages_artifact,
                }
            )
            if float(worst_search_page.get("delta_abs", 0.0)) < 0:
                hypotheses.append(
                    {
                        "title": "Потеря поискового трафика на важных страницах",
                        "status": "подтверждается",
                        "confidence": "high",
                        "because": f"Сильнейшее падение у SEO-страницы {worst_search_page.get('landingPage', '(unknown)')}.",
                        "next_check": "Проверить редиректы, индексацию и изменение контента этой страницы.",
                        "evidence": [search_pages_artifact],
                    }
                )

    if gsc_queries_artifact:
        workbook = artifact_payloads[gsc_queries_artifact]
        totals = workbook["totals"]
        facts.append(
            {
                "title": "GSC clicks по запросам",
                "value": f"{_fmt_number(float(totals['total_clicks_p1']))} -> {_fmt_number(float(totals['total_clicks_p2']))} ({_fmt_number(float(totals['total_delta_pct']))}%)",
                "evidence": gsc_queries_artifact,
            }
        )
        rows = workbook.get("rows") or []
        if rows:
            worst_query = min(rows, key=lambda row: float(row.get("delta_clicks", 0.0)))
            drivers.append(
                {
                    "title": "Главный просевший запрос (GSC)",
                    "value": f"{worst_query.get('query', '(unknown)')}: {_fmt_number(float(worst_query.get('delta_clicks', 0.0)))}",
                    "evidence": gsc_queries_artifact,
                }
            )
            if float(worst_query.get("delta_position", 0.0)) > 0 or float(worst_query.get("delta_ctr_pp", 0.0)) < 0:
                hypotheses.append(
                    {
                        "title": "Просадка органики из-за ухудшения запросов",
                        "status": "подтверждается",
                        "confidence": "high",
                        "because": "По GSC просели клики, а позиции или CTR ухудшились.",
                        "next_check": "Проверить title/snippet и конкурентную выдачу по ключевым запросам.",
                        "evidence": [gsc_queries_artifact],
                    }
                )

    if gsc_pages_artifact:
        workbook = artifact_payloads[gsc_pages_artifact]
        rows = workbook.get("rows") or []
        if rows:
            worst_page = min(rows, key=lambda row: float(row.get("delta_clicks", 0.0)))
            drivers.append(
                {
                    "title": "Главная просевшая страница в GSC",
                    "value": f"{worst_page.get('page', '(unknown)')}: {_fmt_number(float(worst_page.get('delta_clicks', 0.0)))}",
                    "evidence": gsc_pages_artifact,
                }
            )

    if ymw_queries_artifact:
        workbook = artifact_payloads[ymw_queries_artifact]
        totals = workbook["totals"]
        facts.append(
            {
                "title": "Яндекс.Вебмастер clicks по запросам",
                "value": f"{_fmt_number(float(totals['total_clicks_p1']))} -> {_fmt_number(float(totals['total_clicks_p2']))} ({_fmt_number(float(totals['total_delta_pct']))}%)",
                "evidence": ymw_queries_artifact,
            }
        )

    if ymw_indexing_artifact:
        rows = artifact_payloads[ymw_indexing_artifact]
        excluded_count = len(rows) if isinstance(rows, list) else 0
        facts.append(
            {
                "title": "Снимок исключённых URL",
                "value": f"{excluded_count} URL в выборке EXCLUDED",
                "evidence": ymw_indexing_artifact,
            }
        )
        if excluded_count > 0:
            hypotheses.append(
                {
                    "title": "Есть риски по индексации",
                    "status": "частично подтверждается",
                    "confidence": "medium",
                    "because": f"В Яндекс.Вебмастере найдено {excluded_count} исключённых URL в выборке.",
                    "next_check": "Разобрать причины исключения: 404, duplicate, noindex, robots.",
                    "evidence": [ymw_indexing_artifact],
                }
            )

    if goals_source_artifact:
        workbook = artifact_payloads[goals_source_artifact]
        totals = workbook["totals"]
        goal_drop = float(totals["total_delta_goal_visits_abs"]) < 0
        goal_cr_drop = float(totals["total_delta_cr_pp"]) < 0
        facts.append(
            {
                "title": "Конверсионные визиты по источникам",
                "value": f"{_fmt_number(float(totals['total_goal_visits_p1']))} -> {_fmt_number(float(totals['total_goal_visits_p2']))} ({_fmt_number(float(totals['total_delta_goal_visits_pct']))}%)",
                "evidence": goals_source_artifact,
            }
        )
        if goal_drop and goal_cr_drop:
            hypotheses.append(
                {
                    "title": "Падение заявок из-за ухудшения качества трафика",
                    "status": "подтверждается",
                    "confidence": "high",
                    "because": "Конверсионные визиты и общий CR по источникам снизились.",
                    "next_check": "Проверить источники с самым сильным падением CR и лендинги для них.",
                    "evidence": [goals_source_artifact],
                }
            )

    if goals_page_artifact:
        workbook = artifact_payloads[goals_page_artifact]
        rows = workbook.get("rows") or []
        if rows:
            worst_goal_page = min(rows, key=lambda row: float(row.get("delta_goal_visits_abs", 0.0)))
            drivers.append(
                {
                    "title": "Главная просевшая страница по конверсиям",
                    "value": f"{worst_goal_page.get('landingPage', '(unknown)')}: {_fmt_number(float(worst_goal_page.get('delta_goal_visits_abs', 0.0)))}",
                    "evidence": goals_page_artifact,
                }
            )
            if float(worst_goal_page.get("visits_p2", 0.0)) > 0 and float(worst_goal_page.get("goal_visits_p2", 0.0)) == 0:
                hypotheses.append(
                    {
                        "title": "Проблема трекинга или формы на части страниц",
                        "status": "частично подтверждается",
                        "confidence": "medium",
                        "because": "Есть страницы с трафиком, но без конверсий в текущем периоде.",
                        "next_check": "Проверить форму, события и отправку цели на просевших страницах.",
                        "evidence": [goals_page_artifact],
                    }
                )

    if not hypotheses and search_source_row is not None and float(search_source_row.get("delta_abs", 0.0)) < 0:
        hypotheses.append(
            {
                "title": "Есть отдельная просадка по поисковому трафику",
                "status": "частично подтверждается",
                "confidence": "medium",
                "because": "Источник Search engine traffic показал отрицательную динамику.",
                "next_check": "Добавить GSC и Яндекс.Вебмастер или проверить, почему они недоступны.",
                "evidence": [sources_artifact] if sources_artifact else [],
            }
        )

    if intent.wants_conversions and goal_selection.goal_id is not None and "analyze_goals_by_source" not in executed_kinds:
        recommended_next_steps.append(
            _recommend(
                "analyze_goals_by_source",
                "Запрос связан с заявками или конверсиями, но срез по источникам ещё не собран.",
                "high",
            )
        )

    seo_signal = bool(intent.wants_seo or search_source_down or search_pages_artifact)
    if availability.metrika and seo_signal and "analyze_pages_by_source" not in executed_kinds:
        recommended_next_steps.append(
            _recommend(
                "analyze_pages_by_source",
                "Нужно проверить, какие именно страницы просели внутри поискового трафика.",
                "high",
            )
        )

    if seo_signal and availability.gsc and "analyze_gsc_queries" not in executed_kinds:
        recommended_next_steps.append(
            _recommend(
                "analyze_gsc_queries",
                "Нужна проверка поисковых запросов, чтобы понять, просели ли клики, CTR или позиции.",
                "high",
            )
        )
    if seo_signal and availability.gsc and "analyze_gsc_pages" not in executed_kinds and (
        "analyze_gsc_queries" in executed_kinds or search_pages_artifact is not None
    ):
        recommended_next_steps.append(
            _recommend(
                "analyze_gsc_pages",
                "Нужно подтвердить просадку на уровне конкретных SEO-страниц.",
                "medium",
            )
        )
    if seo_signal and availability.ym_webmaster and "analyze_ym_webmaster_queries" not in executed_kinds:
        recommended_next_steps.append(
            _recommend(
                "analyze_ym_webmaster_queries",
                "Нужен второй поисковый источник, чтобы подтвердить или опровергнуть SEO-гипотезу.",
                "medium",
            )
        )
    if (intent.wants_indexing or seo_signal) and availability.ym_webmaster and "ym_webmaster_indexing" not in executed_kinds:
        recommended_next_steps.append(
            _recommend(
                "ym_webmaster_indexing",
                "Нужно проверить индексацию и исключённые URL.",
                "medium",
            )
        )

    if (
        intent.wants_conversions
        and goal_selection.goal_id is not None
        and goals_source_artifact
        and "analyze_goals_by_page" not in executed_kinds
        and (goal_drop or goal_cr_drop)
    ):
        recommended_next_steps.append(
            _recommend(
                "analyze_goals_by_page",
                "Есть просадка по конверсиям или CR, нужно локализовать её на уровне страниц.",
                "high",
            )
        )

    missing_sources = []
    if intent.wants_seo and not availability.gsc:
        missing_sources.append("GSC")
    if intent.wants_seo and not availability.ym_webmaster:
        missing_sources.append("Яндекс.Вебмастер")
    if not availability.metrika:
        missing_sources.append("Метрика")

    if goal_selection.goal_id is None and intent.wants_conversions:
        availability_notes.append(f"Конверсионная цель не определена. {goal_selection.reason}")

    if missing_sources:
        availability_notes.append("Недоступные источники: " + ", ".join(missing_sources))

    if recommended_next_steps:
        unique_recommendations: List[Dict[str, str]] = []
        seen_kinds = set()
        for item in recommended_next_steps:
            if item["kind"] in seen_kinds:
                continue
            seen_kinds.add(item["kind"])
            unique_recommendations.append(item)
        recommended_next_steps = unique_recommendations

    summary_parts: List[str] = []
    if traffic_delta is not None:
        if traffic_delta < 0:
            summary_parts.append("общий трафик снижается")
        elif traffic_delta > 0:
            summary_parts.append("общий трафик растёт")
        else:
            summary_parts.append("общий трафик стабилен")
    if intent.wants_seo and any(h["title"].lower().startswith("просадка органики") or "поисков" in h["title"].lower() for h in hypotheses):
        summary_parts.append("есть подтверждения SEO-проблемы")
    if intent.wants_conversions and any("конвер" in h["title"].lower() or "трекинг" in h["title"].lower() for h in hypotheses):
        summary_parts.append("есть сигналы по конверсиям")

    if not summary_parts:
        summary_parts.append("расследование выполнено, но сильный корневой драйвер автоматически не выделен")

    if any(item["status"] == "подтверждается" and item["confidence"] == "high" for item in hypotheses):
        root_cause_status = "identified"
    elif hypotheses:
        root_cause_status = "partial"
    else:
        root_cause_status = "insufficient"

    return {
        "query": query,
        "client": client,
        "period": {
            "p1_start": period.p1_start,
            "p1_end": period.p1_end,
            "p2_start": period.p2_start,
            "p2_end": period.p2_end,
            "source": period.source,
            "description": period.description,
        },
        "intent": {
            "primary_focus": intent.primary_focus,
            "direction": intent.direction,
            "wants_seo": intent.wants_seo,
            "wants_conversions": intent.wants_conversions,
        },
        "goal_selection": {
            "goal_id": goal_selection.goal_id,
            "source": goal_selection.source,
            "confidence": goal_selection.confidence,
            "reason": goal_selection.reason,
            "candidates": goal_selection.candidates,
        },
        "facts": facts,
        "drivers": drivers,
        "hypotheses": hypotheses,
        "recommended_next_steps": recommended_next_steps,
        "root_cause_status": root_cause_status,
        "availability_notes": availability_notes,
        "summary": ". ".join(summary_parts).capitalize() + ".",
        "executed_steps": [
            {
                "id": step.id,
                "title": step.title,
                "kind": step.kind,
                "success": step.success,
                "exit_code": step.exit_code,
                "artifacts": step.artifacts,
                "source": step.source,
            }
            for step in executed_steps
        ],
    }

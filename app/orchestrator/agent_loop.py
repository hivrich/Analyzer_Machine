from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional

from app.config import load_client_config
from app.orchestrator.analyzer import analyze_results
from app.orchestrator.availability import inspect_availability
from app.orchestrator.date_resolution import resolve_periods
from app.orchestrator.executor import execute_plan
from app.orchestrator.goal_resolver import resolve_primary_goal
from app.orchestrator.intake import parse_intent
from app.orchestrator.models import GoalSelection, InvestigationReport
from app.orchestrator.planner import build_followup_plan, build_initial_plan
from app.orchestrator.report_generator import write_report_files


def investigate(
    *,
    client: str,
    query: str,
    refresh: bool = False,
    p1_start: Optional[str] = None,
    p1_end: Optional[str] = None,
    p2_start: Optional[str] = None,
    p2_end: Optional[str] = None,
) -> tuple[InvestigationReport, Dict[str, Any], list[Any]]:
    cfg, _ = load_client_config(client)
    intent = parse_intent(query)
    period = resolve_periods(
        query=query,
        p1_start=p1_start,
        p1_end=p1_end,
        p2_start=p2_start,
        p2_end=p2_end,
    )
    availability = inspect_availability(cfg)
    if intent.wants_conversions:
        goal_selection = resolve_primary_goal(client=client, cfg=cfg, query=query, refresh=refresh)
    else:
        goal_selection = GoalSelection(
            goal_id=None,
            source="skipped",
            confidence="n/a",
            reason="Запрос не про конверсии, подбор goal_id пропущен.",
            candidates=[],
        )
    initial_plan = build_initial_plan(
        client=client,
        intent=intent,
        period=period,
        availability=availability,
        goal_selection=goal_selection,
        refresh=refresh,
    )
    all_plans = []
    all_planned_steps = []
    executed_steps = []
    analysis: Dict[str, Any] | None = None
    loop_rounds = []
    stop_reason = ""
    next_plan = initial_plan
    max_rounds = 4

    for round_number in range(1, max_rounds + 1):
        if not next_plan:
            stop_reason = "Новых полезных шагов больше нет."
            break

        all_plans.append({"round": round_number, "steps": [asdict(step) for step in next_plan]})
        all_planned_steps.extend(next_plan)
        round_executions = execute_plan(next_plan)
        executed_steps.extend(round_executions)

        successful_steps = [step for step in executed_steps if step.success and step.artifacts]
        if not successful_steps:
            stop_reason = "Не удалось получить usable artifacts."
            break

        analysis = analyze_results(
            client=client,
            query=query,
            period=period,
            intent=intent,
            availability=availability,
            goal_selection=goal_selection,
            executed_steps=executed_steps,
        )
        loop_rounds.append(
            {
                "round": round_number,
                "planned_steps": [asdict(step) for step in next_plan],
                "executed_steps": [
                    {
                        "id": step.id,
                        "kind": step.kind,
                        "success": step.success,
                        "artifacts": step.artifacts,
                    }
                    for step in round_executions
                ],
                "summary": analysis["summary"],
                "root_cause_status": analysis.get("root_cause_status"),
                "recommended_next_steps": analysis.get("recommended_next_steps", []),
            }
        )

        next_plan = build_followup_plan(
            client=client,
            period=period,
            availability=availability,
            goal_selection=goal_selection,
            refresh=refresh,
            analysis=analysis,
            executed_steps=executed_steps,
            round_number=round_number + 1,
        )
        if analysis.get("root_cause_status") == "identified" and not next_plan:
            stop_reason = "Найдена достаточно уверенная причина, дополнительных шагов не требуется."
            break
        if not next_plan:
            stop_reason = "После очередной проверки новые полезные шаги не появились."
            break
    else:
        stop_reason = f"Достигнут лимит в {max_rounds} раунда расследования."

    successful_steps = [step for step in executed_steps if step.success and step.artifacts]
    if not successful_steps:
        analysis = {
            "query": query,
            "client": client,
            "period": asdict(period),
            "intent": {
                "primary_focus": intent.primary_focus,
                "direction": intent.direction,
                "wants_seo": intent.wants_seo,
                "wants_conversions": intent.wants_conversions,
            },
            "goal_selection": asdict(goal_selection),
            "facts": [],
            "drivers": [],
            "hypotheses": [],
            "recommended_next_steps": [],
            "root_cause_status": "insufficient",
            "availability_notes": availability.notes + ["Не удалось получить ни одного usable artifact."],
            "summary": "Расследование не дало usable artifacts.",
            "loop": {
                "mode": "iterative",
                "rounds": loop_rounds,
                "stop_reason": stop_reason or "Не удалось получить usable artifacts.",
                "max_rounds": max_rounds,
            },
            "executed_steps": [
                {
                    "id": step.id,
                    "title": step.title,
                    "kind": step.kind,
                    "success": step.success,
                    "exit_code": step.exit_code,
                    "artifacts": step.artifacts,
                    "source": step.source,
                    "stdout": step.stdout,
                    "stderr": step.stderr,
                }
                for step in executed_steps
            ],
        }
    else:
        assert analysis is not None
        analysis["loop"] = {
            "mode": "iterative",
            "rounds": loop_rounds,
            "stop_reason": stop_reason or "Расследование завершено.",
            "max_rounds": max_rounds,
        }

    evidence = {
        "client": client,
        "query": query,
        "refresh": refresh,
        "period": asdict(period),
        "intent": asdict(intent),
        "availability": asdict(availability),
        "goal_selection": asdict(goal_selection),
        "plan": [asdict(step) for step in all_planned_steps],
        "plans_by_round": all_plans,
        "executions": [
            {
                **asdict(step),
                "stdout": step.stdout,
                "stderr": step.stderr,
            }
            for step in executed_steps
        ],
        "analysis": analysis,
    }
    report = write_report_files(client=client, analysis=analysis, evidence=evidence)
    return report, analysis, executed_steps

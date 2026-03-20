from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from app.config import ClientConfig
from app.metrika_client import MetrikaClient, normalize_goals_list
from app.orchestrator.models import GoalSelection


def _score_goal(goal: Dict[str, Any], query: str) -> int:
    name = str(goal.get("name", "")).lower()
    goal_type = str(goal.get("type", "")).lower()
    lowered = query.lower()

    if goal_type == "e_purchase":
        return 200

    high_patterns = [
        "заяв",
        "форм",
        "contact_data",
        "contact data",
        "contact",
        "лид",
        "отправ",
        "action",
    ]
    medium_patterns = [
        "регистрац",
        "registration",
        "signup",
        "purchase",
        "оплат",
        "заказ",
        "cart",
        "checkout",
    ]

    score = 0
    if any(pattern in name or pattern in goal_type for pattern in high_patterns):
        score = max(score, 120)
    if any(pattern in name or pattern in goal_type for pattern in medium_patterns):
        score = max(score, 90)

    if any(token in lowered for token in ["покуп", "продаж", "оплат", "заказ", "revenue"]):
        if "purchase" in name or goal_type == "e_purchase" or "checkout" in name:
            score = max(score, 180)
    if any(token in lowered for token in ["регистрац", "signup", "регистрация"]) and "регистра" in name:
        score = max(score, 130)
    if any(token in lowered for token in ["заяв", "лид", "форм", "конверс"]) and (
        any(pattern in name for pattern in ["заяв", "форм", "contact", "отправ", "lead"]) or goal_type in {"form", "contact_data", "contact_data_sent", "action"}
    ):
        score = max(score, 150)

    return score


def _load_cached_goals(client: str) -> List[Dict[str, Any]] | None:
    path = Path("data_cache") / client / "metrika_goals_list_norm.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, list) else None


def _fetch_goals(client: str, cfg: ClientConfig) -> List[Dict[str, Any]] | None:
    token = os.getenv("YANDEX_METRIKA_TOKEN", "").strip()
    if not token or int(cfg.counter_id or 0) <= 0:
        return None

    metrika = MetrikaClient(token=token, counter_id=int(cfg.counter_id))
    raw = metrika.list_goals()
    normalized = normalize_goals_list(raw)

    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "metrika_goals_list_raw.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (cache_dir / "metrika_goals_list_norm.json").write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return normalized


def resolve_primary_goal(client: str, cfg: ClientConfig, query: str, refresh: bool = False) -> GoalSelection:
    if int(cfg.goal_id or 0) > 0:
        return GoalSelection(
            goal_id=int(cfg.goal_id),
            source="config",
            confidence="high",
            reason="goal_id задан в config.yaml",
            candidates=[],
        )

    goals = None
    if not refresh:
        goals = _load_cached_goals(client)
    if goals is None:
        goals = _fetch_goals(client, cfg)

    if not goals:
        return GoalSelection(
            goal_id=None,
            source="none",
            confidence="low",
            reason="Не удалось получить список целей Метрики.",
            candidates=[],
        )

    ranked = sorted(
        (
            {
                "id": int(goal.get("id", 0) or 0),
                "name": str(goal.get("name", "")),
                "type": str(goal.get("type", "")),
                "score": _score_goal(goal, query),
            }
            for goal in goals
        ),
        key=lambda item: (-item["score"], item["id"]),
    )

    top = ranked[0] if ranked else None
    if not top or int(top["score"]) < 90:
        return GoalSelection(
            goal_id=None,
            source="auto",
            confidence="low",
            reason="Не удалось уверенно выбрать основную цель автоматически.",
            candidates=ranked[:5],
        )

    confidence = "high" if int(top["score"]) >= 150 else "medium"
    return GoalSelection(
        goal_id=int(top["id"]),
        source="auto",
        confidence=confidence,
        reason=f"Автоматически выбрана цель '{top['name']}' ({top['type']}).",
        candidates=ranked[:5],
    )

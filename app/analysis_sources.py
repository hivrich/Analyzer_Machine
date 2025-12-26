from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from app.metrika_client import MetrikaClient, normalize_sources


def load_or_fetch_sources(
    client: str,
    date1: str,
    date2: str,
    limit: int,
    refresh: bool,
    metrika_client: MetrikaClient,
) -> List[Dict[str, Any]]:
    """
    Загружает данные источников трафика из кэша или запрашивает API.
    
    Returns:
        Нормализованные данные источников
    """
    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    norm_file = cache_dir / f"metrika_sources_norm_{date1}_{date2}.json"
    
    # Проверяем кэш
    if not refresh and norm_file.exists():
        return json.loads(norm_file.read_text(encoding="utf-8"))
    
    # Запрашиваем API
    raw_data = metrika_client.traffic_sources(date1, date2, limit)
    normalized_data = normalize_sources(raw_data)
    
    # Сохраняем в кэш
    raw_file = cache_dir / f"metrika_sources_raw_{date1}_{date2}.json"
    raw_file.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2), encoding="utf-8")
    norm_file.write_text(json.dumps(normalized_data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    return normalized_data


def compare_sources_periods(
    data_p1: List[Dict[str, Any]],
    data_p2: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Сравнивает источники трафика между двумя периодами.
    
    Args:
        data_p1: Нормализованные данные периода 1
        data_p2: Нормализованные данные периода 2
    
    Returns:
        Список строк сравнения с полями: source, visits_p1, visits_p2, delta_abs, delta_pct
    """
    # Создаём словари по источникам для быстрого доступа
    sources_p1 = {row["source"]: row["visits"] for row in data_p1}
    sources_p2 = {row["source"]: row["visits"] for row in data_p2}
    
    # Объединяем все уникальные источники
    all_sources = set(sources_p1.keys()) | set(sources_p2.keys())
    
    rows = []
    for source in all_sources:
        visits_p1 = sources_p1.get(source, 0.0)
        visits_p2 = sources_p2.get(source, 0.0)
        
        delta_abs = visits_p2 - visits_p1
        delta_pct = (delta_abs / max(visits_p1, 1.0)) * 100.0
        
        rows.append({
            "source": source,
            "visits_p1": visits_p1,
            "visits_p2": visits_p2,
            "delta_abs": delta_abs,
            "delta_pct": delta_pct,
        })
    
    return rows


def calculate_contributions(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Рассчитывает вклады источников в общее изменение.
    
    Args:
        rows: Список строк с delta_abs
    
    Returns:
        Список строк с добавленным полем contribution_pct
    """
    total_delta_abs_sum = sum(row["delta_abs"] for row in rows)
    
    if total_delta_abs_sum == 0:
        for row in rows:
            row["contribution_pct"] = 0.0
    else:
        for row in rows:
            row["contribution_pct"] = (row["delta_abs"] / total_delta_abs_sum) * 100.0
    
    return rows


def sort_analysis_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Сортирует строки анализа: по убыванию abs(delta_abs), затем по source (asc).
    """
    return sorted(rows, key=lambda x: (-abs(x["delta_abs"]), x["source"]))


def create_workbook(
    client: str,
    counter_id: int,
    p1_start: str,
    p1_end: str,
    p2_start: str,
    p2_end: str,
    limit: int,
    refresh_used: bool,
    rows: List[Dict[str, Any]],
    all_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Создаёт структуру workbook для сохранения.
    
    Args:
        all_rows: Все строки (до top-N ограничения) для расчёта totals
        rows: Топ-N строк после сортировки
    """
    total_visits_p1 = sum(row["visits_p1"] for row in all_rows)
    total_visits_p2 = sum(row["visits_p2"] for row in all_rows)
    total_delta_abs = total_visits_p2 - total_visits_p1
    total_delta_pct = (total_delta_abs / max(total_visits_p1, 1.0)) * 100.0
    
    return {
        "meta": {
            "client": client,
            "counter_id": counter_id,
            "p1_start": p1_start,
            "p1_end": p1_end,
            "p2_start": p2_start,
            "p2_end": p2_end,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "limit": limit,
            "refresh_used": refresh_used,
        },
        "totals": {
            "total_visits_p1": total_visits_p1,
            "total_visits_p2": total_visits_p2,
            "total_delta_abs": total_delta_abs,
            "total_delta_pct": total_delta_pct,
        },
        "rows": rows[:limit] if limit > 0 else rows,
    }


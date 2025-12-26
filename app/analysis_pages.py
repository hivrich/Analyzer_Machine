from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from app.metrika_client import MetrikaClient, normalize_pages


def load_or_fetch_pages(
    client: str,
    date1: str,
    date2: str,
    limit: int,
    refresh: bool,
    metrika_client: MetrikaClient,
) -> List[Dict[str, Any]]:
    """
    Загружает данные входных страниц (landing pages) из кэша или запрашивает API.

    Returns:
        Нормализованные данные входных страниц
    """
    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)

    norm_file = cache_dir / f"metrika_pages_norm_{date1}_{date2}.json"

    # Проверяем кэш
    if not refresh and norm_file.exists():
        return json.loads(norm_file.read_text(encoding="utf-8"))

    # Запрашиваем API
    raw_data = metrika_client.landing_pages(date1, date2, limit)
    normalized_data = normalize_pages(raw_data)

    # Сохраняем в кэш
    raw_file = cache_dir / f"metrika_pages_raw_{date1}_{date2}.json"
    raw_file.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2), encoding="utf-8")
    norm_file.write_text(json.dumps(normalized_data, ensure_ascii=False, indent=2), encoding="utf-8")

    return normalized_data


def _slugify_for_filename(value: str) -> str:
    """
    Делает безопасный slug для имени файла (ascii/цифры/подчёркивания).
    """
    v = (value or "").strip().lower()
    v = re.sub(r"[^a-z0-9]+", "_", v)
    v = re.sub(r"_+", "_", v).strip("_")
    return v or "unknown"


def load_or_fetch_pages_by_source(
    client: str,
    date1: str,
    date2: str,
    source: str,
    limit: int,
    refresh: bool,
    metrika_client: MetrikaClient,
) -> List[Dict[str, Any]]:
    """
    Загружает данные входных страниц (landing pages) из кэша или запрашивает API
    с фильтром по источнику трафика (ym:s:lastTrafficSource).

    Важно: для корректных вкладов стараемся запросить больше строк, чем печатаем.
    """
    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)

    source_slug = _slugify_for_filename(source)
    raw_file = cache_dir / f"metrika_pages_by_source_raw_{source_slug}_{date1}_{date2}.json"
    norm_file = cache_dir / f"metrika_pages_by_source_norm_{source_slug}_{date1}_{date2}.json"

    # Для анализа вкладов лучше иметь большой срез (но без дополнительных API вызовов).
    fetch_limit = max(5000, int(limit) if limit and limit > 0 else 0)

    # Проверяем кэш (если он достаточный по размеру)
    if not refresh and norm_file.exists():
        try:
            cached = json.loads(norm_file.read_text(encoding="utf-8"))
            if isinstance(cached, list) and len(cached) >= max(1, fetch_limit):
                return cached
        except Exception:
            pass

    raw_data = metrika_client.landing_pages_by_source(date1, date2, source, fetch_limit)
    normalized_data = normalize_pages(raw_data)

    raw_file.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2), encoding="utf-8")
    norm_file.write_text(json.dumps(normalized_data, ensure_ascii=False, indent=2), encoding="utf-8")

    return normalized_data


def compare_pages_periods(
    data_p1: List[Dict[str, Any]],
    data_p2: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Сравнивает входные страницы между двумя периодами.

    Returns:
        Список строк сравнения с полями:
        landingPage, visits_p1, visits_p2, delta_abs, delta_pct
    """
    pages_p1 = {row["landingPage"]: row["visits"] for row in data_p1}
    pages_p2 = {row["landingPage"]: row["visits"] for row in data_p2}

    all_pages = set(pages_p1.keys()) | set(pages_p2.keys())

    rows: List[Dict[str, Any]] = []
    for lp in all_pages:
        visits_p1 = pages_p1.get(lp, 0.0)
        visits_p2 = pages_p2.get(lp, 0.0)

        delta_abs = visits_p2 - visits_p1
        delta_pct = (delta_abs / max(visits_p1, 1.0)) * 100.0

        rows.append(
            {
                "landingPage": lp,
                "visits_p1": visits_p1,
                "visits_p2": visits_p2,
                "delta_abs": delta_abs,
                "delta_pct": delta_pct,
            }
        )

    return rows


def calculate_contributions(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Рассчитывает вклады строк в общее изменение (по visits).
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
    Сортирует строки анализа: по убыванию abs(delta_abs), затем по landingPage (asc).
    """
    return sorted(rows, key=lambda x: (-abs(x["delta_abs"]), x["landingPage"]))


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

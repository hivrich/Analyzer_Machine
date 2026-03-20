from __future__ import annotations

from app.orchestrator.models import InvestigationIntent


def parse_intent(query: str) -> InvestigationIntent:
    lowered = query.lower()

    seo_markers = [
        "seo",
        "органик",
        "органичес",
        "поиск",
        "gsc",
        "search console",
        "вебмастер",
        "индексац",
        "позици",
        "ctr",
        "запрос",
    ]
    conversion_markers = [
        "конверс",
        "заяв",
        "лид",
        "goal",
        "цель",
        "покуп",
        "продаж",
        "cr",
        "форм",
        "регистрац",
    ]
    page_markers = ["страниц", "page", "landing", "лендинг", "входн"]
    traffic_markers = ["трафик", "посещ", "источник", "канал", "traffic"]
    indexing_markers = ["индексац", "excluded", "robots", "404", "noindex"]

    wants_seo = any(marker in lowered for marker in seo_markers)
    wants_conversions = any(marker in lowered for marker in conversion_markers)
    wants_pages = wants_seo or any(marker in lowered for marker in page_markers)
    wants_traffic = True if not lowered.strip() else wants_seo or any(marker in lowered for marker in traffic_markers) or wants_conversions
    wants_indexing = wants_seo or any(marker in lowered for marker in indexing_markers)

    direction = "unknown"
    if any(token in lowered for token in ["упал", "упали", "падени", "сниз", "просел", "потер"]):
        direction = "down"
    elif any(token in lowered for token in ["рост", "вырос", "выросли", "увелич", "поднял"]):
        direction = "up"

    primary_focus = "traffic"
    if wants_seo:
        primary_focus = "seo"
    elif wants_conversions:
        primary_focus = "conversions"
    elif wants_pages:
        primary_focus = "pages"

    return InvestigationIntent(
        query=query,
        wants_traffic=wants_traffic,
        wants_pages=wants_pages,
        wants_conversions=wants_conversions,
        wants_seo=wants_seo,
        wants_indexing=wants_indexing,
        wants_report=True,
        wants_deep=True,
        direction=direction,
        primary_focus=primary_focus,
        period_note="auto-resolved",
    )

from __future__ import annotations

import os

from app.config import ClientConfig
from app.orchestrator.models import InvestigationAvailability


def inspect_availability(cfg: ClientConfig) -> InvestigationAvailability:
    notes: list[str] = []

    metrika = bool(os.getenv("YANDEX_METRIKA_TOKEN", "").strip()) and int(cfg.counter_id or 0) > 0
    if not metrika:
        notes.append("Метрика недоступна: нет токена или counter_id.")

    gsc = (
        bool(str(cfg.gsc_site_url or "").strip())
        and bool(os.getenv("GSC_CLIENT_ID", "").strip())
        and bool(os.getenv("GSC_CLIENT_SECRET", "").strip())
        and bool(os.getenv("GSC_REFRESH_TOKEN", "").strip())
    )
    if not gsc:
        notes.append("GSC недоступен: нет site_url или OAuth переменных.")

    ym_webmaster = (
        bool(str(cfg.ym_webmaster_user_id or "").strip())
        and bool(str(cfg.ym_webmaster_host_id or "").strip())
        and bool(
            os.getenv("YM_WEBMASTER_TOKEN", "").strip()
            or os.getenv("YANDEX_WEBMASTER_TOKEN", "").strip()
        )
    )
    if not ym_webmaster:
        notes.append("Яндекс.Вебмастер недоступен: нет user_id/host_id или токена.")

    return InvestigationAvailability(
        metrika=metrika,
        gsc=gsc,
        ym_webmaster=ym_webmaster,
        notes=notes,
    )

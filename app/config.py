from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml

CLIENTS_DIR = Path("clients")


@dataclass(frozen=True)
class ClientConfig:
    client_name: str
    site_name: str
    timezone: str
    counter_id: int
    goal_id: int
    currency: str
    llm_enabled: bool
    language: str


def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid YAML (expected mapping): {path}")
    return raw


def load_client_config(client_name: str) -> Tuple[ClientConfig, Path]:
    cfg_path = CLIENTS_DIR / client_name / "config.yaml"
    raw = _read_yaml(cfg_path)

    site = raw.get("site") or {}
    metrika = raw.get("metrika") or {}
    reporting = raw.get("reporting") or {}

    site_name = str(site.get("name", "")).strip()
    timezone = str(site.get("timezone", "Europe/Zurich")).strip()

    counter_id = int(metrika.get("counter_id", 0) or 0)
    goal_id = int(metrika.get("goal_id", 0) or 0)
    currency = str(metrika.get("currency", "RUB")).strip()

    llm_enabled = bool(reporting.get("llm_enabled", True))
    language = str(reporting.get("language", "ru")).strip()

    cfg = ClientConfig(
        client_name=client_name,
        site_name=site_name,
        timezone=timezone,
        counter_id=counter_id,
        goal_id=goal_id,
        currency=currency,
        llm_enabled=llm_enabled,
        language=language,
    )
    return cfg, cfg_path


def list_clients() -> list[str]:
    if not CLIENTS_DIR.exists():
        return []
    out: list[str] = []
    for p in CLIENTS_DIR.iterdir():
        if p.is_dir() and not p.name.startswith("_"):
            out.append(p.name)
    return sorted(out)

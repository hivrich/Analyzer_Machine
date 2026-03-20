import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from app.cli import app
from app.metrika_client import MetrikaClient


runner = CliRunner()


def _write_client_config(base_dir: Path, client: str = "demo", goal_id: int = 777) -> None:
    client_dir = base_dir / "clients" / client
    client_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "site": {
            "name": "example.com",
            "timezone": "Europe/Moscow",
        },
        "metrika": {
            "counter_id": 123456,
            "goal_id": goal_id,
            "currency": "RUB",
        },
    }
    (client_dir / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")


def _sources_payload(search_visits: int, direct_visits: int) -> dict:
    return {
        "data": [
            {
                "dimensions": [{"name": "Search engine traffic"}],
                "metrics": [search_visits, search_visits * 0.8, 30.0, 2.5, 60.0],
            },
            {
                "dimensions": [{"name": "Direct traffic"}],
                "metrics": [direct_visits, direct_visits * 0.7, 25.0, 2.0, 45.0],
            },
        ]
    }


def _pages_payload(home_visits: int, pricing_visits: int) -> dict:
    return {
        "data": [
            {
                "dimensions": [{"name": "/"}],
                "metrics": [home_visits, home_visits * 0.8, 28.0, 2.8, 75.0],
            },
            {
                "dimensions": [{"name": "/pricing"}],
                "metrics": [pricing_visits, pricing_visits * 0.7, 32.0, 2.1, 55.0],
            },
        ]
    }


def _goals_by_source_payload(search_visits: int, search_goals: int, direct_visits: int, direct_goals: int) -> dict:
    return {
        "data": [
            {
                "dimensions": [{"name": "Search engine traffic"}],
                "metrics": [
                    search_visits,
                    search_goals,
                    (search_goals / max(search_visits, 1)) * 100.0,
                ],
            },
            {
                "dimensions": [{"name": "Direct traffic"}],
                "metrics": [
                    direct_visits,
                    direct_goals,
                    (direct_goals / max(direct_visits, 1)) * 100.0,
                ],
            },
        ]
    }


def test_operator_pipeline_for_metrika_workflow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("YANDEX_METRIKA_TOKEN", "test-token")
    _write_client_config(tmp_path)

    sources_by_period = {
        ("2024-01-01", "2024-01-31"): _sources_payload(100, 40),
        ("2025-01-01", "2025-01-31"): _sources_payload(130, 20),
    }
    pages_by_period = {
        ("2024-01-01", "2024-01-31"): _pages_payload(80, 20),
        ("2025-01-01", "2025-01-31"): _pages_payload(120, 10),
    }
    goals_by_period = {
        ("2024-01-01", "2024-01-31", 777): _goals_by_source_payload(100, 10, 40, 4),
        ("2025-01-01", "2025-01-31", 777): _goals_by_source_payload(130, 18, 20, 1),
    }

    monkeypatch.setattr(
        MetrikaClient,
        "traffic_sources",
        lambda self, date1, date2, limit=50: sources_by_period[(date1, date2)],
    )
    monkeypatch.setattr(
        MetrikaClient,
        "landing_pages",
        lambda self, date1, date2, limit=50: pages_by_period[(date1, date2)],
    )
    monkeypatch.setattr(
        MetrikaClient,
        "goals_by_source",
        lambda self, date1, date2, goal_id, limit=50: goals_by_period[(date1, date2, goal_id)],
    )

    validate = runner.invoke(app, ["validate", "demo"])
    assert validate.exit_code == 0, validate.stdout

    analyze_sources = runner.invoke(
        app,
        [
            "analyze-sources",
            "demo",
            "2024-01-01",
            "2024-01-31",
            "2025-01-01",
            "2025-01-31",
            "--format",
            "insights",
        ],
    )
    assert analyze_sources.exit_code == 0, analyze_sources.stdout
    assert "Insights: visits by source" in analyze_sources.stdout

    analyze_pages = runner.invoke(
        app,
        [
            "analyze-pages",
            "demo",
            "2024-01-01",
            "2024-01-31",
            "2025-01-01",
            "2025-01-31",
            "--format",
            "insights",
        ],
    )
    assert analyze_pages.exit_code == 0, analyze_pages.stdout
    assert "Insights: visits by landingPage" in analyze_pages.stdout

    analyze_goals = runner.invoke(
        app,
        [
            "analyze-goals-by-source",
            "demo",
            "2024-01-01",
            "2024-01-31",
            "2025-01-01",
            "2025-01-31",
            "--format",
            "insights",
        ],
    )
    assert analyze_goals.exit_code == 0, analyze_goals.stdout
    assert "Insights: goal_visits by source" in analyze_goals.stdout

    cache_dir = tmp_path / "data_cache" / "demo"
    sources_workbook = cache_dir / "analysis_sources_2024010120240131__2025010120250131.json"
    pages_workbook = cache_dir / "analysis_pages_2024010120240131__2025010120250131.json"
    goals_workbook = cache_dir / "analysis_goals_by_source_777_2024010120240131__2025010120250131.json"

    assert sources_workbook.exists()
    assert pages_workbook.exists()
    assert goals_workbook.exists()

    sources_payload = json.loads(sources_workbook.read_text(encoding="utf-8"))
    assert sources_payload["totals"]["total_visits_p1"] == 140.0
    assert sources_payload["totals"]["total_visits_p2"] == 150.0
    assert sources_payload["totals"]["total_delta_abs"] == 10.0

    audit_data = runner.invoke(app, ["audit-data", "demo", "2024-01-01", "2024-01-31"])
    assert audit_data.exit_code == 0, audit_data.stdout

    audit_metric = runner.invoke(
        app,
        [
            "audit-metric",
            "total_visits_p2=150",
            "--source",
            sources_workbook.name,
            "--client",
            "demo",
            "--period",
            "P2",
        ],
    )
    assert audit_metric.exit_code == 0, audit_metric.stdout


def test_pipeline_reuses_cached_goals_workbook_without_refresh(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("YANDEX_METRIKA_TOKEN", "test-token")
    _write_client_config(tmp_path)

    monkeypatch.setattr(
        MetrikaClient,
        "goals_by_source",
        lambda self, date1, date2, goal_id, limit=50: _goals_by_source_payload(100, 10, 30, 3)
        if date1 == "2024-01-01"
        else _goals_by_source_payload(110, 13, 20, 2),
    )

    first_run = runner.invoke(
        app,
        [
            "analyze-goals-by-source",
            "demo",
            "2024-01-01",
            "2024-01-31",
            "2025-01-01",
            "2025-01-31",
            "--limit",
            "2",
            "--format",
            "insights",
        ],
    )
    assert first_run.exit_code == 0, first_run.stdout

    def fail_if_called(self, date1, date2, goal_id, limit=50):
        raise AssertionError("goals_by_source should not be called when cache is available")

    monkeypatch.setattr(MetrikaClient, "goals_by_source", fail_if_called)

    second_run = runner.invoke(
        app,
        [
            "analyze-goals-by-source",
            "demo",
            "2024-01-01",
            "2024-01-31",
            "2025-01-01",
            "2025-01-31",
            "--limit",
            "2",
            "--format",
            "insights",
        ],
    )
    assert second_run.exit_code == 0, second_run.stdout
    assert "Workbook сохранён" in second_run.stdout

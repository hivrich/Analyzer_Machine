import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from app.cli import app
from app.gsc_client import GSCClient
from app.metrika_client import MetrikaClient
from app.ym_webmaster_client import YMWebmasterClient


runner = CliRunner()


def _write_client(
    base_dir: Path,
    client: str = "demo",
    *,
    counter_id: int = 123456,
    goal_id: int = 0,
    with_gsc: bool = True,
    with_ym: bool = True,
) -> None:
    config = {
        "site": {"name": "example.com", "timezone": "Europe/Moscow"},
        "metrika": {"counter_id": counter_id, "goal_id": goal_id, "currency": "RUB"},
        "reporting": {"llm_enabled": True, "language": "ru"},
    }
    if with_gsc:
        config["gsc"] = {"site_url": "https://example.com/"}
    if with_ym:
        config["ym_webmaster"] = {"user_id": "42", "host_id": "https:example.com:443"}
    client_dir = base_dir / "clients" / client
    client_dir.mkdir(parents=True, exist_ok=True)
    (client_dir / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")


def _sources_payload(search_visits: int, direct_visits: int) -> dict:
    return {
        "data": [
            {"dimensions": [{"name": "Search engine traffic"}], "metrics": [search_visits, 0, 0, 0, 0]},
            {"dimensions": [{"name": "Direct traffic"}], "metrics": [direct_visits, 0, 0, 0, 0]},
        ]
    }


def _pages_payload(home_visits: int, blog_visits: int) -> dict:
    return {
        "data": [
            {"dimensions": [{"name": "https://example.com/"}], "metrics": [home_visits, 0, 0, 0, 0]},
            {"dimensions": [{"name": "https://example.com/blog"}], "metrics": [blog_visits, 0, 0, 0, 0]},
        ]
    }


def _goals_payload(a_visits: int, a_goals: int, b_visits: int, b_goals: int) -> dict:
    return {
        "data": [
            {"dimensions": [{"name": "Search engine traffic"}], "metrics": [a_visits, a_goals, (a_goals / max(a_visits, 1)) * 100]},
            {"dimensions": [{"name": "Direct traffic"}], "metrics": [b_visits, b_goals, (b_goals / max(b_visits, 1)) * 100]},
        ]
    }


def _gsc_rows(query_name: str, clicks: int, impressions: int, ctr: float, position: float) -> dict:
    return {"rows": [{"keys": [query_name], "clicks": clicks, "impressions": impressions, "ctr": ctr, "position": position}]}


def _gsc_pages(page_name: str, clicks: int, impressions: int, ctr: float, position: float) -> dict:
    return {"rows": [{"keys": [page_name], "clicks": clicks, "impressions": impressions, "ctr": ctr, "position": position}]}


def _ym_queries(query_name: str, clicks: int, shows: int, position: float) -> dict:
    return {"queries": [{"query_text": query_name, "indicators": {"TOTAL_SHOWS": shows, "TOTAL_CLICKS": clicks, "AVG_SHOW_POSITION": position}}]}


def test_investigate_generates_reports_for_metrika_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("YANDEX_METRIKA_TOKEN", "token")
    _write_client(tmp_path, with_gsc=False, with_ym=False)

    monkeypatch.setattr(
        MetrikaClient,
        "traffic_sources",
        lambda self, date1, date2, limit=50: _sources_payload(100, 50) if date1 == "2024-01-01" else _sources_payload(70, 60),
    )
    monkeypatch.setattr(
        MetrikaClient,
        "landing_pages",
        lambda self, date1, date2, limit=50: _pages_payload(80, 20) if date1 == "2024-01-01" else _pages_payload(50, 10),
    )

    result = runner.invoke(
        app,
        [
            "investigate",
            "demo",
            "--query",
            "Разберись, почему упал трафик 2024-01-01 2024-01-31 2025-01-01 2025-01-31",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Итог:" in result.stdout
    assert "Markdown:" in result.stdout

    reports_root = tmp_path / "reports" / "demo"
    run_dirs = [item for item in reports_root.iterdir() if item.is_dir()]
    assert len(run_dirs) == 1
    report_dir = run_dirs[0]
    assert (report_dir / "report.md").exists()
    assert (report_dir / "report.html").exists()
    assert (report_dir / "evidence.json").exists()

    evidence = json.loads((report_dir / "evidence.json").read_text(encoding="utf-8"))
    assert evidence["analysis"]["availability_notes"]
    assert any("GSC недоступен" in note for note in evidence["analysis"]["availability_notes"])


def test_investigate_runs_seo_sources_when_available(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("YANDEX_METRIKA_TOKEN", "token")
    monkeypatch.setenv("GSC_CLIENT_ID", "cid")
    monkeypatch.setenv("GSC_CLIENT_SECRET", "secret")
    monkeypatch.setenv("GSC_REFRESH_TOKEN", "refresh")
    monkeypatch.setenv("YM_WEBMASTER_TOKEN", "ym-token")
    _write_client(tmp_path, with_gsc=True, with_ym=True)

    monkeypatch.setattr(
        MetrikaClient,
        "traffic_sources",
        lambda self, date1, date2, limit=50: _sources_payload(100, 30) if date1 == "2024-01-01" else _sources_payload(60, 40),
    )
    monkeypatch.setattr(
        MetrikaClient,
        "landing_pages",
        lambda self, date1, date2, limit=50: _pages_payload(70, 30) if date1 == "2024-01-01" else _pages_payload(40, 20),
    )
    monkeypatch.setattr(
        MetrikaClient,
        "landing_pages_by_source",
        lambda self, date1, date2, source, limit=50: _pages_payload(60, 10) if date1 == "2024-01-01" else _pages_payload(30, 5),
    )
    monkeypatch.setattr(
        GSCClient,
        "search_analytics",
        lambda self, date1, date2, dimensions, row_limit=1000, start_row=0, dimension_filter_groups=None, data_state="final": _gsc_rows("seo курс", 100, 1000, 0.10, 3.0)
        if dimensions == ["query"] and date1 == "2024-01-01"
        else _gsc_rows("seo курс", 50, 900, 0.07, 8.0)
        if dimensions == ["query"]
        else _gsc_pages("https://example.com/seo", 80, 500, 0.16, 2.5)
        if date1 == "2024-01-01"
        else _gsc_pages("https://example.com/seo", 20, 350, 0.05, 9.0),
    )
    monkeypatch.setattr(
        YMWebmasterClient,
        "popular_queries",
        lambda self, date_from, date_to, limit=500, offset=0, device_type_indicator="ALL": _ym_queries("seo курс", 90, 1500, 4.0)
        if date_from == "2024-01-01"
        else _ym_queries("seo курс", 30, 900, 9.0),
    )
    monkeypatch.setattr(
        YMWebmasterClient,
        "indexing_samples",
        lambda self, search_url_status="EXCLUDED", limit=100, offset=0: {
            "samples": [
                {"url": "https://example.com/old-page", "search_url_status": "EXCLUDED", "http_code": 404, "reason": "HTTP_404"}
            ]
        },
    )

    result = runner.invoke(
        app,
        [
            "investigate",
            "demo",
            "--query",
            "Разберись, почему упала органика 2024-01-01 2024-01-31 2025-01-01 2025-01-31",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Гипотезы:" in result.stdout

    report_dir = next((tmp_path / "reports" / "demo").iterdir())
    evidence = json.loads((report_dir / "evidence.json").read_text(encoding="utf-8"))
    kinds = {step["kind"] for step in evidence["analysis"]["executed_steps"]}
    assert "analyze_gsc_queries" in kinds
    assert "analyze_ym_webmaster_queries" in kinds
    assert "ym_webmaster_indexing" in kinds
    assert any("SEO" in hypothesis["title"] or "органики" in hypothesis["title"].lower() or "поисков" in hypothesis["title"].lower() for hypothesis in evidence["analysis"]["hypotheses"])
    rounds = evidence["analysis"]["loop"]["rounds"]
    assert len(rounds) >= 2
    round1_kinds = {step["kind"] for step in rounds[0]["planned_steps"]}
    round2_kinds = {step["kind"] for step in rounds[1]["planned_steps"]}
    assert round1_kinds == {"analyze_sources", "analyze_pages"}
    assert "analyze_pages_by_source" in round2_kinds
    assert "analyze_gsc_queries" in round2_kinds


def test_investigate_auto_resolves_goal_when_query_is_about_conversions(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("YANDEX_METRIKA_TOKEN", "token")
    _write_client(tmp_path, goal_id=0, with_gsc=False, with_ym=False)

    monkeypatch.setattr(
        MetrikaClient,
        "list_goals",
        lambda self: {
            "goals": [
                {"id": 1, "name": "Посещение страницы", "type": "url"},
                {"id": 2, "name": "Автоцель: отправка формы заявки", "type": "action"},
            ]
        },
    )
    monkeypatch.setattr(
        MetrikaClient,
        "traffic_sources",
        lambda self, date1, date2, limit=50: _sources_payload(80, 30) if date1 == "2024-01-01" else _sources_payload(75, 20),
    )
    monkeypatch.setattr(
        MetrikaClient,
        "landing_pages",
        lambda self, date1, date2, limit=50: _pages_payload(60, 20) if date1 == "2024-01-01" else _pages_payload(55, 10),
    )
    monkeypatch.setattr(
        MetrikaClient,
        "goals_by_source",
        lambda self, date1, date2, goal_id, limit=50: _goals_payload(80, 10, 30, 3) if date1 == "2024-01-01" else _goals_payload(75, 5, 20, 1),
    )
    monkeypatch.setattr(
        MetrikaClient,
        "goals_by_page",
        lambda self, date1, date2, goal_id, limit=50: {
            "data": [
                {"dimensions": [{"name": "https://example.com/form"}], "metrics": [40, 5, 12.5]},
                {"dimensions": [{"name": "https://example.com/pricing"}], "metrics": [20, 2, 10.0]},
            ]
        }
        if date1 == "2024-01-01"
        else {
            "data": [
                {"dimensions": [{"name": "https://example.com/form"}], "metrics": [35, 0, 0.0]},
                {"dimensions": [{"name": "https://example.com/pricing"}], "metrics": [20, 1, 5.0]},
            ]
        },
    )

    result = runner.invoke(
        app,
        [
            "investigate",
            "demo",
            "--query",
            "Проверь, почему упали заявки и конверсии 2024-01-01 2024-01-31 2025-01-01 2025-01-31",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Goal:" in result.stdout

    report_dir = next((tmp_path / "reports" / "demo").iterdir())
    evidence = json.loads((report_dir / "evidence.json").read_text(encoding="utf-8"))
    assert evidence["goal_selection"]["goal_id"] == 2
    kinds = {step["kind"] for step in evidence["analysis"]["executed_steps"]}
    assert "analyze_goals_by_source" in kinds
    assert "analyze_goals_by_page" in kinds
    rounds = evidence["analysis"]["loop"]["rounds"]
    assert len(rounds) >= 2
    round1_kinds = {step["kind"] for step in rounds[0]["planned_steps"]}
    round2_kinds = {step["kind"] for step in rounds[1]["planned_steps"]}
    assert "analyze_goals_by_source" in round1_kinds
    assert "analyze_goals_by_page" in round2_kinds

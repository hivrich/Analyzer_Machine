import json

from app.seo_activation_funnel import (
    create_seo_activation_funnel_report,
    load_product_activation_by_landing_page,
    normalize_landing_page,
    report_filename,
)


def test_seo_activation_funnel_merges_gsc_metrika_and_product_rows():
    report = create_seo_activation_funnel_report(
        client="stasrun",
        site_url="https://stas.run/",
        counter_id=100635480,
        goal_id=549619513,
        date1="2026-05-01",
        date2="2026-05-07",
        gsc_pages=[
            {
                "page": "https://stas.run/en/guides/intervals-icu-ai-coach?utm=ignored",
                "clicks": 10,
                "impressions": 100,
                "ctr": 10.0,
                "position": 4.0,
            },
            {
                "page": "https://stas.run/en/guides/intervals-icu-ai-coach",
                "clicks": 5,
                "impressions": 50,
                "ctr": 10.0,
                "position": 8.0,
            },
        ],
        metrika_organic_pages=[
            {
                "landingPage": "https://stas.run/en/guides/intervals-icu-ai-coach",
                "visits": 12,
                "users": 9,
            }
        ],
        goals_by_source_page=[
            {
                "source": "Search engine traffic",
                "landingPage": "https://stas.run/en/guides/intervals-icu-ai-coach",
                "visits": 12,
                "goal_visits": 3,
                "goal_cr_pct": 25.0,
            },
            {
                "source": "Direct traffic",
                "landingPage": "https://stas.run/en/guides/intervals-icu-ai-coach",
                "visits": 20,
                "goal_visits": 7,
                "goal_cr_pct": 35.0,
            },
        ],
        product_db={
            "available": True,
            "reason": "ok",
            "rows": [
                {
                    "landingPage": "/en/guides/intervals-icu-ai-coach",
                    "signups": 2,
                    "oauth_start": 1,
                    "intervals_connected": 2,
                    "gpt_connected": 1,
                    "claude_connected": 1,
                    "first_data_request": 1,
                    "training_processed": 1,
                }
            ],
        },
        limit=50,
        refresh_used=True,
        product_db_url_env="STAS_DATABASE_URL",
    )

    assert report["product_db"]["available"] is True
    assert report["totals"]["gsc_clicks"] == 15.0
    assert report["totals"]["metrika_organic_visits"] == 12.0
    assert report["totals"]["metrika_signup_goal"] == 3.0

    row = report["rows"][0]
    assert row["landingPage"] == "/en/guides/intervals-icu-ai-coach"
    assert row["gsc"]["clicks"] == 15.0
    assert row["gsc"]["impressions"] == 150.0
    assert row["gsc"]["ctr"] == 10.0
    assert row["gsc"]["position"] == 5.333333333333333
    assert row["metrika"]["organic_visits"] == 12.0
    assert row["metrika"]["organic_users"] == 9.0
    assert row["metrika"]["signup_goal"] == 3.0
    assert row["product"]["signups"] == 2
    assert row["conversion_rates"]["metrika_visit_to_signup_goal"] == 25.0
    assert row["conversion_rates"]["signup_to_first_data_request"] == 50.0


def test_product_db_env_missing_does_not_invent_activation_data(monkeypatch):
    monkeypatch.delenv("STAS_DATABASE_URL", raising=False)

    product_db = load_product_activation_by_landing_page(
        date1="2026-05-01",
        date2="2026-05-07",
        env_var="STAS_DATABASE_URL",
    )

    assert product_db == {
        "available": False,
        "env_var": "STAS_DATABASE_URL",
        "reason": "env_missing",
        "rows": [],
    }

    report = create_seo_activation_funnel_report(
        client="stasrun",
        site_url="https://stas.run/",
        counter_id=100635480,
        goal_id=549619513,
        date1="2026-05-01",
        date2="2026-05-07",
        gsc_pages=[
            {"page": "https://stas.run/en", "clicks": 1, "impressions": 10, "ctr": 10.0, "position": 2.0},
        ],
        metrika_organic_pages=[],
        goals_by_source_page=[],
        product_db=product_db,
        limit=50,
        refresh_used=False,
    )

    assert report["product_db"]["available"] is False
    assert report["product_db"]["reason"] == "env_missing"
    assert report["rows"][0]["product"]["signups"] == 0
    assert report["rows"][0]["product"]["training_processed"] == 0


def test_report_is_json_serializable_and_uses_expected_filename():
    report = create_seo_activation_funnel_report(
        client="stasrun",
        site_url="https://stas.run/",
        counter_id=100635480,
        goal_id=549619513,
        date1="2026-05-01",
        date2="2026-05-07",
        gsc_pages=[],
        metrika_organic_pages=[],
        goals_by_source_page=[],
        product_db={"available": False, "reason": "env_missing", "rows": []},
        limit=50,
        refresh_used=False,
    )

    assert report_filename("2026-05-01", "2026-05-07") == "seo_activation_funnel_2026-05-01_2026-05-07.json"
    assert json.loads(json.dumps(report))["meta"]["client"] == "stasrun"


def test_normalize_landing_page_is_stable_for_sources():
    assert normalize_landing_page("https://stas.run/en/guides/test?x=1#top") == "/en/guides/test"
    assert normalize_landing_page("/en/guides/test/") == "/en/guides/test"
    assert normalize_landing_page("") == "(unknown)"

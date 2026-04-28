from app.en_seo_report import create_en_seo_weekly_report, is_en_landing_page, is_organic_source
from app.metrika_client import normalize_goals_by_source_page


def test_en_seo_report_aggregates_gsc_and_metrika():
    report = create_en_seo_weekly_report(
        client="stasrun",
        site_url="https://stas.run/",
        counter_id=100635480,
        goal_id=549619513,
        date1="2026-04-20",
        date2="2026-04-26",
        gsc_pages=[
            {"page": "https://stas.run/en/guides/intervals-icu-ai-coach", "clicks": 3, "impressions": 30, "ctr": 10.0, "position": 5.0},
            {"page": "https://stas.run/ru/guides/ai-running-coach", "clicks": 10, "impressions": 100, "ctr": 10.0, "position": 2.0},
            {"page": "https://stas.run/en", "clicks": 2, "impressions": 20, "ctr": 10.0, "position": 8.0},
        ],
        gsc_query_page=[
            {"query": "intervals icu ai coach", "page": "https://stas.run/en/guides/intervals-icu-ai-coach", "clicks": 3, "impressions": 30, "ctr": 10.0, "position": 5.0},
            {"query": "stas", "page": "https://stas.run/en", "clicks": 2, "impressions": 20, "ctr": 10.0, "position": 8.0},
            {"query": "stas ru", "page": "https://stas.run/ru", "clicks": 5, "impressions": 50, "ctr": 10.0, "position": 1.0},
        ],
        goals_by_source=[
            {"source": "Search engine traffic", "visits": 40, "goal_visits": 2, "goal_cr_pct": 5.0},
            {"source": "Direct traffic", "visits": 20, "goal_visits": 1, "goal_cr_pct": 5.0},
        ],
        goals_by_source_page=[
            {"source": "Search engine traffic", "landingPage": "https://stas.run/en/guides/intervals-icu-ai-coach", "visits": 12, "goal_visits": 2, "goal_cr_pct": 16.7},
            {"source": "Direct traffic", "landingPage": "https://stas.run/en", "visits": 10, "goal_visits": 1, "goal_cr_pct": 10.0},
            {"source": "Search engine traffic", "landingPage": "https://stas.run/ru", "visits": 8, "goal_visits": 1, "goal_cr_pct": 12.5},
        ],
        limit=10,
        refresh_used=False,
    )

    assert report["gsc_en"]["clicks"] == 5.0
    assert report["gsc_en"]["impressions"] == 50.0
    assert report["gsc_en"]["ctr"] == 10.0
    assert report["gsc_en"]["position"] == 6.2
    assert report["gsc_en"]["top_queries"][0]["query"] == "intervals icu ai coach"
    assert report["metrika_signup_success"]["en_organic_signups"] == 2.0


def test_normalize_goals_by_source_page():
    rows = normalize_goals_by_source_page(
        {
            "data": [
                {
                    "dimensions": [
                        {"name": "Search engine traffic"},
                        {"name": "https://stas.run/en"},
                    ],
                    "metrics": [10, 2, 20.0],
                }
            ]
        }
    )

    assert rows == [
        {
            "source": "Search engine traffic",
            "landingPage": "https://stas.run/en",
            "visits": 10.0,
            "goal_visits": 2.0,
            "goal_cr_pct": 20.0,
        }
    ]


def test_en_and_organic_detection():
    assert is_en_landing_page("https://stas.run/en/guides/ai-running-coach")
    assert is_en_landing_page("/en")
    assert not is_en_landing_page("https://stas.run/ru")
    assert is_organic_source("Search engine traffic")
    assert is_organic_source("organic")
    assert not is_organic_source("Direct traffic")

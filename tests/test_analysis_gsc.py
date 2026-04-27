import json

from app.analysis_gsc import load_or_fetch_gsc


class FakeGSCClient:
    def search_analytics(self, date1, date2, dimensions, row_limit):
        assert date1 == "2026-04-01"
        assert date2 == "2026-04-25"
        assert dimensions == ["query", "page"]
        assert row_limit == 10
        return {
            "rows": [
                {
                    "keys": ["intervals icu ai coach", "https://stas.run/en/guides/intervals-icu-ai-coach"],
                    "clicks": 2,
                    "impressions": 20,
                    "ctr": 0.1,
                    "position": 7.5,
                }
            ]
        }


def test_load_or_fetch_gsc_query_page(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    rows, dimensions = load_or_fetch_gsc(
        client="stasrun",
        kind="query_page",
        date1="2026-04-01",
        date2="2026-04-25",
        limit=10,
        refresh=True,
        gsc_client=FakeGSCClient(),
    )

    assert dimensions == ["query", "page"]
    assert rows == [
        {
            "query": "intervals icu ai coach",
            "page": "https://stas.run/en/guides/intervals-icu-ai-coach",
            "clicks": 2.0,
            "impressions": 20.0,
            "ctr": 10.0,
            "position": 7.5,
        }
    ]

    norm_file = tmp_path / "data_cache" / "stasrun" / "gsc_query_page_norm_2026-04-01_2026-04-25.json"
    assert json.loads(norm_file.read_text(encoding="utf-8")) == rows

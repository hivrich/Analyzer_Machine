from __future__ import annotations

from app import http_client


def test_merge_no_proxy_merges_and_deduplicates():
    merged = http_client._merge_no_proxy("a,b", ["b", "c"])
    assert merged.split(",") == ["a", "b", "c"]


def test_default_session_sets_proxies(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://proxy:8080")
    monkeypatch.setenv("NO_PROXY", "localhost")
    session = http_client.get_default_session()
    assert session.proxies["http"] == "http://proxy:8080"
    assert "api-metrika.yandex.net" in session.proxies["no_proxy"]

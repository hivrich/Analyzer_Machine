from pathlib import Path

from app.audit import AuditEngine, DataPoint


def test_verify_data_source_reads_from_data_cache(tmp_path):
    client = "acme"
    cache_dir = tmp_path / "data_cache" / client
    reports_dir = tmp_path / "reports"
    cache_dir.mkdir(parents=True)

    source_file = cache_dir / "analysis_sources_sample.json"
    source_file.write_text('{"totals":{"total_visits_p1":123}}', encoding="utf-8")

    cwd = Path.cwd()
    try:
        import os

        os.chdir(tmp_path)
        engine = AuditEngine(client, reports_dir=reports_dir)
        result = engine.verify_data_source(
            DataPoint(
                metric="total_visits_p1",
                value=123,
                source_file="analysis_sources_sample.json",
                period="2026-03",
                context={},
            )
        )
    finally:
        os.chdir(cwd)

    assert result.status == "passed"
    assert any("analysis_sources_sample.json" in evidence for evidence in result.evidence)


def test_verify_data_source_accepts_absolute_path(tmp_path):
    client = "acme"
    reports_dir = tmp_path / "reports"
    source_file = tmp_path / "workbook.json"
    source_file.write_text('{"totals":{"total_visits_p2":456}}', encoding="utf-8")

    engine = AuditEngine(client, reports_dir=reports_dir)
    result = engine.verify_data_source(
        DataPoint(
            metric="total_visits_p2",
            value=456,
            source_file=str(source_file),
            period="2026-03",
            context={},
        )
    )

    assert result.status == "passed"

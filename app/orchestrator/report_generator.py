from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from app.orchestrator.models import InvestigationReport


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _render_markdown(analysis: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# Расследование: {analysis['client']}")
    lines.append("")
    lines.append(f"**Запрос:** {analysis['query']}")
    lines.append(f"**Период:** {analysis['period']['description']}")
    lines.append(f"**Итог:** {analysis['summary']}")
    lines.append("")
    lines.append("## Как система проверяла гипотезы")
    lines.append("")
    loop = analysis.get("loop") or {}
    rounds = loop.get("rounds") or []
    for round_info in rounds:
        step_titles = ", ".join(step["title"] for step in round_info.get("planned_steps", [])) or "шагов не было"
        lines.append(
            f"- **Раунд {round_info.get('round')}**: {round_info.get('summary', '')}  "
        )
        lines.append(f"  Шаги: {step_titles}")
    if loop.get("stop_reason"):
        lines.append(f"- **Остановка:** {loop['stop_reason']}")
    if not rounds:
        lines.append("- Итерации не зафиксированы.")
    lines.append("")
    lines.append("## Что произошло")
    lines.append("")
    for fact in analysis["facts"]:
        lines.append(f"- **{fact['title']}**: {fact['value']}  ")
        lines.append(f"  Evidence: `{fact['evidence']}`")
    if not analysis["facts"]:
        lines.append("- Фактов недостаточно.")
    lines.append("")
    lines.append("## Главные причины")
    lines.append("")
    for driver in analysis["drivers"]:
        lines.append(f"- **{driver['title']}**: {driver['value']}  ")
        lines.append(f"  Evidence: `{driver['evidence']}`")
    if not analysis["drivers"]:
        lines.append("- Явные драйверы автоматически не выделены.")
    lines.append("")
    lines.append("## Гипотезы")
    lines.append("")
    for hypothesis in analysis["hypotheses"]:
        lines.append(f"### {hypothesis['title']}")
        lines.append(f"- Статус: {hypothesis['status']}")
        lines.append(f"- Уверенность: {hypothesis['confidence']}")
        lines.append(f"- Почему: {hypothesis['because']}")
        lines.append(f"- Что проверить: {hypothesis['next_check']}")
        if hypothesis["evidence"]:
            lines.append(f"- Evidence: {', '.join(f'`{item}`' for item in hypothesis['evidence'])}")
        lines.append("")
    if not analysis["hypotheses"]:
        lines.append("- Автоматические гипотезы не сформированы.")
        lines.append("")
    lines.append("## Что было недоступно")
    lines.append("")
    for note in analysis["availability_notes"]:
        lines.append(f"- {note}")
    if not analysis["availability_notes"]:
        lines.append("- Все основные источники были доступны для выбранного сценария.")
    lines.append("")
    lines.append("## Следующие действия")
    lines.append("")
    if analysis.get("recommended_next_steps"):
        for item in analysis["recommended_next_steps"][:5]:
            lines.append(f"- {item['reason']}")
    elif analysis["hypotheses"]:
        for hypothesis in analysis["hypotheses"][:3]:
            lines.append(f"- {hypothesis['next_check']}")
    else:
        lines.append("- Уточнить запрос или расширить набор источников.")
    return "\n".join(lines).strip() + "\n"


def _render_html(analysis: Dict[str, Any]) -> str:
    loop = analysis.get("loop") or {}
    loop_rounds = "\n".join(
        (
            "<li>"
            f"<strong>Раунд {item.get('round')}</strong>: {html.escape(item.get('summary', ''))}"
            f"<br><span class=\"neutral\">Шаги: {html.escape(', '.join(step['title'] for step in item.get('planned_steps', [])) or 'шагов не было')}</span>"
            "</li>"
        )
        for item in loop.get("rounds", [])
    ) or "<li>Итерации не зафиксированы.</li>"

    fact_items = "\n".join(
        f"<li><strong>{html.escape(item['title'])}</strong>: {html.escape(item['value'])} "
        f"<span class=\"neutral\">({html.escape(item['evidence'])})</span></li>"
        for item in analysis["facts"]
    ) or "<li>Фактов недостаточно.</li>"

    driver_items = "\n".join(
        f"<li><strong>{html.escape(item['title'])}</strong>: {html.escape(item['value'])} "
        f"<span class=\"neutral\">({html.escape(item['evidence'])})</span></li>"
        for item in analysis["drivers"]
    ) or "<li>Явные драйверы автоматически не выделены.</li>"

    hypothesis_blocks = "\n".join(
        (
            "<div class=\"insight\">"
            f"<h3>{html.escape(item['title'])}</h3>"
            f"<p><strong>Статус:</strong> {html.escape(item['status'])}</p>"
            f"<p><strong>Уверенность:</strong> {html.escape(item['confidence'])}</p>"
            f"<p><strong>Почему:</strong> {html.escape(item['because'])}</p>"
            f"<p><strong>Что проверить:</strong> {html.escape(item['next_check'])}</p>"
            f"<p><strong>Evidence:</strong> {html.escape(', '.join(item['evidence']))}</p>"
            "</div>"
        )
        for item in analysis["hypotheses"]
    ) or "<p>Автоматические гипотезы не сформированы.</p>"

    missing_items = "\n".join(
        f"<li>{html.escape(note)}</li>" for note in analysis["availability_notes"]
    ) or "<li>Все основные источники были доступны для выбранного сценария.</li>"

    next_actions = "\n".join(
        f"<li>{html.escape(item['reason'])}</li>" for item in analysis.get("recommended_next_steps", [])[:5]
    )
    if not next_actions:
        next_actions = "\n".join(
            f"<li>{html.escape(item['next_check'])}</li>" for item in analysis["hypotheses"][:3]
        ) or "<li>Уточнить запрос или расширить набор источников.</li>"

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="../../../docs/reports/common.css">
    <title>Расследование: {html.escape(analysis['client'])}</title>
</head>
<body>
    <div class="container">
        <h1>Расследование: {html.escape(analysis['client'])}</h1>
        <div class="subtitle">{html.escape(analysis['query'])}</div>
        <div class="meta">
            <div class="meta-item"><strong>Период:</strong> {html.escape(analysis['period']['description'])}</div>
            <div class="meta-item"><strong>Фокус:</strong> {html.escape(analysis['intent']['primary_focus'])}</div>
        </div>

        <div class="executive-summary">
            <h2>Что произошло</h2>
            <p>{html.escape(analysis['summary'])}</p>
        </div>

        <h2>Как система проверяла гипотезы</h2>
        <ul>
            {loop_rounds}
        </ul>
        <p><strong>Остановка:</strong> {html.escape(loop.get('stop_reason', 'Не указана'))}</p>

        <h2>Факты</h2>
        <ul>
            {fact_items}
        </ul>

        <h2>Главные причины</h2>
        <ul>
            {driver_items}
        </ul>

        <h2>Гипотезы</h2>
        {hypothesis_blocks}

        <h2>Что было недоступно</h2>
        <ul>
            {missing_items}
        </ul>

        <h2>Что делать дальше</h2>
        <ul>
            {next_actions}
        </ul>
    </div>
</body>
</html>
"""


def write_report_files(client: str, analysis: Dict[str, Any], evidence: Dict[str, Any]) -> InvestigationReport:
    run_id = _run_id()
    report_dir = Path("reports") / client / run_id
    report_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = report_dir / "report.md"
    html_path = report_dir / "report.html"
    evidence_json_path = report_dir / "evidence.json"
    evidence_txt_path = report_dir / "evidence.txt"

    markdown_path.write_text(_render_markdown(analysis), encoding="utf-8")
    html_path.write_text(_render_html(analysis), encoding="utf-8")
    evidence_json_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")

    evidence_lines = [f"query={analysis['query']}", f"period={analysis['period']['description']}"]
    for step in analysis["executed_steps"]:
        for artifact in step["artifacts"]:
            evidence_lines.append(artifact)
    evidence_txt_path.write_text("\n".join(evidence_lines) + "\n", encoding="utf-8")

    return InvestigationReport(
        run_id=run_id,
        report_dir=str(report_dir),
        markdown_path=str(markdown_path),
        html_path=str(html_path),
        evidence_json_path=str(evidence_json_path),
        evidence_txt_path=str(evidence_txt_path),
        summary=analysis["summary"],
    )

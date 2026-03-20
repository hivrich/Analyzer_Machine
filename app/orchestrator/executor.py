from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import List

import click

from app.orchestrator.models import ExecutedStep, PlannedStep


def _invoke_direct(step: PlannedStep) -> ExecutedStep:
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    exit_code = 0

    try:
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            if step.kind == "analyze_sources":
                from app.cli import analyze_sources_cmd

                analyze_sources_cmd(**step.params)
            elif step.kind == "analyze_pages":
                from app.cli import analyze_pages_cmd

                analyze_pages_cmd(**step.params)
            elif step.kind == "analyze_pages_by_source":
                from app.cli import analyze_pages_by_source_cmd

                analyze_pages_by_source_cmd(**step.params)
            elif step.kind == "analyze_goals_by_source":
                from app.cli import analyze_goals_by_source_cmd

                analyze_goals_by_source_cmd(**step.params)
            elif step.kind == "analyze_goals_by_page":
                from app.cli import analyze_goals_by_page_cmd

                analyze_goals_by_page_cmd(**step.params)
            elif step.kind == "analyze_gsc_queries":
                from app.cli import analyze_gsc_queries_cmd

                analyze_gsc_queries_cmd(**step.params)
            elif step.kind == "analyze_gsc_pages":
                from app.cli import analyze_gsc_pages_cmd

                analyze_gsc_pages_cmd(**step.params)
            elif step.kind == "analyze_ym_webmaster_queries":
                from app.cli import analyze_ym_webmaster_queries_cmd

                analyze_ym_webmaster_queries_cmd(**step.params)
            elif step.kind == "ym_webmaster_indexing":
                from app.cli import ym_webmaster_indexing_cmd

                ym_webmaster_indexing_cmd(**step.params)
            else:
                raise RuntimeError(f"Unsupported planned step kind: {step.kind}")
    except click.exceptions.Exit as exc:
        exit_code = int(exc.exit_code or 0)
    except SystemExit as exc:
        exit_code = int(exc.code or 0)
    except Exception as exc:  # pragma: no cover - defensive path
        exit_code = 1
        stderr_buffer.write(str(exc))

    artifacts = [artifact for artifact in step.expected_artifacts if Path(artifact).exists()]
    return ExecutedStep(
        id=step.id,
        title=step.title,
        kind=step.kind,
        success=exit_code == 0,
        exit_code=exit_code,
        stdout=stdout_buffer.getvalue(),
        stderr=stderr_buffer.getvalue(),
        artifacts=artifacts,
        source=step.source,
        params=step.params,
    )


def execute_plan(plan: List[PlannedStep]) -> List[ExecutedStep]:
    return [_invoke_direct(step) for step in plan]

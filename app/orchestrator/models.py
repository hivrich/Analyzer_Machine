from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class InvestigationIntent:
    query: str
    wants_traffic: bool
    wants_pages: bool
    wants_conversions: bool
    wants_seo: bool
    wants_indexing: bool
    wants_report: bool
    wants_deep: bool
    direction: str
    primary_focus: str
    period_note: str


@dataclass(frozen=True)
class InvestigationAvailability:
    metrika: bool
    gsc: bool
    ym_webmaster: bool
    notes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class GoalSelection:
    goal_id: Optional[int]
    source: str
    confidence: str
    reason: str
    candidates: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class InvestigationPeriod:
    p1_start: str
    p1_end: str
    p2_start: str
    p2_end: str
    source: str
    description: str


@dataclass(frozen=True)
class PlannedStep:
    id: str
    title: str
    kind: str
    params: Dict[str, Any]
    source: str
    expected_artifacts: List[str]


@dataclass(frozen=True)
class ExecutedStep:
    id: str
    title: str
    kind: str
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    artifacts: List[str]
    source: str
    params: Dict[str, Any]


@dataclass(frozen=True)
class InvestigationReport:
    run_id: str
    report_dir: str
    markdown_path: str
    html_path: str
    evidence_json_path: str
    evidence_txt_path: str
    summary: str

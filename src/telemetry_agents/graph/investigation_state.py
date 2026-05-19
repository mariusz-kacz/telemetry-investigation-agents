from enum import StrEnum
from typing import TypedDict, Annotated

from telemetry_agents.domain import (
    Incident,
    InvestigationHypothesis,
    InvestigationReport,
)
from telemetry_agents.domain.models import HypothesisValidationResult
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence


def append_findings(existing: list[str], new: list[str]) -> list[str]:
    return existing + new


class InvestigationRoute(StrEnum):
    """Possible deterministic branches after incident intake."""

    LOG_FOCUSED = "log_focused"
    TRACE_FOCUSED = "trace_focused"
    METRIC_FOCUSED = "metric_focused"
    BROAD = "broad"


class InvestigationGraphState(TypedDict, total=False):
    incident_input: str
    normalized_incident: Incident
    collected_evidence: list[RetrievedEvidence]
    intermediate_findings: Annotated[list[str], append_findings]
    hypotheses: list[InvestigationHypothesis]
    validation_result: HypothesisValidationResult
    final_report: InvestigationReport
    errors: list[str]
    warnings: list[str]
    routing_decision: InvestigationRoute

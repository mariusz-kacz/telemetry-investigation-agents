from enum import StrEnum
from typing import TypedDict, Annotated

from telemetry_agents.domain import (
    Incident,
    InvestigationHypothesis,
    InvestigationReport,
)
from telemetry_agents.domain.models import (
    HypothesisValidationResult,
    HypothesisCritiqueFinding,
)
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence


def append(existing: list[str], new: list[str]) -> list[str]:
    return existing + new


class InvestigationGraphState(TypedDict, total=False):
    incident_input: str
    normalized_incident: Incident
    collected_evidence: list[RetrievedEvidence]
    intermediate_findings: Annotated[list[str], append]
    hypotheses: list[InvestigationHypothesis]
    validation_result: HypothesisValidationResult
    critique_findings: list[HypothesisCritiqueFinding]
    report_review_decision: dict[str, bool]
    report_review_completed: bool
    final_report: InvestigationReport
    errors: list[str]
    warnings: Annotated[list[str], append]

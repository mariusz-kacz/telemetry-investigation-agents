from typing import TypedDict, Annotated

from telemetry_agents.domain import (
    Incident,
    InvestigationHypothesis,
    InvestigationReport,
)
from telemetry_agents.domain.models import (
    HypothesisValidationResult,
    HypothesisCritiqueFinding,
    HumanReviewAssessment,
    HumanReviewStatus,
    HypothesisReviewResult,
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
    review_result: HypothesisReviewResult
    human_review_assessment: HumanReviewAssessment
    human_review_status: HumanReviewStatus
    report_ready: bool
    final_report: InvestigationReport
    errors: list[str]
    warnings: Annotated[list[str], append]

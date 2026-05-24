from pydantic import BaseModel, Field

from telemetry_agents.domain import (
    HypothesisValidationResult,
    Incident,
    HumanReviewAssessment,
    HypothesisCritiqueFinding,
    LOW_CONFIDENCE_THRESHOLD,
    IncidentImpact,
)
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


class HumanReviewAssessmentRequest(BaseModel):
    critique_findings: list[HypothesisCritiqueFinding] = Field(default_factory=list)
    validation_result: HypothesisValidationResult
    evidence: list[RetrievedEvidence] = Field(default_factory=list)
    incident: Incident


def assess_human_review_requirement(
    request: HumanReviewAssessmentRequest,
) -> HumanReviewAssessment:
    reasons: list[str] = []

    if request.incident.impact == IncidentImpact.HIGH:
        reasons.append("high incident impact")

    if request.critique_findings:
        reasons.append("critic findings present")

    if not request.evidence:
        reasons.append("missing evidence")

    if not request.validation_result.accepted_hypotheses:
        reasons.append("no accepted hypotheses")

    if (
        request.validation_result.accepted_hypotheses
        and min(
            item.confidence for item in request.validation_result.accepted_hypotheses
        )
        < LOW_CONFIDENCE_THRESHOLD
    ):
        reasons.append("low accepted hypothesis confidence")

    if any(
        item.strength in {EvidenceStrength.WEAK, EvidenceStrength.MISSING}
        for item in request.evidence
    ):
        reasons.append("missing or weak evidence strength")

    return HumanReviewAssessment(
        human_review_required=bool(reasons),
        human_review_reason="; ".join(reasons) if reasons else None,
    )

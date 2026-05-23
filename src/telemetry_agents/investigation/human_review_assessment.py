from pydantic import BaseModel, Field

from telemetry_agents.domain.models import (
    HypothesisValidationResult,
    Incident,
    HumanReviewAssessment,
    HypothesisCritiqueFinding,
)
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence


class HumanReviewAssessmentRequest(BaseModel):
    critique_findings: list[HypothesisCritiqueFinding] = Field(default_factory=list)
    validation_result: HypothesisValidationResult
    evidence: list[RetrievedEvidence] = Field(default_factory=list)
    incident: Incident


def assess_human_review_requirement(
    request: HumanReviewAssessmentRequest,
) -> HumanReviewAssessment:
    return HumanReviewAssessment(
        human_review_required=True,
        human_review_reason="Human review required",
    )

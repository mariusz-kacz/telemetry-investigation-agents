from pydantic import BaseModel, Field

from telemetry_agents.domain import (
    HypothesisValidationResult,
    Incident,
    HumanReviewAssessment,
    IncidentImpact,
    ReviewedHypothesis,
    HypothesisReviewStatus,
    HypothesisCategory,
)
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


DOMINANCE_MARGIN = 0.15


class HumanReviewAssessmentRequest(BaseModel):
    incident: Incident
    evidence: list[RetrievedEvidence] = Field(default_factory=list)
    validation_result: HypothesisValidationResult
    reviewed_hypotheses: list[ReviewedHypothesis] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def _top_confidence(
    hypotheses: list[ReviewedHypothesis],
    status: HypothesisReviewStatus,
) -> float | None:
    confidences = [
        item.hypothesis.confidence for item in hypotheses if item.status is status
    ]
    return max(confidences, default=None)


def _human_review_reasons_for_hypotheses(
    reviewed_hypotheses: list[ReviewedHypothesis],
) -> list[str]:
    if not reviewed_hypotheses:
        return []

    reasons = []
    top_hypothesis = max(
        reviewed_hypotheses,
        key=lambda item: item.hypothesis.confidence,
    )
    disputed_count = sum(
        item.status is HypothesisReviewStatus.DISPUTED for item in reviewed_hypotheses
    )
    top_accepted_confidence = _top_confidence(
        reviewed_hypotheses,
        HypothesisReviewStatus.ACCEPTED,
    )
    top_disputed_confidence = _top_confidence(
        reviewed_hypotheses,
        HypothesisReviewStatus.DISPUTED,
    )
    top_blocked_confidence = _top_confidence(
        reviewed_hypotheses,
        HypothesisReviewStatus.BLOCKED,
    )

    if top_hypothesis.status in {
        HypothesisReviewStatus.DISPUTED,
        HypothesisReviewStatus.BLOCKED,
    }:
        reasons.append("top reviewed hypothesis is blocked or disputed")

    if top_accepted_confidence is None:
        reasons.append("no accepted hypothesis exists")
        return reasons

    if (
        top_disputed_confidence is not None
        and disputed_count >= 2
        and top_accepted_confidence - top_disputed_confidence < DOMINANCE_MARGIN
    ):
        reasons.append(
            "multiple disputed hypotheses exist and no dominant accepted hypothesis exists"
        )

    if top_blocked_confidence is not None and (
        top_accepted_confidence - top_blocked_confidence < DOMINANCE_MARGIN
    ):
        reasons.append(
            "blocked hypothesis is within DOMINANCE_MARGIN of the top accepted hypothesis"
        )

    return reasons


def assess_human_review_requirement(
    request: HumanReviewAssessmentRequest,
) -> HumanReviewAssessment:
    reasons: list[str] = []

    if request.incident.impact == IncidentImpact.HIGH:
        reasons.append("high incident impact")

    if not request.evidence:
        reasons.append("missing evidence")

    if any(
        item.strength in {EvidenceStrength.WEAK, EvidenceStrength.MISSING}
        for item in request.evidence
    ):
        reasons.append("missing or weak evidence strength")

    if not request.validation_result.validated_hypotheses:
        reasons.append("no validated hypotheses")

    if any(
        item.status is HypothesisReviewStatus.ACCEPTED
        and item.hypothesis.category
        in {
            HypothesisCategory.INSUFFICIENT_EVIDENCE,
            HypothesisCategory.UNCERTAIN_ROOT_CAUSE,
        }
        for item in request.reviewed_hypotheses
    ):
        reasons.append("accepted hypothesis indicates insufficient evidence")

    reasons.extend(
        _human_review_reasons_for_hypotheses(
            reviewed_hypotheses=request.reviewed_hypotheses
        )
    )

    if request.warnings:
        reasons.append("warnings present")

    return HumanReviewAssessment(
        human_review_required=bool(reasons),
        human_review_reason="; ".join(reasons) if reasons else None,
    )

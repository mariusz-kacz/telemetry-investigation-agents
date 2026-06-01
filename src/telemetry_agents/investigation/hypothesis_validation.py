from pydantic import BaseModel, Field

from telemetry_agents.domain import InvestigationHypothesis
from telemetry_agents.domain.models import (
    HypothesisValidationResult,
    LOW_CONFIDENCE_THRESHOLD,
    RejectedHypothesis,
    ConfidenceAdjustment,
)
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


class HypothesisValidationRequest(BaseModel):
    evidence: list[RetrievedEvidence] = Field(default_factory=list)
    hypotheses: list[InvestigationHypothesis]


def _max_confidence_for_evidence_strengths(strengths: set[EvidenceStrength]) -> float:
    if not strengths or EvidenceStrength.MISSING in strengths:
        return 0.0

    if strengths <= {EvidenceStrength.WEAK}:
        return 0.4

    if strengths <= {EvidenceStrength.WEAK, EvidenceStrength.MEDIUM}:
        return 0.8

    return 1.0


def validate_hypotheses(
    request: HypothesisValidationRequest,
) -> HypothesisValidationResult:
    """Validate generated hypotheses against retrieved evidence."""
    accepted_hypotheses: list[InvestigationHypothesis] = []
    rejected_hypotheses: list[RejectedHypothesis] = []
    confidence_adjustments: list[ConfidenceAdjustment] = []

    evidence_by_id = {
        evidence.evidence.evidence_id: evidence for evidence in request.evidence
    }

    for hypothesis in request.hypotheses:
        if not hypothesis.supporting_evidence_ids:
            rejected_hypotheses.append(
                RejectedHypothesis(
                    hypothesis=hypothesis,
                    reason="Hypothesis has no supporting evidence IDs.",
                )
            )
            continue

        unknown_ids = set(hypothesis.supporting_evidence_ids) - evidence_by_id.keys()
        if unknown_ids:
            rejected_hypotheses.append(
                RejectedHypothesis(
                    hypothesis=hypothesis,
                    reason="Hypothesis references unknown evidence IDs.",
                )
            )
            continue

        supporting_evidences: list[RetrievedEvidence] = [
            evidence_by_id[supporting_evidence_id]
            for supporting_evidence_id in hypothesis.supporting_evidence_ids
        ]

        strengths = {item.strength for item in supporting_evidences}

        if EvidenceStrength.MISSING in strengths:
            rejected_hypotheses.append(
                RejectedHypothesis(
                    hypothesis=hypothesis,
                    reason="Hypothesis uses missing evidence as support.",
                )
            )
            continue

        max_confidence = _max_confidence_for_evidence_strengths(strengths)

        if hypothesis.confidence > max_confidence:
            updates: dict[str, str | float] = {"confidence": max_confidence}
            adjustment_reason = "Confidence was reduced because the cited evidence is not strong enough to support a higher-confidence hypothesis."
            if max_confidence < LOW_CONFIDENCE_THRESHOLD and (
                not hypothesis.uncertainty or not hypothesis.uncertainty.strip()
            ):
                updates["uncertainty"] = adjustment_reason

            confidence_adjustments.append(
                ConfidenceAdjustment(
                    reason=adjustment_reason,
                    hypothesis_id=hypothesis.hypothesis_id,
                    original_confidence=hypothesis.confidence,
                    adjusted_confidence=max_confidence,
                )
            )

            adjusted_hypothesis_data = hypothesis.model_dump()
            adjusted_hypothesis_data.update(updates)
            adjusted_hypothesis = InvestigationHypothesis.model_validate(
                adjusted_hypothesis_data
            )
            accepted_hypotheses.append(adjusted_hypothesis)
        else:
            accepted_hypotheses.append(hypothesis)

    return HypothesisValidationResult(
        accepted_hypotheses=accepted_hypotheses,
        rejected_hypotheses=rejected_hypotheses,
        confidence_adjustments=confidence_adjustments,
    )

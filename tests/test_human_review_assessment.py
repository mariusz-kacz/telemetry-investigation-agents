import pytest

from telemetry_agents.domain import (
    EvidenceSource,
    InvestigationHypothesis,
    TelemetryEvidence,
)
from telemetry_agents.domain.models import (
    HypothesisCritiqueFinding,
    CritiqueFindingType,
    HypothesisValidationResult,
    Incident,
    RejectedHypothesis,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.investigation.human_review_assessment import (
    HumanReviewAssessmentRequest,
    assess_human_review_requirement,
)


def _retrieved_evidence(
    *,
    summary: str = "Checkout API reports database timeout errors.",
    strength: EvidenceStrength = EvidenceStrength.STRONG,
) -> RetrievedEvidence:
    evidence = TelemetryEvidence(
        evidence_id="evidence_001",
        source=EvidenceSource.LOG,
        summary=summary,
        citation="sample_data/logs/checkout-api.log:1",
        service="checkout-api",
    )
    return RetrievedEvidence(
        evidence=evidence,
        citation=CitationMetadata(
            source_file="sample_data/logs/checkout-api.log",
            line_number=1,
            service="checkout-api",
            selection_reason="Matched incident query terms.",
        ),
        strength=strength,
        relevance_score=1.0 if strength == EvidenceStrength.STRONG else 0.2,
    )


def _critique_finding() -> HypothesisCritiqueFinding:
    return HypothesisCritiqueFinding(
        hypothesis_id="hyp-001",
        evidence_ids=["log-001"],
        finding_type=CritiqueFindingType.UNSUPPORTED_CAUSAL_LEAP,
        reason="The evidence supports timeout symptoms but not the full causal claim.",
    )


def _hypothesis(
    hypothesis_id: str = "hyp-001",
    confidence: float = 0.9,
    uncertainty: str | None = None,
) -> InvestigationHypothesis:
    return InvestigationHypothesis(
        hypothesis_id=hypothesis_id,
        statement="Checkout latency is caused by database timeout errors.",
        supporting_evidence_ids=["log-001"],
        confidence=confidence,
        uncertainty=uncertainty,
    )


def _validation_result() -> HypothesisValidationResult:
    return HypothesisValidationResult(accepted_hypotheses=[_hypothesis()])


def _incident() -> Incident:
    return Incident(
        incident_id="inc-001",
        title="Checkout API latency spike",
        service="checkout-api",
    )


def test_requires_human_review_when_has_critic_findings() -> None:
    request = HumanReviewAssessmentRequest(
        validation_result=_validation_result(),
        critique_findings=[_critique_finding()],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert result.human_review_reason == "critic findings present"


def test_requires_human_review_when_has_no_evidences() -> None:
    request = HumanReviewAssessmentRequest(
        validation_result=_validation_result(),
        critique_findings=[],
        evidence=[],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert result.human_review_reason == "missing evidence"


def test_requires_human_review_when_has_no_accepted_hypotheses() -> None:
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(accepted_hypotheses=[]),
        critique_findings=[],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert result.human_review_reason == "no accepted hypotheses"


def test_requires_human_review_when_hypothesis_has_low_confidence() -> None:
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(
            accepted_hypotheses=[
                _hypothesis(confidence=0.4, uncertainty="Low confidence")
            ]
        ),
        critique_findings=[],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert result.human_review_reason == "low accepted hypothesis confidence"


@pytest.mark.parametrize(
    "strength",
    [
        EvidenceStrength.WEAK,
        EvidenceStrength.MISSING,
    ],
)
def test_requires_human_review_when_weak_evidence_strength(
    strength: EvidenceStrength,
) -> None:
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(
            accepted_hypotheses=[_hypothesis()]
        ),
        critique_findings=[],
        evidence=[_retrieved_evidence(strength=strength)],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert result.human_review_reason == "missing or weak evidence strength"


def test_human_review_not_required_when_all_criteria_met() -> None:
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(
            accepted_hypotheses=[_hypothesis()]
        ),
        critique_findings=[],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is False
    assert not result.human_review_reason


def test_rejected_alternative_does_not_require_review_when_accepted_hypothesis_is_strong() -> (
    None
):
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(
            accepted_hypotheses=[_hypothesis()],
            rejected_hypotheses=[
                RejectedHypothesis(
                    hypothesis=_hypothesis(
                        confidence=0.4,
                        uncertainty="Low confidence",
                        hypothesis_id="hyp-rejected-001",
                    ),
                    reason="Weak hypothesis",
                )
            ],
        ),
        critique_findings=[],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is False
    assert result.human_review_reason is None


def test_collects_multiple_review_reasons() -> None:
    request = HumanReviewAssessmentRequest(
        validation_result=_validation_result(),
        critique_findings=[_critique_finding()],
        evidence=[_retrieved_evidence(strength=EvidenceStrength.WEAK)],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert result.human_review_reason == (
        "critic findings present; missing or weak evidence strength"
    )

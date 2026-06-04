from telemetry_agents.domain import (
    CritiqueFindingType,
    HypothesisCategory,
    HypothesisReviewStatus,
    InvestigationHypothesis,
)
from telemetry_agents.domain.models import HypothesisCritiqueFinding
from telemetry_agents.investigation.hypothesis_review import (
    HypothesisReviewRequest,
    review_hypotheses,
)


def _hypothesis(
    hypothesis_id: str = "hyp-001",
    *,
    confidence: float = 0.9,
) -> InvestigationHypothesis:
    return InvestigationHypothesis(
        hypothesis_id=hypothesis_id,
        statement=f"Hypothesis {hypothesis_id}",
        category=HypothesisCategory.DATABASE_FAILURE,
        supporting_evidence_ids=["log-001"],
        confidence=confidence,
    )


def _finding(
    finding_type: CritiqueFindingType,
    *,
    hypothesis_id: str = "hyp-001",
) -> HypothesisCritiqueFinding:
    return HypothesisCritiqueFinding(
        hypothesis_id=hypothesis_id,
        evidence_ids=["log-001"],
        finding_type=finding_type,
        reason=f"Critic found {finding_type.value}.",
    )


def _review_status_for(
    *findings: HypothesisCritiqueFinding,
    hypothesis: InvestigationHypothesis | None = None,
) -> HypothesisReviewStatus:
    result = review_hypotheses(
        HypothesisReviewRequest(
            validated_hypotheses=[hypothesis or _hypothesis()],
            critique_findings=list(findings),
        )
    )

    return result.reviewed_hypotheses[0].status


def test_no_findings_marks_hypothesis_accepted() -> None:
    assert _review_status_for() is HypothesisReviewStatus.ACCEPTED


def test_alternative_interpretation_marks_hypothesis_disputed() -> None:
    assert (
        _review_status_for(_finding(CritiqueFindingType.ALTERNATIVE_INTERPRETATION))
        is HypothesisReviewStatus.DISPUTED
    )


def test_overstated_confidence_marks_hypothesis_disputed() -> None:
    assert (
        _review_status_for(_finding(CritiqueFindingType.OVERSTATED_CONFIDENCE))
        is HypothesisReviewStatus.DISPUTED
    )


def test_unsupported_causal_leap_marks_hypothesis_blocked() -> None:
    assert (
        _review_status_for(_finding(CritiqueFindingType.UNSUPPORTED_CAUSAL_LEAP))
        is HypothesisReviewStatus.BLOCKED
    )


def test_contradiction_marks_hypothesis_blocked() -> None:
    assert (
        _review_status_for(_finding(CritiqueFindingType.CONTRADICTION))
        is HypothesisReviewStatus.BLOCKED
    )


def test_blocked_finding_beats_disputed_finding_for_same_hypothesis() -> None:
    assert (
        _review_status_for(
            _finding(CritiqueFindingType.ALTERNATIVE_INTERPRETATION),
            _finding(CritiqueFindingType.CONTRADICTION),
        )
        is HypothesisReviewStatus.BLOCKED
    )


def test_review_result_is_one_to_one_with_validated_hypotheses() -> None:
    hypotheses = [
        _hypothesis("hyp-001"),
        _hypothesis("hyp-002"),
    ]

    result = review_hypotheses(
        HypothesisReviewRequest(
            validated_hypotheses=hypotheses,
            critique_findings=[
                _finding(
                    CritiqueFindingType.ALTERNATIVE_INTERPRETATION,
                    hypothesis_id="hyp-002",
                )
            ],
        )
    )

    assert [item.hypothesis.hypothesis_id for item in result.reviewed_hypotheses] == [
        "hyp-001",
        "hyp-002",
    ]
    assert [item.status for item in result.reviewed_hypotheses] == [
        HypothesisReviewStatus.ACCEPTED,
        HypothesisReviewStatus.DISPUTED,
    ]


def test_review_preserves_all_findings_for_hypothesis() -> None:
    findings = [
        _finding(CritiqueFindingType.ALTERNATIVE_INTERPRETATION),
        _finding(CritiqueFindingType.OVERSTATED_CONFIDENCE),
    ]

    result = review_hypotheses(
        HypothesisReviewRequest(
            validated_hypotheses=[_hypothesis()],
            critique_findings=findings,
        )
    )

    assert result.reviewed_hypotheses[0].critique_findings == findings


def test_review_does_not_change_hypothesis_confidence() -> None:
    hypothesis = _hypothesis(confidence=0.95)

    result = review_hypotheses(
        HypothesisReviewRequest(
            validated_hypotheses=[hypothesis],
            critique_findings=[_finding(CritiqueFindingType.CONTRADICTION)],
        )
    )

    assert result.reviewed_hypotheses[0].hypothesis.confidence == 0.95

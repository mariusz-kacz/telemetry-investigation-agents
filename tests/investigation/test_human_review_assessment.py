import pytest

from telemetry_agents.domain import (
    HypothesisCritiqueFinding,
    CritiqueFindingType,
    HypothesisValidationResult,
    HypothesisReviewStatus,
    Incident,
    IncidentImpact,
    RejectedHypothesis,
    ReviewedHypothesis,
    EvidenceSource,
    InvestigationHypothesis,
    TelemetryEvidence,
    HypothesisCategory,
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
    category: HypothesisCategory = HypothesisCategory.DATABASE_FAILURE,
) -> InvestigationHypothesis:
    return InvestigationHypothesis(
        hypothesis_id=hypothesis_id,
        statement="Checkout latency is caused by database timeout errors.",
        category=category,
        supporting_evidence_ids=["log-001"],
        confidence=confidence,
        uncertainty=uncertainty,
    )


def _validation_result() -> HypothesisValidationResult:
    return HypothesisValidationResult(validated_hypotheses=[_hypothesis()])


def _reviewed_hypothesis(
    hypothesis: InvestigationHypothesis | None = None,
    *,
    status: HypothesisReviewStatus = HypothesisReviewStatus.ACCEPTED,
) -> ReviewedHypothesis:
    return ReviewedHypothesis(
        hypothesis=hypothesis or _hypothesis(),
        status=status,
    )


def _incident(impact: IncidentImpact = IncidentImpact.MEDIUM) -> Incident:
    return Incident(
        incident_id="inc-001",
        title="Checkout API latency spike",
        service="checkout-api",
        impact=impact,
        reported_at="2026-05-11T10:05:00Z",
        investigation_window={
            "start": "2026-05-11T09:40:00Z",
            "end": "2026-05-11T10:10:00Z",
        },
        retrieval={"query_terms": ["timeout"], "trace_id": "trace-001"},
    )


def test_raw_critic_findings_do_not_directly_trigger_human_review() -> None:
    request = HumanReviewAssessmentRequest(
        validation_result=_validation_result(),
        critique_findings=[_critique_finding()],
        reviewed_hypotheses=[_reviewed_hypothesis()],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is False
    assert result.human_review_reason is None


def test_requires_human_review_when_has_no_evidences() -> None:
    request = HumanReviewAssessmentRequest(
        validation_result=_validation_result(),
        reviewed_hypotheses=[_reviewed_hypothesis()],
        evidence=[],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert result.human_review_reason == "missing evidence"


def test_requires_human_review_when_has_no_validated_hypotheses() -> None:
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(validated_hypotheses=[]),
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert result.human_review_reason == "no validated hypotheses"


def test_low_confidence_alone_does_not_trigger_human_review() -> None:
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(
            validated_hypotheses=[
                _hypothesis(confidence=0.4, uncertainty="Low confidence")
            ]
        ),
        reviewed_hypotheses=[
            _reviewed_hypothesis(
                _hypothesis(confidence=0.4, uncertainty="Low confidence")
            )
        ],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is False
    assert result.human_review_reason is None


def test_accepted_insufficient_evidence_hypothesis_triggers_human_review() -> None:
    insufficient_evidence_hypothesis = _hypothesis(
        "hyp-insufficient",
        confidence=0.4,
        uncertainty="Evidence shows symptoms but does not identify a root cause.",
        category=HypothesisCategory.INSUFFICIENT_EVIDENCE,
    )
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(
            validated_hypotheses=[insufficient_evidence_hypothesis]
        ),
        reviewed_hypotheses=[_reviewed_hypothesis(insufficient_evidence_hypothesis)],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert (
        result.human_review_reason
        == "accepted hypothesis indicates insufficient evidence"
    )


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
            validated_hypotheses=[_hypothesis()]
        ),
        reviewed_hypotheses=[_reviewed_hypothesis()],
        evidence=[_retrieved_evidence(strength=strength)],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert result.human_review_reason == "missing or weak evidence strength"


def test_human_review_not_required_when_all_criteria_met() -> None:
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(
            validated_hypotheses=[_hypothesis()]
        ),
        reviewed_hypotheses=[_reviewed_hypothesis()],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is False
    assert not result.human_review_reason


def test_rejected_alternative_does_not_require_review_when_validated_hypothesis_is_strong() -> (
    None
):
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(
            validated_hypotheses=[_hypothesis()],
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
        reviewed_hypotheses=[_reviewed_hypothesis()],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is False
    assert result.human_review_reason is None


def test_collects_multiple_review_reasons() -> None:
    request = HumanReviewAssessmentRequest(
        validation_result=_validation_result(),
        reviewed_hypotheses=[_reviewed_hypothesis()],
        evidence=[_retrieved_evidence(strength=EvidenceStrength.WEAK)],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert result.human_review_reason == "missing or weak evidence strength"


def test_requires_human_review_when_incident_impact_is_high() -> None:
    request = HumanReviewAssessmentRequest(
        validation_result=_validation_result(),
        reviewed_hypotheses=[_reviewed_hypothesis()],
        evidence=[_retrieved_evidence()],
        incident=_incident(IncidentImpact.HIGH),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert result.human_review_reason == "high incident impact"


def test_requires_human_review_when_has_warnings() -> None:
    request = HumanReviewAssessmentRequest(
        warnings=["Hypothesis critic was unavailable; semantic review was skipped."],
        validation_result=_validation_result(),
        reviewed_hypotheses=[_reviewed_hypothesis()],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert result.human_review_reason == "warnings present"


def test_medium_impact_does_not_require_review_when_other_conditions_are_safe() -> None:
    request = HumanReviewAssessmentRequest(
        validation_result=_validation_result(),
        reviewed_hypotheses=[_reviewed_hypothesis()],
        evidence=[_retrieved_evidence()],
        incident=_incident(IncidentImpact.MEDIUM),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is False
    assert result.human_review_reason is None


def test_top_disputed_hypothesis_triggers_human_review() -> None:
    top_hypothesis = _hypothesis("hyp-top", confidence=0.95)
    lower_hypothesis = _hypothesis("hyp-lower", confidence=0.9)
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(
            validated_hypotheses=[top_hypothesis, lower_hypothesis]
        ),
        reviewed_hypotheses=[
            _reviewed_hypothesis(
                top_hypothesis,
                status=HypothesisReviewStatus.DISPUTED,
            ),
            _reviewed_hypothesis(lower_hypothesis),
        ],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert "top reviewed hypothesis is blocked or disputed" in (
        result.human_review_reason or ""
    )


def test_top_blocked_hypothesis_triggers_human_review() -> None:
    top_hypothesis = _hypothesis("hyp-top", confidence=0.95)
    lower_hypothesis = _hypothesis("hyp-lower", confidence=0.9)
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(
            validated_hypotheses=[top_hypothesis, lower_hypothesis]
        ),
        reviewed_hypotheses=[
            _reviewed_hypothesis(
                top_hypothesis,
                status=HypothesisReviewStatus.BLOCKED,
            ),
            _reviewed_hypothesis(lower_hypothesis),
        ],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert "top reviewed hypothesis is blocked or disputed" in (
        result.human_review_reason or ""
    )


def test_no_accepted_hypothesis_triggers_human_review() -> None:
    disputed_hypothesis = _hypothesis("hyp-disputed", confidence=0.95)
    blocked_hypothesis = _hypothesis("hyp-blocked", confidence=0.9)
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(
            validated_hypotheses=[disputed_hypothesis, blocked_hypothesis]
        ),
        reviewed_hypotheses=[
            _reviewed_hypothesis(
                disputed_hypothesis,
                status=HypothesisReviewStatus.DISPUTED,
            ),
            _reviewed_hypothesis(
                blocked_hypothesis,
                status=HypothesisReviewStatus.BLOCKED,
            ),
        ],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert "no accepted hypothesis exists" in (result.human_review_reason or "")


def test_multiple_disputed_without_dominant_accepted_triggers_human_review() -> None:
    accepted_hypothesis = _hypothesis("hyp-accepted", confidence=0.9)
    disputed_hypothesis = _hypothesis("hyp-disputed-001", confidence=0.82)
    other_disputed_hypothesis = _hypothesis("hyp-disputed-002", confidence=0.81)
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(
            validated_hypotheses=[
                accepted_hypothesis,
                disputed_hypothesis,
                other_disputed_hypothesis,
            ]
        ),
        reviewed_hypotheses=[
            _reviewed_hypothesis(accepted_hypothesis),
            _reviewed_hypothesis(
                disputed_hypothesis,
                status=HypothesisReviewStatus.DISPUTED,
            ),
            _reviewed_hypothesis(
                other_disputed_hypothesis,
                status=HypothesisReviewStatus.DISPUTED,
            ),
        ],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert (
        "multiple disputed hypotheses exist and no dominant accepted hypothesis exists"
        in (result.human_review_reason or "")
    )


def test_multiple_disputed_with_dominant_accepted_does_not_trigger_human_review() -> (
    None
):
    accepted_hypothesis = _hypothesis("hyp-accepted", confidence=0.99)
    disputed_hypothesis = _hypothesis("hyp-disputed-001", confidence=0.83)
    other_disputed_hypothesis = _hypothesis("hyp-disputed-002", confidence=0.82)
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(
            validated_hypotheses=[
                accepted_hypothesis,
                disputed_hypothesis,
                other_disputed_hypothesis,
            ]
        ),
        reviewed_hypotheses=[
            _reviewed_hypothesis(accepted_hypothesis),
            _reviewed_hypothesis(
                disputed_hypothesis,
                status=HypothesisReviewStatus.DISPUTED,
            ),
            _reviewed_hypothesis(
                other_disputed_hypothesis,
                status=HypothesisReviewStatus.DISPUTED,
            ),
        ],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is False
    assert result.human_review_reason is None


def test_non_top_disputed_alone_does_not_trigger_human_review_when_top_accepted_is_dominant() -> (
    None
):
    accepted_hypothesis = _hypothesis("hyp-accepted", confidence=0.99)
    disputed_hypothesis = _hypothesis("hyp-disputed", confidence=0.83)
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(
            validated_hypotheses=[accepted_hypothesis, disputed_hypothesis]
        ),
        reviewed_hypotheses=[
            _reviewed_hypothesis(accepted_hypothesis),
            _reviewed_hypothesis(
                disputed_hypothesis,
                status=HypothesisReviewStatus.DISPUTED,
            ),
        ],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is False
    assert result.human_review_reason is None


def test_blocked_hypothesis_near_top_accepted_hypothesis_triggers_human_review() -> (
    None
):
    accepted_hypothesis = _hypothesis("hyp-accepted", confidence=0.95)
    blocked_hypothesis = _hypothesis("hyp-blocked", confidence=0.90)
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(
            validated_hypotheses=[accepted_hypothesis, blocked_hypothesis]
        ),
        reviewed_hypotheses=[
            _reviewed_hypothesis(accepted_hypothesis),
            _reviewed_hypothesis(
                blocked_hypothesis,
                status=HypothesisReviewStatus.BLOCKED,
            ),
        ],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is True
    assert (
        "blocked hypothesis is within DOMINANCE_MARGIN of the top accepted hypothesis"
        in (result.human_review_reason or "")
    )


def test_zero_confidence_accepted_hypothesis_still_counts_as_accepted_present() -> None:
    accepted_hypothesis = _hypothesis(
        "hyp-zero-confidence",
        confidence=0.0,
        uncertainty="Evidence support is effectively absent.",
    )
    request = HumanReviewAssessmentRequest(
        validation_result=HypothesisValidationResult(
            validated_hypotheses=[accepted_hypothesis]
        ),
        reviewed_hypotheses=[_reviewed_hypothesis(accepted_hypothesis)],
        evidence=[_retrieved_evidence()],
        incident=_incident(),
    )

    result = assess_human_review_requirement(request)

    assert result.human_review_required is False
    assert result.human_review_reason is None

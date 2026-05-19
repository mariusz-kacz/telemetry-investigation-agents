from telemetry_agents.domain import (
    EvidenceSource,
    InvestigationHypothesis,
    TelemetryEvidence,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.investigation.hypothesis_validation import (
    HypothesisValidationRequest,
    validate_hypotheses,
)


def _retrieved_evidence(
    evidence_id: str,
    *,
    summary: str = "Checkout API reports database timeout errors.",
    strength: EvidenceStrength = EvidenceStrength.STRONG,
) -> RetrievedEvidence:
    evidence = TelemetryEvidence(
        evidence_id=evidence_id,
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


def test_validation_rejects_hypothesis_without_supporting_evidence() -> None:
    hypothesis = InvestigationHypothesis(
        hypothesis_id="hyp-unsupported",
        statement="Checkout latency is caused by database timeout errors.",
        supporting_evidence_ids=[],
        confidence=0.8,
    )
    request = HypothesisValidationRequest(
        evidence=[_retrieved_evidence("log-001")],
        hypotheses=[hypothesis],
    )

    result = validate_hypotheses(request)

    assert result.accepted_hypotheses == []
    assert result.rejected_hypotheses[0].hypothesis == hypothesis
    assert "supporting evidence" in result.rejected_hypotheses[0].reason


def test_validation_rejects_missing_evidence_as_support() -> None:
    hypothesis = InvestigationHypothesis(
        hypothesis_id="hyp-missing-evidence",
        statement="Checkout latency is caused by database timeout errors.",
        supporting_evidence_ids=["missing-log-inc-001"],
        confidence=0.8,
    )
    request = HypothesisValidationRequest(
        evidence=[
            _retrieved_evidence(
                "missing-log-inc-001",
                summary="No matching log evidence found for the incident filters.",
                strength=EvidenceStrength.MISSING,
            )
        ],
        hypotheses=[hypothesis],
    )

    result = validate_hypotheses(request)

    assert result.accepted_hypotheses == []
    assert result.rejected_hypotheses[0].hypothesis == hypothesis
    assert "missing evidence" in result.rejected_hypotheses[0].reason


def test_validation_rejects_unknown_evidence_reference() -> None:
    hypothesis = InvestigationHypothesis(
        hypothesis_id="hyp-unknown-evidence",
        statement="Checkout latency is caused by database timeout errors.",
        supporting_evidence_ids=["unknown-log-001"],
        confidence=0.8,
    )
    request = HypothesisValidationRequest(
        evidence=[_retrieved_evidence("log-001")],
        hypotheses=[hypothesis],
    )

    result = validate_hypotheses(request)

    assert result.accepted_hypotheses == []
    assert result.rejected_hypotheses[0].hypothesis == hypothesis
    assert "unknown evidence" in result.rejected_hypotheses[0].reason


def test_validation_rejects_mixed_known_and_unknown_evidence_references() -> None:
    hypothesis = InvestigationHypothesis(
        hypothesis_id="hyp-mixed-evidence",
        statement="Checkout latency is caused by database timeout errors.",
        supporting_evidence_ids=["log-001", "unknown-log-001"],
        confidence=0.8,
    )
    request = HypothesisValidationRequest(
        evidence=[_retrieved_evidence("log-001")],
        hypotheses=[hypothesis],
    )

    result = validate_hypotheses(request)

    assert result.accepted_hypotheses == []
    assert result.rejected_hypotheses[0].hypothesis == hypothesis
    assert "unknown evidence" in result.rejected_hypotheses[0].reason


def test_validation_downgrades_weak_but_plausible_hypothesis() -> None:
    hypothesis = InvestigationHypothesis(
        hypothesis_id="hyp-weak",
        statement="Checkout latency may be related to intermittent database timeouts.",
        supporting_evidence_ids=["log-weak"],
        confidence=0.9,
    )
    request = HypothesisValidationRequest(
        evidence=[
            _retrieved_evidence(
                "log-weak",
                summary="One checkout request reported a database timeout.",
                strength=EvidenceStrength.WEAK,
            )
        ],
        hypotheses=[hypothesis],
    )

    result = validate_hypotheses(request)

    assert len(result.accepted_hypotheses) == 1
    assert result.accepted_hypotheses[0].hypothesis_id == "hyp-weak"
    assert result.accepted_hypotheses[0].confidence <= 0.4
    assert result.accepted_hypotheses[0].uncertainty
    assert result.confidence_adjustments[0].hypothesis_id == "hyp-weak"
    assert result.confidence_adjustments[0].original_confidence == 0.9
    assert result.confidence_adjustments[0].adjusted_confidence <= 0.4


def test_validation_caps_confidence_for_medium_without_strong_evidence() -> (
    None
):
    hypothesis = InvestigationHypothesis(
        hypothesis_id="hyp-medium",
        statement="Checkout API latency may be caused by elevated database latency.",
        supporting_evidence_ids=["metric-001"],
        confidence=0.95,
    )
    request = HypothesisValidationRequest(
        evidence=[
            _retrieved_evidence(
                "metric-001",
                strength=EvidenceStrength.MEDIUM,
            )
        ],
        hypotheses=[hypothesis],
    )

    result = validate_hypotheses(request)

    assert len(result.accepted_hypotheses) == 1
    assert result.accepted_hypotheses[0].hypothesis_id == "hyp-medium"
    assert result.accepted_hypotheses[0].confidence <= 0.8
    assert result.confidence_adjustments[0].hypothesis_id == "hyp-medium"
    assert result.confidence_adjustments[0].original_confidence == 0.95
    assert result.confidence_adjustments[0].adjusted_confidence <= 0.8


def test_validation_keeps_confidence_when_strong_evidence_supports_it() -> (
    None
):
    hypothesis = InvestigationHypothesis(
        hypothesis_id="hyp-strong",
        statement="Checkout API latency spike.",
        supporting_evidence_ids=["metric-001"],
        confidence=0.95,
    )
    request = HypothesisValidationRequest(
        evidence=[
            _retrieved_evidence(
                "metric-001",
                strength=EvidenceStrength.STRONG,
            )
        ],
        hypotheses=[hypothesis],
    )

    result = validate_hypotheses(request)

    assert len(result.accepted_hypotheses) == 1
    assert result.accepted_hypotheses[0].hypothesis_id == "hyp-strong"
    assert result.accepted_hypotheses[0].confidence == 0.95
    assert len(result.confidence_adjustments) == 0


def test_validation_allows_empty_hypothesis_list() -> None:
    request = HypothesisValidationRequest(
        evidence=[_retrieved_evidence("log-001")],
        hypotheses=[],
    )

    result = validate_hypotheses(request)

    assert result.accepted_hypotheses == []
    assert result.rejected_hypotheses == []
    assert result.confidence_adjustments == []
    assert result.contradictions == []


def test_validation_does_not_mutate_original_hypothesis_when_confidence_is_adjusted() -> (
    None
):
    hypothesis = InvestigationHypothesis(
        hypothesis_id="hyp-weak",
        statement="Checkout latency may be related to intermittent database timeouts.",
        supporting_evidence_ids=["log-weak"],
        confidence=0.9,
    )
    request = HypothesisValidationRequest(
        evidence=[_retrieved_evidence("log-weak", strength=EvidenceStrength.WEAK)],
        hypotheses=[hypothesis],
    )

    result = validate_hypotheses(request)

    assert result.accepted_hypotheses[0].confidence <= 0.4
    assert hypothesis.confidence == 0.9


def test_validation_accepts_strong_evidence_hypothesis() -> None:
    hypothesis = InvestigationHypothesis(
        hypothesis_id="hyp-strong",
        statement="Checkout latency is caused by database timeout errors.",
        supporting_evidence_ids=["log-strong"],
        confidence=0.9,
    )
    request = HypothesisValidationRequest(
        evidence=[_retrieved_evidence("log-strong")],
        hypotheses=[hypothesis],
    )

    result = validate_hypotheses(request)

    assert result.accepted_hypotheses == [hypothesis]
    assert result.rejected_hypotheses == []
    assert result.confidence_adjustments == []


def test_validation_surfaces_contradicting_evidence() -> None:
    hypothesis = InvestigationHypothesis(
        hypothesis_id="hyp-contradicted",
        statement="Checkout latency is caused by database timeout errors.",
        supporting_evidence_ids=["log-timeout"],
        confidence=0.9,
    )
    request = HypothesisValidationRequest(
        evidence=[
            _retrieved_evidence("log-timeout"),
            _retrieved_evidence(
                "metric-normal-db-latency",
                summary="Database latency stayed within the normal range during the incident.",
            ),
        ],
        hypotheses=[hypothesis],
    )

    result = validate_hypotheses(request)

    assert result.contradictions
    assert result.contradictions[0].hypothesis_id == "hyp-contradicted"
    assert result.contradictions[0].contradicting_evidence_ids == [
        "metric-normal-db-latency"
    ]

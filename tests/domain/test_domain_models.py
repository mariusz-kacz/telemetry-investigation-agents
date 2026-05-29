import pytest
from pydantic import ValidationError

from telemetry_agents.domain import (
    ConfidenceAdjustment,
    CritiqueFindingType,
    EvidenceSource,
    HumanReviewAssessment,
    HypothesisCritiqueFinding,
    HypothesisValidationResult,
    Incident,
    IncidentImpact,
    InvestigationHypothesis,
    InvestigationReport,
    RejectedHypothesis,
    TelemetryEvidence,
)


def _hypothesis(
    hypothesis_id: str = "hyp-001",
    *,
    confidence: float = 0.9,
    uncertainty: str | None = None,
    supporting_evidence_ids: list[str] | None = None,
) -> InvestigationHypothesis:
    return InvestigationHypothesis(
        hypothesis_id=hypothesis_id,
        statement="Checkout latency is caused by database timeout errors.",
        supporting_evidence_ids=supporting_evidence_ids or ["log-001"],
        confidence=confidence,
        uncertainty=uncertainty,
    )


def _adjustment(hypothesis_id: str = "hyp-001") -> ConfidenceAdjustment:
    return ConfidenceAdjustment(
        hypothesis_id=hypothesis_id,
        original_confidence=0.9,
        adjusted_confidence=0.7,
        reason="Evidence only supports reduced confidence.",
    )


def test_incident_requires_meaningful_identity_and_title() -> None:
    with pytest.raises(ValidationError):
        Incident(
            incident_id="",
            title="",
            service="checkout-api",
            impact=IncidentImpact.MEDIUM,
        )


def test_incident_requires_impact() -> None:
    with pytest.raises(ValidationError):
        Incident.model_validate(
            {"incident_id": "inc-001", "title": "Timeout", "service": "checkout-api"}
        )


def test_non_empty_strings_are_stripped_before_storage() -> None:
    incident = Incident(
        incident_id=" inc-001 ",
        title=" Timeout ",
        service=" checkout-api ",
        impact=IncidentImpact.MEDIUM,
    )

    assert incident.incident_id == "inc-001"
    assert incident.title == "Timeout"
    assert incident.service == "checkout-api"


def test_telemetry_evidence_preserves_citation_metadata() -> None:
    evidence = TelemetryEvidence(
        evidence_id="log-001",
        source=EvidenceSource.LOG,
        summary="Timeout errors increased after deployment.",
        citation="sample_data/logs/checkout-api.log:42",
        service="checkout-api",
    )

    assert evidence.evidence_id == "log-001"
    assert evidence.source == EvidenceSource.LOG
    assert evidence.citation == "sample_data/logs/checkout-api.log:42"


def test_hypothesis_references_supporting_evidence_ids() -> None:
    hypothesis = InvestigationHypothesis(
        hypothesis_id="hyp-001",
        statement="Checkout latency is caused by database timeout errors.",
        supporting_evidence_ids=["log-001", "metric-002"],
        confidence=0.65,
        uncertainty="Confidence is limited because supporting evidence has not been validated yet.",
    )

    assert hypothesis.supporting_evidence_ids == ["log-001", "metric-002"]


def test_report_contains_summary_confidence_and_uncertainty() -> None:
    report = InvestigationReport(
        incident_id="inc-001",
        summary="Checkout API latency increased during payment flow.",
        confidence=0.7,
        uncertainty="Trace data has not been reviewed yet.",
    )

    assert report.incident_id == "inc-001"
    assert report.uncertainty


def test_hypothesis_supporting_evidence_ids_are_normalized() -> None:
    hypothesis = _hypothesis(supporting_evidence_ids=[" log-001 ", "metric-002"])

    assert hypothesis.supporting_evidence_ids == ["log-001", "metric-002"]


@pytest.mark.parametrize(
    "supporting_evidence_ids",
    [
        [" "],
        ["log-001", " log-001 "],
    ],
)
def test_hypothesis_rejects_invalid_supporting_evidence_ids(
    supporting_evidence_ids: list[str],
) -> None:
    with pytest.raises(ValidationError):
        _hypothesis(supporting_evidence_ids=supporting_evidence_ids)


def test_critique_finding_rejects_duplicate_normalized_evidence_ids() -> None:
    with pytest.raises(ValidationError):
        HypothesisCritiqueFinding(
            hypothesis_id="hyp-001",
            evidence_ids=["log-001", " log-001 "],
            finding_type=CritiqueFindingType.CONTRADICTION,
            reason="Evidence conflicts with the hypothesis.",
        )


def test_high_confidence_hypothesis_can_omit_uncertainty() -> None:
    assert _hypothesis().uncertainty is None


@pytest.mark.parametrize("uncertainty", [None, " "])
def test_low_confidence_hypothesis_requires_meaningful_uncertainty(
    uncertainty: str | None,
) -> None:
    with pytest.raises(ValidationError):
        _hypothesis(confidence=0.7, uncertainty=uncertainty)


@pytest.mark.parametrize("uncertainty", [None, " "])
def test_low_confidence_report_requires_meaningful_uncertainty(
    uncertainty: str | None,
) -> None:
    with pytest.raises(ValidationError):
        InvestigationReport(
            incident_id="inc-001",
            summary="Checkout latency is elevated.",
            confidence=0.7,
            uncertainty=uncertainty,
        )


def test_validation_result_rejects_duplicate_accepted_hypothesis_ids() -> None:
    with pytest.raises(ValidationError):
        HypothesisValidationResult(
            accepted_hypotheses=[_hypothesis(), _hypothesis()],
        )


def test_validation_result_rejects_duplicate_rejected_hypothesis_ids() -> None:
    rejected = RejectedHypothesis(
        hypothesis=_hypothesis(),
        reason="Not adequately supported.",
    )

    with pytest.raises(ValidationError):
        HypothesisValidationResult(rejected_hypotheses=[rejected, rejected])


def test_validation_result_rejects_duplicate_confidence_adjustments() -> None:
    with pytest.raises(ValidationError):
        HypothesisValidationResult(
            accepted_hypotheses=[_hypothesis()],
            confidence_adjustments=[_adjustment(), _adjustment()],
        )


def test_validation_result_rejects_accepted_and_rejected_same_hypothesis_id() -> None:
    with pytest.raises(ValidationError):
        HypothesisValidationResult(
            accepted_hypotheses=[_hypothesis()],
            rejected_hypotheses=[
                RejectedHypothesis(
                    hypothesis=_hypothesis(),
                    reason="Rejected alternative.",
                )
            ],
        )


def test_validation_result_rejects_adjustment_for_unaccepted_hypothesis() -> None:
    with pytest.raises(ValidationError):
        HypothesisValidationResult(
            accepted_hypotheses=[_hypothesis()],
            confidence_adjustments=[_adjustment("hyp-unknown")],
        )


def test_human_review_assessment_accepts_required_review_with_reason() -> None:
    assessment = HumanReviewAssessment(
        human_review_required=True,
        human_review_reason="Low confidence.",
    )

    assert assessment.human_review_reason == "Low confidence."


@pytest.mark.parametrize(
    ("required", "reason"),
    [
        (True, None),
        (True, " "),
        (False, "Not applicable."),
    ],
)
def test_human_review_assessment_rejects_inconsistent_reason_state(
    required: bool,
    reason: str | None,
) -> None:
    with pytest.raises(ValidationError):
        HumanReviewAssessment(
            human_review_required=required,
            human_review_reason=reason,
        )

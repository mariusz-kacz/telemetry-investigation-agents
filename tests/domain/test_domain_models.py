import pytest
from pydantic import ValidationError

from telemetry_agents.domain import (
    ConfidenceAdjustment,
    CritiqueFindingType,
    EvidenceSource,
    HumanReviewAssessment,
    HumanReviewStatus,
    HypothesisCritiqueFinding,
    HypothesisValidationResult,
    Incident,
    IncidentImpact,
    InvestigationHypothesis,
    HypothesisCategory,
    InvestigationReport,
    RejectedHypothesis,
    TelemetryEvidence,
)


def _incident_payload(
    *,
    incident_id: str = "inc-001",
    title: str = "Timeout",
    service: str = "checkout-api",
    impact: IncidentImpact = IncidentImpact.MEDIUM,
) -> dict[str, object]:
    return {
        "incident_id": incident_id,
        "title": title,
        "service": service,
        "impact": impact,
        "reported_at": "2026-05-11T10:05:00Z",
        "investigation_window": {
            "start": "2026-05-11T09:40:00Z",
            "end": "2026-05-11T10:10:00Z",
        },
        "retrieval": {
            "query_terms": ["timeout"],
            "trace_id": "trace-001",
        },
    }


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
        category=HypothesisCategory.DATABASE_FAILURE,
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
        Incident.model_validate(_incident_payload(incident_id="", title=""))


def test_incident_requires_impact() -> None:
    with pytest.raises(ValidationError):
        Incident.model_validate(
            {
                key: value
                for key, value in _incident_payload().items()
                if key != "impact"
            }
        )


def test_non_empty_strings_are_stripped_before_storage() -> None:
    incident = Incident.model_validate(
        _incident_payload(
            incident_id=" inc-001 ",
            title=" Timeout ",
            service=" checkout-api ",
        )
    )

    assert incident.incident_id == "inc-001"
    assert incident.title == "Timeout"
    assert incident.service == "checkout-api"


def test_incident_matches_eval_incident_file_contract() -> None:
    incident = Incident.model_validate(
        {
            "incident_id": "inc-checkout-db-timeout-001",
            "title": "Checkout API failures during normal checkout traffic",
            "service": "checkout-api",
            "impact": "medium",
            "reported_at": "2026-05-11T10:05:00Z",
            "investigation_window": {
                "start": "2026-05-11T09:40:00Z",
                "end": "2026-05-11T10:10:00Z",
            },
            "retrieval": {
                "query_terms": ["timeout"],
                "trace_id": "trace-checkout-8421",
            },
        }
    )

    assert incident.retrieval.query_terms == ["timeout"]
    assert incident.retrieval.trace_id == "trace-checkout-8421"
    assert incident.investigation_window.start.isoformat() == (
        "2026-05-11T09:40:00+00:00"
    )


def test_incident_rejects_inverted_investigation_window() -> None:
    payload = _incident_payload()
    payload["investigation_window"] = {
        "start": "2026-05-11T10:10:00Z",
        "end": "2026-05-11T09:40:00Z",
    }

    with pytest.raises(ValidationError, match="end must not precede start"):
        Incident.model_validate(payload)


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
        category=HypothesisCategory.DATABASE_FAILURE,
        supporting_evidence_ids=["log-001", "metric-002"],
        confidence=0.65,
        uncertainty="Confidence is limited because supporting evidence has not been validated yet.",
    )

    assert hypothesis.supporting_evidence_ids == ["log-001", "metric-002"]


def test_hypothesis_category_taxonomy_is_explicit() -> None:
    assert set(HypothesisCategory) == {
        HypothesisCategory.DATABASE_FAILURE,
        HypothesisCategory.AUTHENTICATION_FAILURE,
        HypothesisCategory.DOWNSTREAM_DEPENDENCY_FAILURE,
        HypothesisCategory.RESOURCE_SATURATION,
        HypothesisCategory.NETWORK_FAILURE,
        HypothesisCategory.CONFIGURATION_ERROR,
        HypothesisCategory.APPLICATION_ERROR,
        HypothesisCategory.METRIC_ANOMALY,
        HypothesisCategory.UNCERTAIN_ROOT_CAUSE,
        HypothesisCategory.OTHER,
        HypothesisCategory.INSUFFICIENT_EVIDENCE,
    }


def test_hypothesis_requires_category() -> None:
    with pytest.raises(ValidationError):
        InvestigationHypothesis.model_validate(
            {
                "hypothesis_id": "hyp-001",
                "statement": "Database calls are failing.",
                "supporting_evidence_ids": ["log-001"],
                "confidence": 0.9,
            }
        )


def test_hypothesis_rejects_unknown_serialized_category() -> None:
    with pytest.raises(ValidationError):
        InvestigationHypothesis.model_validate(
            {
                "hypothesis_id": "hyp-001",
                "category": "unknown_failure",
                "statement": "Database calls are failing.",
                "supporting_evidence_ids": ["log-001"],
                "confidence": 0.9,
            }
        )


def test_hypothesis_accepts_known_serialized_category() -> None:
    hypothesis = InvestigationHypothesis.model_validate(
        {
            "hypothesis_id": "hyp-001",
            "category": "database_failure",
            "statement": "Database calls are failing.",
            "supporting_evidence_ids": ["log-001"],
            "confidence": 0.9,
        }
    )

    assert hypothesis.category is HypothesisCategory.DATABASE_FAILURE


def test_report_contains_summary_confidence_and_uncertainty() -> None:
    report = InvestigationReport(
        incident_id="inc-001",
        summary="Checkout API latency increased during payment flow.",
        confidence=0.7,
        uncertainty="Trace data has not been reviewed yet.",
        selected_hypothesis_id=None,
        category=None,
        human_review_status=HumanReviewStatus.NOT_REQUIRED,
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
            selected_hypothesis_id=None,
            category=None,
            human_review_status=HumanReviewStatus.NOT_REQUIRED,
        )


def test_validation_result_rejects_duplicate_accepted_hypothesis_ids() -> None:
    with pytest.raises(ValidationError):
        HypothesisValidationResult(
            validated_hypotheses=[_hypothesis(), _hypothesis()],
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
            validated_hypotheses=[_hypothesis()],
            confidence_adjustments=[_adjustment(), _adjustment()],
        )


def test_validation_result_rejects_accepted_and_rejected_same_hypothesis_id() -> None:
    with pytest.raises(ValidationError):
        HypothesisValidationResult(
            validated_hypotheses=[_hypothesis()],
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
            validated_hypotheses=[_hypothesis()],
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

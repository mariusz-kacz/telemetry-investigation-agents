import pytest
from pydantic import ValidationError

from telemetry_agents.domain import (
    EvidenceSource,
    Incident,
    InvestigationHypothesis,
    InvestigationReport,
    TelemetryEvidence,
)


def test_incident_requires_meaningful_identity_and_title() -> None:
    with pytest.raises(ValidationError):
        Incident(incident_id="", title="", service="checkout-api")


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

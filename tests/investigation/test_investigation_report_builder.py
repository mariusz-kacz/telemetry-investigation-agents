import pytest

from telemetry_agents.domain import (
    EvidenceSource,
    HumanReviewStatus,
    HypothesisCategory,
    HypothesisReviewStatus,
    Incident,
    IncidentImpact,
    InvestigationHypothesis,
    ReviewedHypothesis,
    TelemetryEvidence,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.investigation.investigation_report_builder import (
    build_investigation_report,
)


def test_report_uses_highest_confidence_accepted_hypothesis() -> None:
    report = build_investigation_report(
        incident=_incident(),
        reviewed_hypotheses=[
            _reviewed_hypothesis(
                hypothesis_id="hyp-low",
                statement="A lower confidence explanation.",
                confidence=0.81,
                evidence_ids=["log-001"],
            ),
            _reviewed_hypothesis(
                hypothesis_id="hyp-top",
                statement="Database timeout evidence best explains the incident.",
                confidence=0.91,
                evidence_ids=["log-001", "trace-001"],
            ),
        ],
        collected_evidence=[_evidence("log-001"), _evidence("trace-001")],
        human_review_status=HumanReviewStatus.NOT_REQUIRED,
    )

    assert report.incident_id == "inc-001"
    assert report.summary == "Database timeout evidence best explains the incident."
    assert report.confidence == 0.91
    assert report.selected_hypothesis_id == "hyp-top"
    assert report.category is HypothesisCategory.DATABASE_FAILURE
    assert report.human_review_status is HumanReviewStatus.NOT_REQUIRED
    assert [item.evidence_id for item in report.evidence_citations] == [
        "log-001",
        "trace-001",
    ]


def test_report_ignores_blocked_and_disputed_hypotheses() -> None:
    report = build_investigation_report(
        incident=_incident(),
        reviewed_hypotheses=[
            _reviewed_hypothesis(
                hypothesis_id="hyp-blocked",
                statement="Blocked explanation.",
                confidence=0.95,
                evidence_ids=["log-001"],
                status=HypothesisReviewStatus.BLOCKED,
            ),
            _reviewed_hypothesis(
                hypothesis_id="hyp-disputed",
                statement="Disputed explanation.",
                confidence=0.92,
                evidence_ids=["log-001"],
                status=HypothesisReviewStatus.DISPUTED,
            ),
        ],
        collected_evidence=[_evidence("log-001")],
        human_review_status=HumanReviewStatus.APPROVED,
    )

    assert report.selected_hypothesis_id is None
    assert report.category is None
    assert report.confidence == 0
    assert report.evidence_citations == []
    assert report.uncertainty == (
        "All candidate hypotheses were blocked, disputed, or unavailable."
    )
    assert report.human_review_status is HumanReviewStatus.APPROVED


def test_report_raises_clear_error_for_unknown_evidence_reference() -> None:
    with pytest.raises(ValueError, match="unknown evidence ID: missing-evidence"):
        build_investigation_report(
            incident=_incident(),
            reviewed_hypotheses=[
                _reviewed_hypothesis(
                    hypothesis_id="hyp-001",
                    statement="Database timeout evidence best explains the incident.",
                    confidence=0.91,
                    evidence_ids=["missing-evidence"],
                )
            ],
            collected_evidence=[_evidence("log-001")],
            human_review_status=HumanReviewStatus.NOT_REQUIRED,
        )


def _incident() -> Incident:
    return Incident.model_validate(
        {
            "incident_id": "inc-001",
            "title": "Checkout API latency spike",
            "service": "checkout-api",
            "impact": IncidentImpact.MEDIUM,
            "reported_at": "2026-05-11T10:05:00Z",
            "investigation_window": {
                "start": "2026-05-11T09:40:00Z",
                "end": "2026-05-11T10:10:00Z",
            },
            "retrieval": {"query_terms": ["timeout"], "trace_id": "trace-001"},
        }
    )


def _reviewed_hypothesis(
    *,
    hypothesis_id: str,
    statement: str,
    confidence: float,
    evidence_ids: list[str],
    status: HypothesisReviewStatus = HypothesisReviewStatus.ACCEPTED,
) -> ReviewedHypothesis:
    return ReviewedHypothesis(
        hypothesis=InvestigationHypothesis(
            hypothesis_id=hypothesis_id,
            statement=statement,
            category=HypothesisCategory.DATABASE_FAILURE,
            supporting_evidence_ids=evidence_ids,
            confidence=confidence,
        ),
        status=status,
    )


def _evidence(evidence_id: str) -> RetrievedEvidence:
    return RetrievedEvidence(
        evidence=TelemetryEvidence(
            evidence_id=evidence_id,
            source=EvidenceSource.LOG,
            summary=f"Evidence summary for {evidence_id}.",
            citation=f"sample_data/logs/checkout-api.log:{evidence_id[-1]}",
            service="checkout-api",
        ),
        citation=CitationMetadata(
            source_file="sample_data/logs/checkout-api.log",
            line_number=1,
            service="checkout-api",
            selection_reason="Matched incident query terms.",
        ),
        strength=EvidenceStrength.STRONG,
        relevance_score=1.0,
    )

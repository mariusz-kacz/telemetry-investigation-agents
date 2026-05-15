from telemetry_agents.application.evidence_retrieval import (
    EvidenceRetrievalRequest,
    EvidenceStrength,
    RetrievedEvidence,
    retrieve_evidence,
)
from telemetry_agents.domain import EvidenceSource


def test_retrieved_evidence_preserves_citation_metadata() -> None:
    request = EvidenceRetrievalRequest(
        incident_id="inc-checkout-db-timeout-001",
        service="checkout-api",
        query_terms=["timeout", "database", "deployment"],
        start_timestamp="2026-05-11T09:40:00Z",
        end_timestamp="2026-05-11T10:10:00Z",
        correlation_id="cart-123",
        trace_id="trace-001",
    )

    evidence = retrieve_evidence(request)

    assert evidence
    assert all(isinstance(item, RetrievedEvidence) for item in evidence)
    assert all(item.citation.source_file for item in evidence)
    assert all(item.citation.service == "checkout-api" for item in evidence)
    assert all(item.citation.selection_reason for item in evidence)
    assert any(item.citation.line_number == 1 for item in evidence)
    assert {item.evidence.source for item in evidence} >= {
        EvidenceSource.LOG,
        EvidenceSource.TRACE,
        EvidenceSource.METRIC,
        EvidenceSource.DEPLOYMENT,
    }


def test_evidence_retrieval_ranks_strong_evidence_before_weak_evidence() -> None:
    request = EvidenceRetrievalRequest(
        incident_id="inc-checkout-db-timeout-001",
        service="checkout-api",
        query_terms=["timeout", "database"],
        start_timestamp="2026-05-11T09:40:00Z",
        end_timestamp="2026-05-11T10:10:00Z",
        correlation_id="cart-123",
        trace_id="trace-001",
    )

    evidence = retrieve_evidence(request)

    assert evidence[0].strength == EvidenceStrength.STRONG
    assert evidence[0].relevance_score >= evidence[-1].relevance_score


def test_missing_evidence_is_represented_explicitly() -> None:
    request = EvidenceRetrievalRequest(
        incident_id="inc-no-matching-evidence",
        service="checkout-api",
        query_terms=["cache-poisoning"],
        start_timestamp="2026-05-11T11:00:00Z",
        end_timestamp="2026-05-11T11:30:00Z",
        correlation_id="missing-correlation-id",
        trace_id="missing-trace-id",
    )

    evidence = retrieve_evidence(request)

    assert evidence
    assert any(item.strength == EvidenceStrength.MISSING for item in evidence)
    assert all(item.citation.selection_reason for item in evidence)

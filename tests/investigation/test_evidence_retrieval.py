from pathlib import Path

from telemetry_agents.investigation.evidence_retrieval import (
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
        query_terms=["timeout", "database"],
        start_timestamp="2026-05-11T09:40:00Z",
        end_timestamp="2026-05-11T10:10:00Z",
        correlation_id="cart-123",
        trace_id="trace-001",
        data_root="sample_data",
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
    }
    for item in evidence:
        assert item.evidence.service == item.citation.service
        if item.citation.line_number is not None:
            assert item.evidence.citation == (
                f"{item.citation.source_file}:{item.citation.line_number}"
            )
        else:
            assert item.evidence.citation == item.citation.source_file


def test_evidence_retrieval_ranks_strong_evidence_before_weak_evidence() -> None:
    request = EvidenceRetrievalRequest(
        incident_id="inc-checkout-db-timeout-001",
        service="checkout-api",
        query_terms=["timeout", "database"],
        start_timestamp="2026-05-11T09:40:00Z",
        end_timestamp="2026-05-11T10:10:00Z",
        correlation_id="cart-123",
        trace_id="trace-001",
        data_root="sample_data",
    )

    evidence = retrieve_evidence(request)

    assert evidence[0].strength == EvidenceStrength.STRONG
    assert evidence[0].relevance_score >= evidence[-1].relevance_score


def test_evidence_retrieval_ranks_across_telemetry_sources(tmp_path: Path) -> None:
    (tmp_path / "logs").mkdir()
    (tmp_path / "traces").mkdir()
    (tmp_path / "metrics").mkdir()
    (tmp_path / "logs" / "checkout-api.log").write_text(
        "2026-05-11T10:01:13Z INFO checkout-api "
        "correlation_id=unrelated trace_id=unrelated timeout observed\n",
        encoding="utf-8",
    )
    (tmp_path / "traces" / "checkout-api.jsonl").write_text(
        '{"trace_id":"trace-ranked","span_id":"span-001",'
        '"service":"checkout-api","operation":"POST /checkout",'
        '"duration_ms":2420,"status":"error",'
        '"timestamp":"2026-05-11T10:01:13Z"}\n',
        encoding="utf-8",
    )
    (tmp_path / "metrics" / "checkout-api.jsonl").write_text(
        '{"timestamp":"2026-05-11T10:01:00Z","service":"checkout-api",'
        '"metric_name":"p95_latency_ms","value":2400}\n',
        encoding="utf-8",
    )
    request = EvidenceRetrievalRequest(
        incident_id="inc-ranking-regression",
        service="checkout-api",
        query_terms=["timeout"],
        start_timestamp="2026-05-11T09:40:00Z",
        end_timestamp="2026-05-11T10:10:00Z",
        trace_id="trace-ranked",
        data_root=str(tmp_path),
    )

    evidence = retrieve_evidence(request)

    assert [item.relevance_score for item in evidence] == sorted(
        [item.relevance_score for item in evidence],
        reverse=True,
    )
    assert evidence[0].evidence.source == EvidenceSource.TRACE


def test_evidence_retrieval_preserves_trace_span_citation_metadata() -> None:
    request = EvidenceRetrievalRequest(
        incident_id="inc-checkout-db-timeout-001",
        service="checkout-api",
        query_terms=[],
        start_timestamp="2026-05-11T09:40:00Z",
        end_timestamp="2026-05-11T10:10:00Z",
        trace_id="trace-001",
        data_root="sample_data",
    )

    evidence = retrieve_evidence(request)
    trace_evidence = [
        item for item in evidence if item.evidence.source == EvidenceSource.TRACE
    ]

    assert trace_evidence
    assert (
        trace_evidence[0].citation.source_file
        == "sample_data/traces/checkout-api.jsonl"
    )
    assert trace_evidence[0].citation.line_number == 1
    assert trace_evidence[0].citation.selection_reason == "Matched trace ID trace-001."
    assert trace_evidence[0].evidence.citation.endswith(":1")


def test_evidence_retrieval_preserves_metric_sample_citation_metadata() -> None:
    request = EvidenceRetrievalRequest(
        incident_id="inc-checkout-db-timeout-001",
        service="checkout-api",
        query_terms=[],
        start_timestamp="2026-05-11T09:40:00Z",
        end_timestamp="2026-05-11T10:10:00Z",
        data_root="sample_data",
    )

    evidence = retrieve_evidence(request)
    metric_evidence = [
        item for item in evidence if item.evidence.source == EvidenceSource.METRIC
    ]

    assert metric_evidence
    assert (
        metric_evidence[0].citation.source_file
        == "sample_data/metrics/checkout-api.jsonl"
    )
    assert metric_evidence[0].citation.line_number == 1
    assert metric_evidence[0].citation.selection_reason == (
        "Matched metric p95_latency_ms for service checkout-api "
        "inside incident time window."
    )
    assert metric_evidence[0].evidence.citation.endswith(":1")


def test_missing_evidence_is_represented_explicitly() -> None:
    request = EvidenceRetrievalRequest(
        incident_id="inc-no-matching-evidence",
        service="checkout-api",
        query_terms=["cache-poisoning"],
        start_timestamp="2026-05-11T11:00:00Z",
        end_timestamp="2026-05-11T11:30:00Z",
        correlation_id="missing-correlation-id",
        trace_id="missing-trace-id",
        data_root="sample_data",
    )

    evidence = retrieve_evidence(request)

    assert evidence
    assert any(item.strength == EvidenceStrength.MISSING for item in evidence)
    assert all(item.citation.selection_reason for item in evidence)


def test_missing_source_files_are_represented_as_missing_evidence(
    tmp_path: Path,
) -> None:
    request = EvidenceRetrievalRequest(
        incident_id="inc-no-source-files",
        service="checkout-api",
        query_terms=["timeout"],
        start_timestamp="2026-05-11T11:00:00Z",
        end_timestamp="2026-05-11T11:30:00Z",
        correlation_id="missing-correlation-id",
        trace_id="missing-trace-id",
        data_root=str(tmp_path),
    )

    evidence = retrieve_evidence(request)

    assert {item.evidence.source for item in evidence} == {
        EvidenceSource.LOG,
        EvidenceSource.TRACE,
        EvidenceSource.METRIC,
    }
    assert all(item.strength == EvidenceStrength.MISSING for item in evidence)

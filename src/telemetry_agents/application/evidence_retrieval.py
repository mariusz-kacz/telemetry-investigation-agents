from collections import defaultdict
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from telemetry_agents.application.telemetry_classification import (
    EvidenceStrength,
    classify_matching_log_line,
)
from telemetry_agents.application.log_matching import (
    MatchReason,
    MatchDetail,
    MatchedLogLine,
    get_matching_log_lines,
)
from telemetry_agents.domain import TelemetryEvidence, EvidenceSource
from telemetry_agents.infrastructure.telemetry_readers import LocalFileTelemetryReader
from telemetry_agents.shared.time import parse_utc_timestamp


class CitationMetadata(BaseModel):
    source_file: str = Field(min_length=1)
    line_number: int | None = Field(default=None, ge=1)
    record_id: str | None = None
    timestamp: str | None = None
    service: str = Field(min_length=1)
    selection_reason: str = Field(min_length=1)


class RetrievedEvidence(BaseModel):
    evidence: TelemetryEvidence
    citation: CitationMetadata
    strength: EvidenceStrength
    relevance_score: float = Field(ge=0.0, le=1.0)


class EvidenceRetrievalRequest(BaseModel):
    data_root: str = Field(min_length=1)
    incident_id: str = Field(min_length=1)
    service: str = Field(min_length=1)
    query_terms: list[str] = Field(default_factory=list)
    start_timestamp: str = Field(min_length=1)
    end_timestamp: str = Field(min_length=1)
    correlation_id: str | None = None
    trace_id: str | None = None


def _format_selection_reason(
    match_details: list[MatchDetail],
) -> str:
    result_parts: list[str] = []
    grouped_matches: dict[MatchReason, list[str]] = defaultdict(list)
    for match_detail in match_details:
        grouped_matches[match_detail.reason].append(match_detail.value)

    if correlation_ids := grouped_matches.get(MatchReason.CORRELATION_ID):
        result_parts.append(f"incident correlation ID {correlation_ids[0]}")
    if trace_ids := grouped_matches.get(MatchReason.TRACE_ID):
        result_parts.append(f"trace ID {trace_ids[0]}")
    if query_terms := grouped_matches.get(MatchReason.QUERY_TERM):
        query_terms_text = ", ".join(query_terms)
        result_parts.append(f"query terms: {query_terms_text}")

    if not result_parts:
        raise ValueError("selection reason requires at least one match detail")

    return f"Matched {', '.join(result_parts)}."


def retrieve_evidence(request: EvidenceRetrievalRequest) -> list[RetrievedEvidence]:
    """Retrieve and rank cited evidence for one incident investigation.

    TODO for Phase 7:
    - read logs, traces, metrics, and deployments from local sample data,
    - use deterministic keyword, time-window, correlation ID, and trace ID matching,
    - preserve citation metadata for every returned item,
    - return weak or missing evidence explicitly instead of crashing on empty results.
    """
    try:
        start_timestamp = parse_utc_timestamp(request.start_timestamp)
        end_timestamp = parse_utc_timestamp(request.end_timestamp)
    except ValueError as exc:
        raise ValueError("Wrong timestamp value") from exc

    return _retrieve_log_evidence(end_timestamp, request, start_timestamp)


def _retrieve_log_evidence(
    end_timestamp: datetime,
    request: EvidenceRetrievalRequest,
    start_timestamp: datetime,
) -> list[RetrievedEvidence]:
    retrieved_log_evidence: list[RetrievedEvidence] = []

    reader = LocalFileTelemetryReader(Path(request.data_root))

    matching_log_lines: list[MatchedLogLine] = get_matching_log_lines(
        log_records=reader.read_logs(service=request.service),
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        service=request.service,
        query_terms=request.query_terms,
        correlation_id=request.correlation_id,
        trace_id=request.trace_id,
    )

    for matching_log_line in matching_log_lines:
        telemetry_evidence = TelemetryEvidence(
            evidence_id=f"log-{matching_log_line.log_line.service}-{matching_log_line.line_number}",
            service=matching_log_line.log_line.service,
            citation=f"{matching_log_line.source_file.as_posix()}:{matching_log_line.line_number}",
            source=EvidenceSource.LOG,
            summary=f"{matching_log_line.log_line.level} log from {matching_log_line.log_line.service}: {matching_log_line.log_line.message}",
        )
        citation_metadata = CitationMetadata(
            line_number=matching_log_line.line_number,
            source_file=matching_log_line.source_file.as_posix(),
            service=matching_log_line.log_line.service,
            timestamp=matching_log_line.log_line.timestamp.isoformat(),
            record_id=None,
            selection_reason=_format_selection_reason(matching_log_line.match_details),
        )

        evidence_strength, relevance_score = classify_matching_log_line(
            matching_log_line
        )

        retrieved_log_evidence.append(
            RetrievedEvidence(
                evidence=telemetry_evidence,
                citation=citation_metadata,
                strength=evidence_strength,
                relevance_score=relevance_score,
            )
        )

    if not retrieved_log_evidence:
        return [
            RetrievedEvidence(
                evidence=TelemetryEvidence(
                    evidence_id=f"missing-log-{request.incident_id}",
                    service=request.service,
                    source=EvidenceSource.LOG,
                    citation=f"{request.data_root}/logs/{request.service}.log",
                    summary="No matching log evidence found for the incident filters.",
                ),
                citation=CitationMetadata(
                    source_file=f"{request.data_root}/logs/{request.service}.log",
                    line_number=None,
                    service=request.service,
                    timestamp=None,
                    record_id=None,
                    selection_reason="No log records matched the incident time window, IDs, or query terms.",
                ),
                strength=EvidenceStrength.MISSING,
                relevance_score=0,
            )
        ]
    return retrieved_log_evidence

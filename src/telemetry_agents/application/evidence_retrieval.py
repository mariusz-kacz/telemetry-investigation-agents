from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from telemetry_agents.application.telemetry_parsing import ParsedLogRecord
from telemetry_agents.domain import TelemetryEvidence, EvidenceSource
from telemetry_agents.infrastructure.telemetry_readers import LocalFileTelemetryReader
from telemetry_agents.shared.time import parse_utc_timestamp


class EvidenceStrength(StrEnum):
    STRONG = "strong"
    MEDIUM = "medium"
    WEAK = "weak"
    MISSING = "missing"


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


class MatchReason(StrEnum):
    CORRELATION_ID = "correlation_id"
    TRACE_ID = "trace_id"
    QUERY_TERM = "query_term"


ClassificationRule = tuple[frozenset[MatchReason], EvidenceStrength, float]


LOG_CLASSIFICATION_RULES: tuple[ClassificationRule, ...] = (
    (
        frozenset(
            {
                MatchReason.QUERY_TERM,
                MatchReason.CORRELATION_ID,
                MatchReason.TRACE_ID,
            }
        ),
        EvidenceStrength.STRONG,
        1.0,
    ),
    (
        frozenset({MatchReason.QUERY_TERM, MatchReason.CORRELATION_ID}),
        EvidenceStrength.STRONG,
        0.8,
    ),
    (
        frozenset({MatchReason.QUERY_TERM, MatchReason.TRACE_ID}),
        EvidenceStrength.STRONG,
        0.8,
    ),
    (
        frozenset({MatchReason.CORRELATION_ID, MatchReason.TRACE_ID}),
        EvidenceStrength.MEDIUM,
        0.6,
    ),
    (
        frozenset({MatchReason.CORRELATION_ID}),
        EvidenceStrength.MEDIUM,
        0.4,
    ),
    (
        frozenset({MatchReason.TRACE_ID}),
        EvidenceStrength.MEDIUM,
        0.4,
    ),
    (
        frozenset({MatchReason.QUERY_TERM}),
        EvidenceStrength.WEAK,
        0.2,
    ),
)

class MatchedLogLine(BaseModel):
    log_line: ParsedLogRecord
    source_file: Path
    line_number: int
    match_reasons: list[MatchReason] = Field(default_factory=list)


def _contains_any_keyword(
    message: str,
    keywords: list[str],
) -> bool:
    normalized_message = message.lower()

    return any(keyword.lower() in normalized_message for keyword in keywords)


def _get_matching_log_lines(
    *,
    data_root: Path,
    start_timestamp: datetime,
    end_timestamp: datetime,
    service: str,
    query_terms: list[str],
    correlation_id: str | None,
    trace_id: str | None,
) -> list[MatchedLogLine]:
    reader = LocalFileTelemetryReader(data_root)

    matched_log_lines: list[MatchedLogLine] = []
    for source_log in reader.read_logs(service=service):
        log_line = source_log.record
        if (
            log_line.service == service
            and start_timestamp <= log_line.timestamp <= end_timestamp
        ):
            match_reasons: list[MatchReason] = []

            if trace_id and log_line.trace_id == trace_id:
                match_reasons.append(MatchReason.TRACE_ID)

            if correlation_id and log_line.correlation_id == correlation_id:
                match_reasons.append(MatchReason.CORRELATION_ID)

            if query_terms and _contains_any_keyword(
                log_line.message, keywords=query_terms
            ):
                match_reasons.append(MatchReason.QUERY_TERM)

            if match_reasons:
                matched_log_lines.append(
                    MatchedLogLine(
                        log_line=log_line,
                        source_file=source_log.source_file,
                        line_number=source_log.line_number,
                        match_reasons=match_reasons,
                    )
                )

    return matched_log_lines


def _format_selection_reason(match_reasons: list[MatchReason]) -> str: ...


def _classify_matching_log_line(
    matching_log_line: MatchedLogLine,
) -> tuple[EvidenceStrength, float]:
    found_reasons = set(matching_log_line.match_reasons)

    for required_reasons, strength, relevance_score in LOG_CLASSIFICATION_RULES:
        if required_reasons <= found_reasons:
            return strength, relevance_score

    raise ValueError("matched log line has no match reasons")


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

    retrieved_evidence: list[RetrievedEvidence] = []

    matching_log_lines: list[MatchedLogLine] = _get_matching_log_lines(
        data_root=Path(request.data_root),
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
            selection_reason=_format_selection_reason(matching_log_line.match_reasons),
        )

        evidence_strength, relevance_score = _classify_matching_log_line(
            matching_log_line
        )

        retrieved_evidence.append(
            RetrievedEvidence(
                evidence=telemetry_evidence,
                citation=citation_metadata,
                strength=evidence_strength,
                relevance_score=relevance_score,
            )
        )

    return retrieved_evidence

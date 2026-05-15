from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from telemetry_agents.application.telemetry_parsing import (
    parse_log_line,
    ParsedLogRecord,
)
from telemetry_agents.domain import TelemetryEvidence
from telemetry_agents.shared.time import parse_utc_timestamp


class EvidenceStrength(StrEnum):
    STRONG = "strong"
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
    incident_id: str = Field(min_length=1)
    service: str = Field(min_length=1)
    query_terms: list[str] = Field(default_factory=list)
    start_timestamp: str = Field(min_length=1)
    end_timestamp: str = Field(min_length=1)
    correlation_id: str | None = None
    trace_id: str | None = None

class MatchReason(StrEnum):
    TIME_WINDOW = "time_window"
    CORRELATION_ID = "correlation_id"
    TRACE_ID = "trace_id"
    QUERY_TERM = "query_term"

def _contains_any_keyword(
    message: str,
    keywords: list[str],
) -> bool:
    normalized_message = message.lower()

    return any(keyword.lower() in normalized_message for keyword in keywords)


def _find_relevant_log_lines(
    *,
    data_root: Path,
    start_timestamp: datetime,
    end_timestamp: datetime,
    service: str,
    query_terms: list[str],
    correlation_id: str | None,
    trace_id: str | None,
) -> list[tuple[int, ParsedLogRecord]]:
    path = data_root / "logs" / f"{service}.log"

    relevant_log_lines: list[tuple[int, ParsedLogRecord]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            cleaned_raw_line = raw_line.strip()

            if not cleaned_raw_line:
                continue

            log_line = parse_log_line(cleaned_raw_line)
            if (
                log_line.service == service
                and (not trace_id or log_line.trace_id == trace_id)
                and (not correlation_id or log_line.correlation_id == correlation_id)
                and (start_timestamp <= log_line.timestamp <= end_timestamp)
                and (
                    not query_terms
                    or _contains_any_keyword(log_line.message, keywords=query_terms)
                )
            ):
                relevant_log_lines.append((line_number, log_line))

    return relevant_log_lines


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

    _find_relevant_log_lines(
        data_root=Path("sample_data"),
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        service=request.service,
        query_terms=request.query_terms,
        correlation_id=request.correlation_id,
        trace_id=request.trace_id,
    )


#     raise NotImplementedError("Phase 7 exercise: implement deterministic evidence retrieval")
#
# class ParsedLogRecord(BaseModel):
#     timestamp: datetime
#     level: str = Field(min_length=1)
#     service: str = Field(min_length=1)
#     message: str = Field(min_length=1)
#     correlation_id: str | None = None
#     trace_id: str | None = None
#     exception_type: str | None = None
#
#
# class ParsedTraceSpan(BaseModel):
#     timestamp: datetime
#     trace_id: str = Field(min_length=1)
#     span_id: str = Field(min_length=1)
#     service: str = Field(min_length=1)
#     operation: str = Field(min_length=1)
#     duration_ms: int = Field(ge=0)
#     status: str = Field(min_length=1)
#
#
# class ParsedMetricSample(BaseModel):
#     timestamp: datetime
#     service: str = Field(min_length=1)
#     metric_name: str = Field(min_length=1)
#     value: float
#
#
# class ParsedDeploymentEvent(BaseModel):
#     timestamp: datetime
#     service: str = Field(min_length=1)
#     version: str = Field(min_length=1)
#     commit: str = Field(min_length=1)
#     change_summary: str = Field(min_length=1)

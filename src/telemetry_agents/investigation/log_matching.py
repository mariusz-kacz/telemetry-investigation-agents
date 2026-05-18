from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Iterable, Protocol

from pydantic import BaseModel, Field

from telemetry_agents.telemetry.models import ParsedLogRecord


class MatchReason(StrEnum):
    CORRELATION_ID = "correlation_id"
    TRACE_ID = "trace_id"
    QUERY_TERM = "query_term"


class MatchDetail(BaseModel):
    reason: MatchReason
    value: str


class MatchedLogLine(BaseModel):
    log_line: ParsedLogRecord
    source_file: Path
    line_number: int
    match_details: list[MatchDetail] = Field(default_factory=list)


class SourceLog(Protocol):
    source_file: Path
    line_number: int
    record: ParsedLogRecord


def _get_matching_query_terms(
    message: str,
    keywords: list[str],
) -> list[str]:
    normalized_message = message.lower()
    return [key for key in keywords if key.lower() in normalized_message]


def get_matching_log_lines(
    *,
    log_records: Iterable[SourceLog],
    start_timestamp: datetime,
    end_timestamp: datetime,
    service: str,
    query_terms: list[str],
    correlation_id: str | None,
    trace_id: str | None,
) -> list[MatchedLogLine]:
    matched_log_lines: list[MatchedLogLine] = []
    for source_log in log_records:
        log_line = source_log.record
        if (
            log_line.service == service
            and start_timestamp <= log_line.timestamp <= end_timestamp
        ):
            match_details: list[MatchDetail] = []

            if trace_id and log_line.trace_id == trace_id:
                match_details.append(
                    MatchDetail(reason=MatchReason.TRACE_ID, value=trace_id)
                )

            if correlation_id and log_line.correlation_id == correlation_id:
                match_details.append(
                    MatchDetail(reason=MatchReason.CORRELATION_ID, value=correlation_id)
                )

            if query_terms:
                matched_query_terms = _get_matching_query_terms(
                    log_line.message, keywords=query_terms
                )
                for query_term in matched_query_terms:
                    match_details.append(
                        MatchDetail(reason=MatchReason.QUERY_TERM, value=query_term)
                    )

            if match_details:
                matched_log_lines.append(
                    MatchedLogLine(
                        log_line=log_line,
                        source_file=source_log.source_file,
                        line_number=source_log.line_number,
                        match_details=match_details,
                    )
                )

    return matched_log_lines

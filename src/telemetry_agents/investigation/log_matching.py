from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Iterable, Protocol

from telemetry_agents.telemetry.models import ParsedLogRecord


class MatchReason(StrEnum):
    QUERY_TERM = "query_term"
    REQUEST_TRACE_ID = "request_trace_id"
    DISCOVERED_TRACE_ID = "discovered_trace_id"
    SEVERITY = "severity"


@dataclass(frozen=True)
class MatchDetail:
    reason: MatchReason
    value: str


@dataclass(frozen=True)
class MatchedLogLine:
    log_line: ParsedLogRecord
    source_file: Path
    line_number: int
    match_details: list[MatchDetail]


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


def _log_line_severity_high(level: str):
    return level in {"WARN", "ERROR", "CRITICAL"}


def get_trace_ids_from_seed_logs(
    *,
    log_records: Iterable[SourceLog],
    start_timestamp: datetime,
    end_timestamp: datetime,
    service: str,
    query_terms: list[str],
) -> set[str]:
    discovered_trace_ids: set[str] = set()
    for source_log in log_records:
        log_line = source_log.record
        if (
            log_line.service == service
            and start_timestamp <= log_line.timestamp <= end_timestamp
        ):
            if log_line.trace_id:
                if query_terms and _get_matching_query_terms(
                    log_line.message, keywords=query_terms
                ):
                    discovered_trace_ids.add(log_line.trace_id)
                elif _log_line_severity_high(log_line.level):
                    discovered_trace_ids.add(log_line.trace_id)
    return discovered_trace_ids


def get_matching_log_lines(
    *,
    log_records: Iterable[SourceLog],
    start_timestamp: datetime,
    end_timestamp: datetime,
    service: str,
    query_terms: list[str],
    trace_id: str | None,
    trace_ids_from_query_seed_logs: set[str],
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
                    MatchDetail(reason=MatchReason.REQUEST_TRACE_ID, value=trace_id)
                )

            matched_query_terms = _get_matching_query_terms(
                log_line.message, keywords=query_terms
            )

            for query_term in matched_query_terms:
                match_details.append(MatchDetail(MatchReason.QUERY_TERM, query_term))

            if _log_line_severity_high(log_line.level):
                match_details.append(MatchDetail(MatchReason.SEVERITY, log_line.level))

            if (
                not _log_line_severity_high(log_line.level)
                and not matched_query_terms
                and log_line.trace_id
                and log_line.trace_id in trace_ids_from_query_seed_logs
            ):
                match_details.append(
                    MatchDetail(MatchReason.DISCOVERED_TRACE_ID, log_line.trace_id)
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

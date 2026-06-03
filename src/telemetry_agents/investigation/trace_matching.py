from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Iterable, Protocol

from telemetry_agents.telemetry.models import ParsedTraceSpan


class TraceMatchReason(StrEnum):
    REQUEST_TRACE_ID = "request_trace_id"
    DISCOVERED_TRACE_ID = "discovered_trace_id"


@dataclass(frozen=True)
class MatchedTraceSpan:
    trace_span: ParsedTraceSpan
    match_reason: TraceMatchReason
    source_file: Path
    line_number: int


class SourceTraceSpan(Protocol):
    source_file: Path
    line_number: int
    record: ParsedTraceSpan


def get_matching_trace_spans(
    *,
    trace_span_records: Iterable[SourceTraceSpan],
    start_timestamp: datetime,
    end_timestamp: datetime,
    trace_id: str | None,
    trace_ids_from_query_seed_logs: set[str] | None = None,
) -> list[MatchedTraceSpan]:
    trace_ids_from_query_seed_logs = trace_ids_from_query_seed_logs or set()

    if trace_id is None and not trace_ids_from_query_seed_logs:
        return []

    matched_trace_spans: list[MatchedTraceSpan] = []
    for source_trace_span in trace_span_records:
        trace_span = source_trace_span.record
        if start_timestamp <= trace_span.timestamp <= end_timestamp:
            match_reason: TraceMatchReason | None = None
            if trace_span.trace_id == trace_id:
                match_reason = TraceMatchReason.REQUEST_TRACE_ID
            elif trace_span.trace_id in trace_ids_from_query_seed_logs:
                match_reason = TraceMatchReason.DISCOVERED_TRACE_ID

            if match_reason is not None:
                matched_trace_spans.append(
                    MatchedTraceSpan(
                        trace_span=trace_span,
                        match_reason=match_reason,
                        source_file=source_trace_span.source_file,
                        line_number=source_trace_span.line_number,
                    )
                )
    return matched_trace_spans

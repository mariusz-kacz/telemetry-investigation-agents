from datetime import datetime
from pathlib import Path
from typing import Iterable, Protocol

from pydantic import BaseModel

from telemetry_agents.telemetry.models import ParsedTraceSpan


class MatchedTraceSpan(BaseModel):
    trace_span: ParsedTraceSpan
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
    service: str,
    trace_id: str | None,
) -> list[MatchedTraceSpan]:
    if trace_id is None:
        return []

    matched_trace_spans: list[MatchedTraceSpan] = []
    for source_trace_span in trace_span_records:
        trace_span = source_trace_span.record
        if (
            trace_span.service == service
            and start_timestamp <= trace_span.timestamp <= end_timestamp
            and trace_span.trace_id == trace_id
        ):
            matched_trace_spans.append(
                MatchedTraceSpan(
                    trace_span=trace_span,
                    source_file=source_trace_span.source_file,
                    line_number=source_trace_span.line_number,
                )
            )

    return matched_trace_spans


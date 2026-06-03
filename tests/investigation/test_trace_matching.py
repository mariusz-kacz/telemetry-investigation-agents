from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from telemetry_agents.investigation.trace_matching import (
    TraceMatchReason,
    get_matching_trace_spans,
)
from telemetry_agents.telemetry.models import ParsedTraceSpan


@dataclass
class SourceTraceSpanStub:
    source_file: Path
    line_number: int
    record: ParsedTraceSpan


def _trace_span(
    *,
    timestamp: datetime,
    service: str = "checkout-api",
    trace_id: str = "trace-001",
) -> ParsedTraceSpan:
    return ParsedTraceSpan(
        timestamp=timestamp,
        trace_id=trace_id,
        span_id="span-001",
        service=service,
        operation="POST /checkout",
        duration_ms=2420,
        status="error",
    )


def test_get_matching_trace_spans_returns_strict_trace_matches_with_source_metadata() -> (
    None
):
    source_trace_span = SourceTraceSpanStub(
        source_file=Path("sample_data/traces/checkout-api.jsonl"),
        line_number=3,
        record=_trace_span(timestamp=datetime(2026, 5, 11, 10, 1, 13, tzinfo=UTC)),
    )

    matches = get_matching_trace_spans(
        trace_span_records=[source_trace_span],
        start_timestamp=datetime(2026, 5, 11, 10, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 5, 11, 10, 5, tzinfo=UTC),
        trace_id="trace-001",
    )

    assert len(matches) == 1
    assert matches[0].trace_span == source_trace_span.record
    assert matches[0].match_reason == TraceMatchReason.REQUEST_TRACE_ID
    assert matches[0].source_file == source_trace_span.source_file
    assert matches[0].line_number == source_trace_span.line_number


def test_get_matching_trace_spans_requires_trace_id_and_time_window() -> None:
    wrong_trace_id = SourceTraceSpanStub(
        source_file=Path("sample_data/traces/checkout-api.jsonl"),
        line_number=1,
        record=_trace_span(
            timestamp=datetime(2026, 5, 11, 10, 1, tzinfo=UTC),
            trace_id="trace-999",
        ),
    )
    outside_window = SourceTraceSpanStub(
        source_file=Path("sample_data/traces/checkout-api.jsonl"),
        line_number=2,
        record=_trace_span(timestamp=datetime(2026, 5, 11, 11, 0, tzinfo=UTC)),
    )

    matches = get_matching_trace_spans(
        trace_span_records=[wrong_trace_id, outside_window],
        start_timestamp=datetime(2026, 5, 11, 10, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 5, 11, 10, 5, tzinfo=UTC),
        trace_id="trace-001",
    )

    assert matches == []


def test_get_matching_trace_spans_includes_correlated_dependency_spans() -> None:
    dependency_span = SourceTraceSpanStub(
        source_file=Path("sample_data/traces/checkout-api.jsonl"),
        line_number=2,
        record=_trace_span(
            timestamp=datetime(2026, 5, 11, 10, 1, tzinfo=UTC),
            service="shipping-rate-service",
        ),
    )

    matches = get_matching_trace_spans(
        trace_span_records=[dependency_span],
        start_timestamp=datetime(2026, 5, 11, 10, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 5, 11, 10, 5, tzinfo=UTC),
        trace_id="trace-001",
    )

    assert len(matches) == 1
    assert matches[0].trace_span.service == "shipping-rate-service"


def test_get_matching_trace_spans_returns_empty_when_trace_id_is_missing() -> None:
    source_trace_span = SourceTraceSpanStub(
        source_file=Path("sample_data/traces/checkout-api.jsonl"),
        line_number=1,
        record=_trace_span(timestamp=datetime(2026, 5, 11, 10, 1, tzinfo=UTC)),
    )

    matches = get_matching_trace_spans(
        trace_span_records=[source_trace_span],
        start_timestamp=datetime(2026, 5, 11, 10, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 5, 11, 10, 5, tzinfo=UTC),
        trace_id=None,
    )

    assert matches == []


def test_get_matching_trace_spans_matches_discovered_trace_ids() -> None:
    discovered_trace_span = SourceTraceSpanStub(
        source_file=Path("sample_data/traces/checkout-api.jsonl"),
        line_number=4,
        record=_trace_span(
            timestamp=datetime(2026, 5, 11, 10, 1, tzinfo=UTC),
            trace_id="trace-discovered",
        ),
    )

    matches = get_matching_trace_spans(
        trace_span_records=[discovered_trace_span],
        start_timestamp=datetime(2026, 5, 11, 10, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 5, 11, 10, 5, tzinfo=UTC),
        trace_id=None,
        trace_ids_from_query_seed_logs={"trace-discovered"},
    )

    assert len(matches) == 1
    assert matches[0].match_reason == TraceMatchReason.DISCOVERED_TRACE_ID


def test_get_matching_trace_spans_prefers_request_reason_when_trace_id_is_both_request_and_discovered() -> (
    None
):
    trace_span = SourceTraceSpanStub(
        source_file=Path("sample_data/traces/checkout-api.jsonl"),
        line_number=5,
        record=_trace_span(
            timestamp=datetime(2026, 5, 11, 10, 1, tzinfo=UTC),
            trace_id="trace-001",
        ),
    )

    matches = get_matching_trace_spans(
        trace_span_records=[trace_span],
        start_timestamp=datetime(2026, 5, 11, 10, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 5, 11, 10, 5, tzinfo=UTC),
        trace_id="trace-001",
        trace_ids_from_query_seed_logs={"trace-001"},
    )

    assert len(matches) == 1
    assert matches[0].match_reason == TraceMatchReason.REQUEST_TRACE_ID

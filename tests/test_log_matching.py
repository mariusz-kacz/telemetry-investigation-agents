from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from telemetry_agents.application.log_matching import (
    MatchReason,
    get_matching_log_lines,
)
from telemetry_agents.telemetry.models import ParsedLogRecord


@dataclass
class SourceLogStub:
    source_file: Path
    line_number: int
    record: ParsedLogRecord


def _log_record(
    *,
    timestamp: datetime,
    service: str = "checkout-api",
    message: str = "DatabaseTimeoutException while calling orders-db",
    correlation_id: str = "cart-123",
    trace_id: str = "trace-001",
) -> ParsedLogRecord:
    return ParsedLogRecord(
        timestamp=timestamp,
        level="ERROR",
        service=service,
        message=message,
        correlation_id=correlation_id,
        trace_id=trace_id,
    )


def test_get_matching_log_lines_returns_matches_with_source_metadata() -> None:
    source_log = SourceLogStub(
        source_file=Path("sample_data/logs/checkout-api.log"),
        line_number=7,
        record=_log_record(timestamp=datetime(2026, 5, 11, 10, 1, 13, tzinfo=UTC)),
    )

    matches = get_matching_log_lines(
        log_records=[source_log],
        start_timestamp=datetime(2026, 5, 11, 10, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 5, 11, 10, 5, tzinfo=UTC),
        service="checkout-api",
        query_terms=["database", "timeout"],
        correlation_id="cart-123",
        trace_id="trace-001",
    )

    assert len(matches) == 1
    assert matches[0].source_file == source_log.source_file
    assert matches[0].line_number == source_log.line_number
    assert {detail.reason for detail in matches[0].match_details} == {
        MatchReason.CORRELATION_ID,
        MatchReason.TRACE_ID,
        MatchReason.QUERY_TERM,
    }
    assert {detail.value for detail in matches[0].match_details} >= {
        "cart-123",
        "trace-001",
        "database",
        "timeout",
    }


def test_get_matching_log_lines_filters_service_time_window_and_non_matches() -> None:
    in_window_non_matching = SourceLogStub(
        source_file=Path("sample_data/logs/checkout-api.log"),
        line_number=1,
        record=_log_record(
            timestamp=datetime(2026, 5, 11, 10, 1, tzinfo=UTC),
            message="Health check succeeded",
            correlation_id="other-cart",
            trace_id="other-trace",
        ),
    )
    wrong_service = SourceLogStub(
        source_file=Path("sample_data/logs/payments-api.log"),
        line_number=2,
        record=_log_record(
            timestamp=datetime(2026, 5, 11, 10, 1, tzinfo=UTC),
            service="payments-api",
        ),
    )
    outside_window = SourceLogStub(
        source_file=Path("sample_data/logs/checkout-api.log"),
        line_number=3,
        record=_log_record(timestamp=datetime(2026, 5, 11, 11, 0, tzinfo=UTC)),
    )

    matches = get_matching_log_lines(
        log_records=[in_window_non_matching, wrong_service, outside_window],
        start_timestamp=datetime(2026, 5, 11, 10, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 5, 11, 10, 5, tzinfo=UTC),
        service="checkout-api",
        query_terms=["database"],
        correlation_id="cart-123",
        trace_id="trace-001",
    )

    assert matches == []

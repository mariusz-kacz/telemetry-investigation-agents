from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from telemetry_agents.investigation.log_matching import (
    MatchReason,
    get_matching_log_lines,
    get_trace_ids_from_seed_logs,
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
    trace_id: str = "trace-001",
    level: str = "INFO",
) -> ParsedLogRecord:
    return ParsedLogRecord(
        timestamp=timestamp,
        level=level,
        service=service,
        message=message,
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
        trace_id="trace-001",
        trace_ids_from_query_seed_logs=set(),
    )

    assert len(matches) == 1
    assert matches[0].source_file == source_log.source_file
    assert matches[0].line_number == source_log.line_number
    assert {detail.reason for detail in matches[0].match_details} == {
        MatchReason.REQUEST_TRACE_ID,
        MatchReason.QUERY_TERM,
    }
    assert {detail.value for detail in matches[0].match_details} >= {
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
        trace_id="trace-001",
        trace_ids_from_query_seed_logs=set(),
    )

    assert matches == []


def test_get_trace_ids_from_seed_logs_discovers_case_insensitive_query_matches() -> (
    None
):
    matching_seed = SourceLogStub(
        source_file=Path("sample_data/logs/checkout-api.log"),
        line_number=1,
        record=_log_record(
            timestamp=datetime(2026, 5, 11, 10, 1, tzinfo=UTC),
            message="Timeout waiting for orders-db",
            trace_id="trace-seed",
        ),
    )
    wrong_service = SourceLogStub(
        source_file=Path("sample_data/logs/payments-api.log"),
        line_number=2,
        record=_log_record(
            timestamp=datetime(2026, 5, 11, 10, 1, tzinfo=UTC),
            service="payments-api",
            message="timeout waiting for processor",
            trace_id="trace-wrong-service",
        ),
    )
    outside_window = SourceLogStub(
        source_file=Path("sample_data/logs/checkout-api.log"),
        line_number=3,
        record=_log_record(
            timestamp=datetime(2026, 5, 11, 11, 0, tzinfo=UTC),
            message="timeout waiting for orders-db",
            trace_id="trace-outside-window",
        ),
    )

    trace_ids = get_trace_ids_from_seed_logs(
        log_records=[matching_seed, wrong_service, outside_window],
        start_timestamp=datetime(2026, 5, 11, 10, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 5, 11, 10, 5, tzinfo=UTC),
        service="checkout-api",
        query_terms=["timeout"],
    )

    assert trace_ids == {"trace-seed"}


def test_get_trace_ids_from_seed_logs_returns_empty_without_query_terms_or_severity() -> (
    None
):
    matching_seed = SourceLogStub(
        source_file=Path("sample_data/logs/checkout-api.log"),
        line_number=1,
        record=_log_record(
            timestamp=datetime(2026, 5, 11, 10, 1, tzinfo=UTC),
            message="timeout waiting for orders-db",
            trace_id="trace-seed",
        ),
    )

    trace_ids = get_trace_ids_from_seed_logs(
        log_records=[matching_seed],
        start_timestamp=datetime(2026, 5, 11, 10, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 5, 11, 10, 5, tzinfo=UTC),
        service="checkout-api",
        query_terms=[],
    )

    assert trace_ids == set()


def test_get_matching_log_lines_distinguishes_query_seed_and_discovered_trace_matches() -> (
    None
):
    query_seed = SourceLogStub(
        source_file=Path("sample_data/logs/checkout-api.log"),
        line_number=1,
        record=_log_record(
            timestamp=datetime(2026, 5, 11, 10, 1, tzinfo=UTC),
            message="timeout waiting for orders-db",
            trace_id="trace-seed",
        ),
    )
    companion_log = SourceLogStub(
        source_file=Path("sample_data/logs/checkout-api.log"),
        line_number=2,
        record=_log_record(
            timestamp=datetime(2026, 5, 11, 10, 2, tzinfo=UTC),
            message="request accepted",
            trace_id="trace-seed",
        ),
    )

    matches = get_matching_log_lines(
        log_records=[query_seed, companion_log],
        start_timestamp=datetime(2026, 5, 11, 10, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 5, 11, 10, 5, tzinfo=UTC),
        service="checkout-api",
        query_terms=["timeout"],
        trace_id=None,
        trace_ids_from_query_seed_logs={"trace-seed"},
    )

    match_reasons_by_line = {
        match.line_number: {detail.reason for detail in match.match_details}
        for match in matches
    }
    assert match_reasons_by_line == {
        1: {MatchReason.QUERY_TERM},
        2: {MatchReason.DISCOVERED_TRACE_ID},
    }


def test_get_matching_log_lines_matches_warn_or_higher_severity_logs() -> None:
    warn_log = SourceLogStub(
        source_file=Path("sample_data/logs/checkout-api.log"),
        line_number=1,
        record=_log_record(
            timestamp=datetime(2026, 5, 11, 10, 1, tzinfo=UTC),
            level="WARN",
            message="Shipping rate lookup took 1750ms",
            trace_id="trace-shipping",
        ),
    )
    error_log = SourceLogStub(
        source_file=Path("sample_data/logs/checkout-api.log"),
        line_number=2,
        record=_log_record(
            timestamp=datetime(2026, 5, 11, 10, 2, tzinfo=UTC),
            level="ERROR",
            message="Checkout request exceeded client timeout",
            trace_id="trace-timeout",
        ),
    )
    critical_log = SourceLogStub(
        source_file=Path("sample_data/logs/checkout-api.log"),
        line_number=3,
        record=_log_record(
            timestamp=datetime(2026, 5, 11, 10, 3, tzinfo=UTC),
            level="CRITICAL",
            message="Checkout API unavailable",
            trace_id="trace-critical",
        ),
    )
    info_log = SourceLogStub(
        source_file=Path("sample_data/logs/checkout-api.log"),
        line_number=4,
        record=_log_record(
            timestamp=datetime(2026, 5, 11, 10, 4, tzinfo=UTC),
            level="INFO",
            message="Checkout request completed",
            trace_id="trace-info",
        ),
    )

    matches = get_matching_log_lines(
        log_records=[warn_log, error_log, critical_log, info_log],
        start_timestamp=datetime(2026, 5, 11, 10, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 5, 11, 10, 6, tzinfo=UTC),
        service="checkout-api",
        query_terms=[],
        trace_id=None,
        trace_ids_from_query_seed_logs=set(),
    )

    severity_matches_by_line = {
        match.line_number: {detail.reason for detail in match.match_details}
        for match in matches
    }
    severity_values_by_line = {
        match.line_number: {detail.value for detail in match.match_details}
        for match in matches
    }

    assert severity_matches_by_line == {
        1: {MatchReason.SEVERITY},
        2: {MatchReason.SEVERITY},
        3: {MatchReason.SEVERITY},
    }
    assert severity_values_by_line == {
        1: {"WARN"},
        2: {"ERROR"},
        3: {"CRITICAL"},
    }


def test_get_matching_log_lines_combines_severity_with_other_match_reasons() -> None:
    source_log = SourceLogStub(
        source_file=Path("sample_data/logs/checkout-api.log"),
        line_number=7,
        record=_log_record(
            timestamp=datetime(2026, 5, 11, 10, 1, 13, tzinfo=UTC),
            level="WARN",
            message="Timeout waiting for orders-db",
            trace_id="trace-001",
        ),
    )

    matches = get_matching_log_lines(
        log_records=[source_log],
        start_timestamp=datetime(2026, 5, 11, 10, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 5, 11, 10, 5, tzinfo=UTC),
        service="checkout-api",
        query_terms=["timeout"],
        trace_id="trace-001",
        trace_ids_from_query_seed_logs=set(),
    )

    assert len(matches) == 1
    assert {detail.reason for detail in matches[0].match_details} == {
        MatchReason.REQUEST_TRACE_ID,
        MatchReason.QUERY_TERM,
        MatchReason.SEVERITY,
    }

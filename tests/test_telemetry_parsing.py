from datetime import UTC, datetime

import pytest

from telemetry_agents.application.telemetry_parsing import (
    ParsedLogRecord,
    filter_by_time_window,
    filter_logs_by_correlation_id,
    parse_deployment_event_json,
    parse_log_line,
    parse_metric_sample_json,
    parse_trace_span_json,
)


def test_parse_log_line_normalizes_structured_log_fields() -> None:
    record = parse_log_line(
        "2026-05-11T10:01:13Z ERROR checkout-api "
        "correlation_id=cart-123 trace_id=trace-001 "
        "DatabaseTimeoutException while calling orders-db"
    )

    assert record.timestamp == datetime(2026, 5, 11, 10, 1, 13, tzinfo=UTC)
    assert record.level == "ERROR"
    assert record.service == "checkout-api"
    assert record.correlation_id == "cart-123"
    assert record.trace_id == "trace-001"
    assert record.exception_type == "DatabaseTimeoutException"
    assert record.message == "DatabaseTimeoutException while calling orders-db"


def test_parse_log_line_rejects_missing_correlation_id() -> None:
    with pytest.raises(ValueError):
        parse_log_line(
            "2026-05-11T10:01:13Z ERROR checkout-api "
            "trace_id=trace-001 DatabaseTimeoutException while calling orders-db"
        )


def test_parse_log_line_rejects_empty_correlation_id() -> None:
    with pytest.raises(ValueError):
        parse_log_line(
            "2026-05-11T10:01:13Z ERROR checkout-api "
            "correlation_id= trace_id=trace-001 DatabaseTimeoutException while calling orders-db"
        )


def test_parse_log_line_rejects_missing_trace_id() -> None:
    with pytest.raises(ValueError):
        parse_log_line(
            "2026-05-11T10:01:13Z ERROR checkout-api "
            "correlation_id=cart-123 DatabaseTimeoutException while calling orders-db"
        )


def test_parse_log_line_rejects_empty_trace_id() -> None:
    with pytest.raises(ValueError):
        parse_log_line(
            "2026-05-11T10:01:13Z ERROR checkout-api "
            "correlation_id=cart-123 trace_id= DatabaseTimeoutException while calling orders-db"
        )


def test_parse_log_line_rejects_invalid_timestamp() -> None:
    with pytest.raises(ValueError):
        parse_log_line(
            "not-a-timestamp ERROR checkout-api correlation_id=cart-123 "
            "trace_id=trace-001 DatabaseTimeoutException while calling orders-db"
        )


def test_parse_log_line_allows_message_without_exception() -> None:
    record = parse_log_line(
        "2026-05-11T10:01:13Z INFO checkout-api "
        "correlation_id=cart-123 trace_id=trace-001 request completed successfully"
    )

    assert record.exception_type is None
    assert record.message == "request completed successfully"


def test_parse_trace_span_json_normalizes_trace_fields() -> None:
    record = parse_trace_span_json(
        '{"trace_id":"trace-001","span_id":"span-001","service":"checkout-api",'
        '"operation":"POST /checkout","duration_ms":2420,"status":"error",'
        '"timestamp":"2026-05-11T10:01:13Z"}'
    )

    assert record.trace_id == "trace-001"
    assert record.span_id == "span-001"
    assert record.duration_ms == 2420
    assert record.status == "error"
    assert record.timestamp == datetime(2026, 5, 11, 10, 1, 13, tzinfo=UTC)


def test_parse_metric_sample_json_normalizes_metric_fields() -> None:
    record = parse_metric_sample_json(
        '{"timestamp":"2026-05-11T10:01:00Z","service":"checkout-api",'
        '"metric_name":"p95_latency_ms","value":2400}'
    )

    assert record.service == "checkout-api"
    assert record.metric_name == "p95_latency_ms"
    assert record.value == 2400
    assert record.timestamp == datetime(2026, 5, 11, 10, 1, tzinfo=UTC)


def test_parse_deployment_event_json_normalizes_deployment_fields() -> None:
    record = parse_deployment_event_json(
        '{"timestamp":"2026-05-11T09:45:00Z","service":"checkout-api",'
        '"version":"2026.05.11.1","commit":"abc1234",'
        '"change_summary":"Updated database retry timeout configuration."}'
    )

    assert record.service == "checkout-api"
    assert record.version == "2026.05.11.1"
    assert record.commit == "abc1234"
    assert "retry timeout" in record.change_summary
    assert record.timestamp == datetime(2026, 5, 11, 9, 45, tzinfo=UTC)


def test_time_window_filter_is_inclusive() -> None:
    before = ParsedLogRecord(
        timestamp=datetime(2026, 5, 11, 9, 59, tzinfo=UTC),
        level="INFO",
        service="checkout-api",
        message="before",
    )
    inside = ParsedLogRecord(
        timestamp=datetime(2026, 5, 11, 10, 1, tzinfo=UTC),
        level="ERROR",
        service="checkout-api",
        message="inside",
    )

    filtered = filter_by_time_window(
        [before, inside],
        start_timestamp=datetime(2026, 5, 11, 10, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 5, 11, 10, 5, tzinfo=UTC),
    )

    assert filtered == [inside]


def test_correlation_id_filter_returns_matching_logs_only() -> None:
    matching = ParsedLogRecord(
        timestamp=datetime(2026, 5, 11, 10, 1, tzinfo=UTC),
        level="ERROR",
        service="checkout-api",
        message="timeout",
        correlation_id="cart-123",
    )
    unrelated = ParsedLogRecord(
        timestamp=datetime(2026, 5, 11, 10, 2, tzinfo=UTC),
        level="ERROR",
        service="checkout-api",
        message="timeout",
        correlation_id="cart-999",
    )

    assert filter_logs_by_correlation_id(
        [matching, unrelated],
        correlation_id="cart-123",
    ) == [matching]


def test_malformed_trace_json_is_rejected() -> None:
    with pytest.raises(ValueError):
        parse_trace_span_json('{"trace_id": "trace-001"')


def test_trace_span_rejects_missing_span_id() -> None:
    with pytest.raises(ValueError):
        parse_trace_span_json(
            '{"trace_id":"trace-001","service":"checkout-api",'
            '"operation":"POST /checkout","duration_ms":2420,"status":"error",'
            '"timestamp":"2026-05-11T10:01:13Z"}'
        )


def test_metric_sample_rejects_missing_metric_name() -> None:
    with pytest.raises(ValueError):
        parse_metric_sample_json(
            '{"timestamp":"2026-05-11T10:01:00Z","service":"checkout-api","value":2400}'
        )


def test_metric_sample_rejects_non_numeric_value() -> None:
    with pytest.raises(ValueError):
        parse_metric_sample_json(
            '{"timestamp":"2026-05-11T10:01:00Z","service":"checkout-api",'
            '"metric_name":"p95_latency_ms","value":"high"}'
        )


def test_deployment_event_rejects_missing_commit() -> None:
    with pytest.raises(ValueError):
        parse_deployment_event_json(
            '{"timestamp":"2026-05-11T09:45:00Z","service":"checkout-api",'
            '"version":"2026.05.11.1",'
            '"change_summary":"Updated database retry timeout configuration."}'
        )

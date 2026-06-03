import json
import re
from typing import Any

from telemetry_agents.shared.time import parse_utc_timestamp
from telemetry_agents.telemetry.models import (
    ParsedLogRecord,
    ParsedTraceSpan,
    ParsedMetricSample,
)

EXCEPTION_PATTERN = re.compile(r"\b([A-Z][A-Za-z0-9]+Exception)\b")


def _parse_json_object(line: str, label: str) -> dict[str, Any]:
    try:
        record = json.loads(line)
    except ValueError as exc:
        raise ValueError(f"{label} JSON could not be parsed") from exc

    if not isinstance(record, dict):
        raise ValueError(f"{label} JSON could not be parsed")

    return record


def _required_string(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


def parse_log_line(line: str) -> ParsedLogRecord:
    """Parse one synthetic structured log line into a normalized record."""
    tokens = line.split()

    if len(tokens) < 6:
        raise ValueError("Log line could not be parsed")

    # Synthetic logs use: timestamp level service key=value message...
    timestamp_text = tokens[0]
    log_level = tokens[1]
    service = tokens[2]

    try:
        timestamp = parse_utc_timestamp(timestamp_text)
    except ValueError as exc:
        raise ValueError("Wrong timestamp value") from exc

    metadata = {}
    message_parts = []

    for token in tokens[3:]:
        if "=" in token:
            key, value = token.split("=", 1)
            metadata[key] = value
        else:
            message_parts.append(token)

    message = " ".join(message_parts)

    exception_match = EXCEPTION_PATTERN.search(message)
    exception_type = exception_match.group(1) if exception_match else None

    trace_id = _required_string(metadata, "trace_id")

    return ParsedLogRecord(
        timestamp=timestamp,
        level=log_level,
        service=service,
        trace_id=trace_id,
        exception_type=exception_type,
        message=message,
    )


def parse_trace_span_json(line: str) -> ParsedTraceSpan:
    """Parse one JSONL trace span into a normalized record."""
    record = _parse_json_object(line, "Trace span")

    try:
        timestamp = parse_utc_timestamp(_required_string(record, "timestamp"))
    except ValueError as exc:
        raise ValueError("Wrong timestamp value") from exc

    trace_id = _required_string(record, "trace_id")
    span_id = _required_string(record, "span_id")
    service = _required_string(record, "service")
    operation = _required_string(record, "operation")
    status = _required_string(record, "status")

    duration_ms = record.get("duration_ms")
    if isinstance(duration_ms, bool) or not isinstance(duration_ms, int):
        raise ValueError("Wrong duration value")

    if duration_ms < 0:
        raise ValueError("Wrong duration value")

    return ParsedTraceSpan(
        timestamp=timestamp,
        trace_id=trace_id,
        span_id=span_id,
        service=service,
        operation=operation,
        duration_ms=duration_ms,
        status=status,
    )


def parse_metric_sample_json(line: str) -> ParsedMetricSample:
    """Parse one JSONL metric sample into a normalized record."""
    record = _parse_json_object(line, "Metric sample")

    try:
        timestamp = parse_utc_timestamp(_required_string(record, "timestamp"))
    except ValueError as exc:
        raise ValueError("Wrong timestamp value") from exc

    service = _required_string(record, "service")
    metric_name = _required_string(record, "metric_name")

    value = record.get("value")
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("Wrong metric value")
    value = float(value)

    return ParsedMetricSample(
        timestamp=timestamp,
        service=service,
        metric_name=metric_name,
        value=value,
    )

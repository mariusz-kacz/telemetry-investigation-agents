import json
import re
from datetime import datetime
from typing import Any, Protocol

from pydantic import BaseModel, Field


class Timestamped(Protocol):
    timestamp: datetime


class ParsedLogRecord(BaseModel):
    timestamp: datetime
    level: str = Field(min_length=1)
    service: str = Field(min_length=1)
    message: str = Field(min_length=1)
    correlation_id: str | None = None
    trace_id: str | None = None
    exception_type: str | None = None


class ParsedTraceSpan(BaseModel):
    timestamp: datetime
    trace_id: str = Field(min_length=1)
    span_id: str = Field(min_length=1)
    service: str = Field(min_length=1)
    operation: str = Field(min_length=1)
    duration_ms: int = Field(ge=0)
    status: str = Field(min_length=1)


class ParsedMetricSample(BaseModel):
    timestamp: datetime
    service: str = Field(min_length=1)
    metric_name: str = Field(min_length=1)
    value: float


class ParsedDeploymentEvent(BaseModel):
    timestamp: datetime
    service: str = Field(min_length=1)
    version: str = Field(min_length=1)
    commit: str = Field(min_length=1)
    change_summary: str = Field(min_length=1)


EXCEPTION_PATTERN = re.compile(r"\b([A-Z][A-Za-z0-9]+Exception)\b")


def _parse_utc_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


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

    # Synthetic logs use: timestamp level service key=value key=value message...
    timestamp_text = tokens[0]
    log_level = tokens[1]
    service = tokens[2]

    try:
        timestamp = _parse_utc_timestamp(timestamp_text)
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

    correlation_id = _required_string(metadata, "correlation_id")
    trace_id = _required_string(metadata, "trace_id")

    return ParsedLogRecord(
        timestamp=timestamp,
        level=log_level,
        service=service,
        correlation_id=correlation_id,
        trace_id=trace_id,
        exception_type=exception_type,
        message=message,
    )


def parse_trace_span_json(line: str) -> ParsedTraceSpan:
    """Parse one JSONL trace span into a normalized record."""
    record = _parse_json_object(line, "Trace span")

    try:
        timestamp = _parse_utc_timestamp(_required_string(record, "timestamp"))
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
        timestamp = _parse_utc_timestamp(_required_string(record, "timestamp"))
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


def parse_deployment_event_json(line: str) -> ParsedDeploymentEvent:
    """Parse one JSONL deployment event into a normalized record."""
    record = _parse_json_object(line, "Deployment event")

    try:
        timestamp = _parse_utc_timestamp(_required_string(record, "timestamp"))
    except ValueError as exc:
        raise ValueError("Wrong timestamp value") from exc

    service = _required_string(record, "service")
    version = _required_string(record, "version")
    commit = _required_string(record, "commit")
    change_summary = _required_string(record, "change_summary")

    return ParsedDeploymentEvent(
        timestamp=timestamp,
        service=service,
        version=version,
        commit=commit,
        change_summary=change_summary,
    )


def filter_by_time_window[T: Timestamped](
    records: list[T],
    *,
    start_timestamp: datetime,
    end_timestamp: datetime,
) -> list[T]:
    """Return records whose timestamp falls inside the inclusive time window."""
    return [
        record
        for record in records
        if start_timestamp <= record.timestamp and end_timestamp >= record.timestamp
    ]


def filter_logs_by_correlation_id(
    records: list[ParsedLogRecord],
    *,
    correlation_id: str,
) -> list[ParsedLogRecord]:
    """Return log records that match the supplied correlation ID."""
    return [record for record in records if record.correlation_id == correlation_id]

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from telemetry_agents.application.metrics_matching import get_matching_metric_samples
from telemetry_agents.telemetry.models import ParsedMetricSample


@dataclass
class SourceMetricSampleStub:
    source_file: Path
    line_number: int
    record: ParsedMetricSample


def _metric_sample(
    *,
    timestamp: datetime,
    service: str = "checkout-api",
) -> ParsedMetricSample:
    return ParsedMetricSample(
        timestamp=timestamp,
        service=service,
        metric_name="p95_latency_ms",
        value=2400,
    )


def test_get_matching_metric_samples_returns_matches_with_source_metadata() -> None:
    source_metric_sample = SourceMetricSampleStub(
        source_file=Path("sample_data/metrics/checkout-api.jsonl"),
        line_number=4,
        record=_metric_sample(timestamp=datetime(2026, 5, 11, 10, 1, tzinfo=UTC)),
    )

    matches = get_matching_metric_samples(
        metric_sample_records=[source_metric_sample],
        start_timestamp=datetime(2026, 5, 11, 10, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 5, 11, 10, 5, tzinfo=UTC),
        service="checkout-api",
    )

    assert len(matches) == 1
    assert matches[0].metric_sample == source_metric_sample.record
    assert matches[0].source_file == source_metric_sample.source_file
    assert matches[0].line_number == source_metric_sample.line_number


def test_get_matching_metric_samples_requires_service_and_time_window() -> None:
    wrong_service = SourceMetricSampleStub(
        source_file=Path("sample_data/metrics/payments-api.jsonl"),
        line_number=1,
        record=_metric_sample(
            timestamp=datetime(2026, 5, 11, 10, 1, tzinfo=UTC),
            service="payments-api",
        ),
    )
    outside_window = SourceMetricSampleStub(
        source_file=Path("sample_data/metrics/checkout-api.jsonl"),
        line_number=2,
        record=_metric_sample(timestamp=datetime(2026, 5, 11, 11, 0, tzinfo=UTC)),
    )

    matches = get_matching_metric_samples(
        metric_sample_records=[wrong_service, outside_window],
        start_timestamp=datetime(2026, 5, 11, 10, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 5, 11, 10, 5, tzinfo=UTC),
        service="checkout-api",
    )

    assert matches == []

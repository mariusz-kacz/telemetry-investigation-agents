from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Protocol

from telemetry_agents.telemetry.models import ParsedMetricSample


@dataclass(frozen=True)
class MatchedMetricSample:
    metric_sample: ParsedMetricSample
    source_file: Path
    line_number: int


class SourceMetricSample(Protocol):
    source_file: Path
    line_number: int
    record: ParsedMetricSample


def get_matching_metric_samples(
    *,
    metric_sample_records: Iterable[SourceMetricSample],
    start_timestamp: datetime,
    end_timestamp: datetime,
    service: str,
) -> list[MatchedMetricSample]:

    matched_metric_samples: list[MatchedMetricSample] = []
    for source_metric_sample in metric_sample_records:
        metric_sample = source_metric_sample.record
        if (
            metric_sample.service == service
            and start_timestamp <= metric_sample.timestamp <= end_timestamp
        ):
            matched_metric_samples.append(
                MatchedMetricSample(
                    metric_sample=metric_sample,
                    source_file=source_metric_sample.source_file,
                    line_number=source_metric_sample.line_number,
                )
            )

    return matched_metric_samples

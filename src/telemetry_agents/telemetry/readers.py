from pathlib import Path

from pydantic import BaseModel, Field

from telemetry_agents.telemetry.parsing import (
    ParsedLogRecord,
    ParsedMetricSample,
    ParsedTraceSpan,
    parse_log_line,
    parse_metric_sample_json,
    parse_trace_span_json,
)


class SourceLogRecord(BaseModel):
    source_file: Path
    line_number: int = Field(ge=1)
    record: ParsedLogRecord


class SourceTraceSpan(BaseModel):
    source_file: Path
    line_number: int = Field(ge=1)
    record: ParsedTraceSpan


class SourceMetricSample(BaseModel):
    source_file: Path
    line_number: int = Field(ge=1)
    record: ParsedMetricSample


class LocalFileTelemetryReader:
    """Read local synthetic telemetry and preserve source location metadata."""

    def __init__(self, data_root: Path) -> None:
        self.data_root = data_root

    def read_logs(self, *, service: str) -> list[SourceLogRecord]:
        file_path = self.data_root / "logs" / f"{service}.log"
        records: list[SourceLogRecord] = []

        with file_path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                cleaned_line = line.strip()
                if not cleaned_line:
                    continue

                records.append(
                    SourceLogRecord(
                        source_file=file_path,
                        line_number=line_number,
                        record=parse_log_line(cleaned_line),
                    )
                )

        return records

    def read_traces(self, *, service: str) -> list[SourceTraceSpan]:
        file_path = self.data_root / "traces" / f"{service}.jsonl"
        records: list[SourceTraceSpan] = []

        with file_path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                cleaned_line = line.strip()
                if not cleaned_line:
                    continue

                records.append(
                    SourceTraceSpan(
                        source_file=file_path,
                        line_number=line_number,
                        record=parse_trace_span_json(cleaned_line),
                    )
                )

        return records

    def read_metrics(self, *, service: str) -> list[SourceMetricSample]:
        file_path = self.data_root / "metrics" / f"{service}.jsonl"
        records: list[SourceMetricSample] = []

        with file_path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                cleaned_line = line.strip()
                if not cleaned_line:
                    continue

                records.append(
                    SourceMetricSample(
                        source_file=file_path,
                        line_number=line_number,
                        record=parse_metric_sample_json(cleaned_line),
                    )
                )

        return records


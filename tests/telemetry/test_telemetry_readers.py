from pathlib import Path

from telemetry_agents.telemetry.readers import LocalFileTelemetryReader
from telemetry_agents.shared.paths import SAMPLE_DATA_DIR


def test_local_file_reader_reads_utf8_bom_trace_file(tmp_path: Path) -> None:
    traces_dir = tmp_path / "traces"
    traces_dir.mkdir()
    (traces_dir / "checkout-api.jsonl").write_text(
        '\ufeff{"timestamp":"2026-05-13T14:34:12Z",'
        '"trace_id":"trace-checkout-9301",'
        '"span_id":"span-9301-01",'
        '"service":"checkout-api",'
        '"operation":"POST /checkout",'
        '"duration_ms":221,'
        '"status":"ok"}\n',
        encoding="utf-8",
    )

    reader = LocalFileTelemetryReader(tmp_path)

    traces = reader.read_traces(service="checkout-api")

    assert traces[0].record.trace_id == "trace-checkout-9301"


def test_local_file_reader_reads_logs_with_source_location() -> None:
    reader = LocalFileTelemetryReader(SAMPLE_DATA_DIR)

    logs = reader.read_logs(service="checkout-api")

    assert logs
    assert logs[0].source_file == SAMPLE_DATA_DIR / "logs" / "checkout-api.log"
    assert logs[0].line_number == 1
    assert logs[0].record.service == "checkout-api"
    assert logs[0].record.trace_id == "trace-001"


def test_local_file_reader_reads_traces_with_source_location() -> None:
    reader = LocalFileTelemetryReader(SAMPLE_DATA_DIR)

    traces = reader.read_traces(service="checkout-api")

    assert traces
    assert traces[0].source_file == SAMPLE_DATA_DIR / "traces" / "checkout-api.jsonl"
    assert traces[0].line_number == 1
    assert traces[0].record.trace_id == "trace-001"


def test_local_file_reader_reads_metrics_with_source_location() -> None:
    reader = LocalFileTelemetryReader(SAMPLE_DATA_DIR)

    metrics = reader.read_metrics(service="checkout-api")

    assert metrics
    assert metrics[0].source_file == SAMPLE_DATA_DIR / "metrics" / "checkout-api.jsonl"
    assert metrics[0].line_number == 1
    assert metrics[0].record.metric_name == "p95_latency_ms"

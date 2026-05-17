from pathlib import Path

from telemetry_agents.infrastructure.telemetry_readers import LocalFileTelemetryReader


SAMPLE_DATA = Path("sample_data")


def test_local_file_reader_reads_logs_with_source_location() -> None:
    reader = LocalFileTelemetryReader(SAMPLE_DATA)

    logs = reader.read_logs(service="checkout-api")

    assert logs
    assert logs[0].source_file == SAMPLE_DATA / "logs" / "checkout-api.log"
    assert logs[0].line_number == 1
    assert logs[0].record.service == "checkout-api"
    assert logs[0].record.correlation_id == "cart-123"


def test_local_file_reader_reads_traces_with_source_location() -> None:
    reader = LocalFileTelemetryReader(SAMPLE_DATA)

    traces = reader.read_traces(service="checkout-api")

    assert traces
    assert traces[0].source_file == SAMPLE_DATA / "traces" / "checkout-api.jsonl"
    assert traces[0].line_number == 1
    assert traces[0].record.trace_id == "trace-001"


def test_local_file_reader_reads_metrics_with_source_location() -> None:
    reader = LocalFileTelemetryReader(SAMPLE_DATA)

    metrics = reader.read_metrics(service="checkout-api")

    assert metrics
    assert metrics[0].source_file == SAMPLE_DATA / "metrics" / "checkout-api.jsonl"
    assert metrics[0].line_number == 1
    assert metrics[0].record.metric_name == "p95_latency_ms"

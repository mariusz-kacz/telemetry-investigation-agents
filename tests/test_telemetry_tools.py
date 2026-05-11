import json
from pathlib import Path

import pytest

from telemetry_agents.domain import EvidenceSource, TelemetryEvidence
from telemetry_agents.infrastructure.telemetry_tools import (
    LocalFileDeploymentEventTool,
    LocalFileLogSearchTool,
    LocalFileMetricWindowTool,
    LocalFileTraceLookupTool,
)


SAMPLE_DATA = Path("sample_data")


def test_log_search_returns_typed_cited_evidence_from_local_file() -> None:
    tool = LocalFileLogSearchTool(SAMPLE_DATA)

    evidence = tool.search(service="checkout-api", query="timeout")

    assert evidence
    assert all(isinstance(item, TelemetryEvidence) for item in evidence)
    assert evidence[0].source == EvidenceSource.LOG
    assert evidence[0].citation.startswith("sample_data/logs/")


def test_trace_lookup_returns_typed_cited_evidence_from_local_file() -> None:
    tool = LocalFileTraceLookupTool(SAMPLE_DATA)

    evidence = tool.lookup(service="checkout-api", trace_id="trace-001")

    assert evidence
    assert evidence[0].source == EvidenceSource.TRACE
    assert evidence[0].citation.startswith("sample_data/traces/")


def test_metric_window_returns_typed_cited_evidence_from_local_file() -> None:
    tool = LocalFileMetricWindowTool(SAMPLE_DATA)

    evidence = tool.get_window(
        service="checkout-api",
        metric_name="p95_latency_ms",
        start_timestamp="2026-05-11T09:55:00Z",
        end_timestamp="2026-05-11T10:10:00Z",
    )

    assert evidence
    assert evidence[0].source == EvidenceSource.METRIC
    assert evidence[0].citation.startswith("sample_data/metrics/")


def test_deployment_lookup_returns_typed_cited_evidence_from_local_file() -> None:
    tool = LocalFileDeploymentEventTool(SAMPLE_DATA)

    evidence = tool.find_changes(
        service="checkout-api",
        start_timestamp="2026-05-11T09:30:00Z",
        end_timestamp="2026-05-11T10:10:00Z",
    )

    assert evidence
    assert evidence[0].source == EvidenceSource.DEPLOYMENT
    assert evidence[0].citation.startswith("sample_data/deployments/")


def test_missing_data_behavior_is_explicit() -> None:
    tool = LocalFileLogSearchTool(Path("sample_data/missing-root"))

    with pytest.raises(FileNotFoundError):
        tool.search(service="checkout-api", query="timeout")


def test_trace_lookup_raises_for_malformed_json(tmp_path: Path) -> None:
    traces_dir = tmp_path / "traces"
    traces_dir.mkdir()
    (traces_dir / "checkout-api.jsonl").write_text("{bad json\n", encoding="utf-8")

    tool = LocalFileTraceLookupTool(tmp_path)

    with pytest.raises(json.JSONDecodeError):
        tool.lookup(service="checkout-api", trace_id="trace-001")


def test_metrics_get_window_raises_for_malformed_json(tmp_path: Path) -> None:
    metrics_dir = tmp_path / "metrics"
    metrics_dir.mkdir()
    (metrics_dir / "checkout-api.jsonl").write_text("{bad json\n", encoding="utf-8")

    tool = LocalFileMetricWindowTool(tmp_path)

    with pytest.raises(json.JSONDecodeError):
        tool.get_window(
            service="checkout-api",
            metric_name="any",
            start_timestamp="2026-05-11T09:55:00Z",
            end_timestamp="2026-05-11T10:10:00Z",
        )


def test_deployments_find_changes_raises_for_malformed_json(tmp_path: Path) -> None:
    deployments_dir = tmp_path / "deployments"
    deployments_dir.mkdir()
    (deployments_dir / "checkout-api.jsonl").write_text("{bad json\n", encoding="utf-8")

    tool = LocalFileDeploymentEventTool(tmp_path)

    with pytest.raises(json.JSONDecodeError):
        tool.find_changes(
            service="checkout-api",
            start_timestamp="2026-05-11T09:55:00Z",
            end_timestamp="2026-05-11T10:10:00Z",
        )

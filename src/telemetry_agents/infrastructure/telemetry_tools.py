import json
from pathlib import Path
from typing import Protocol

from telemetry_agents.domain import EvidenceSource, TelemetryEvidence


class LogSearchTool(Protocol):
    def search(self, *, service: str, query: str) -> list[TelemetryEvidence]:
        """Search logs and return cited evidence."""


class TraceLookupTool(Protocol):
    def lookup(self, *, service: str, trace_id: str) -> list[TelemetryEvidence]:
        """Look up trace spans and return cited evidence."""


class MetricWindowTool(Protocol):
    def get_window(
        self,
        *,
        service: str,
        metric_name: str,
        start_timestamp: str,
        end_timestamp: str,
    ) -> list[TelemetryEvidence]:
        """Read metric samples for a time window and return cited evidence."""


class DeploymentEventTool(Protocol):
    def find_changes(
        self,
        *,
        service: str,
        start_timestamp: str,
        end_timestamp: str,
    ) -> list[TelemetryEvidence]:
        """Find deployment changes for a service and return cited evidence."""


class LocalFileLogSearchTool:
    def __init__(self, data_root: Path) -> None:
        self.data_root = data_root

    def search(self, *, service: str, query: str) -> list[TelemetryEvidence]:
        file_path = self.data_root / f"logs/{service}.log"

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        telemetry_evidences: list[TelemetryEvidence] = []
        with file_path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                if query.lower() not in line.lower():
                    continue

                telemetry_evidences.append(
                    TelemetryEvidence(
                        evidence_id=f"log-{service}-{line_number}",
                        service=service,
                        citation=f"{file_path.as_posix()}:{line_number}",
                        source=EvidenceSource.LOG,
                        summary=line.strip(),
                    )
                )
        return telemetry_evidences


class LocalFileTraceLookupTool:
    def __init__(self, data_root: Path) -> None:
        self.data_root = data_root

    def lookup(self, *, service: str, trace_id: str) -> list[TelemetryEvidence]:
        file_path = self.data_root / f"traces/{service}.jsonl"

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        telemetry_evidences: list[TelemetryEvidence] = []
        with file_path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                record = json.loads(line)
                if record["trace_id"] != trace_id or record["service"] != service:
                    continue

                telemetry_evidences.append(
                    TelemetryEvidence(
                        evidence_id=f"trace-{service}-{line_number}",
                        service=service,
                        citation=f"{file_path.as_posix()}:{line_number}",
                        source=EvidenceSource.TRACE,
                        summary=(
                            f"Trace {record['trace_id']} span {record['span_id']} "
                            f"for {record['operation']} ended with status {record['status']} "
                            f"in {record['duration_ms']}ms."
                        ),
                    )
                )
        return telemetry_evidences


class LocalFileMetricWindowTool:
    def __init__(self, data_root: Path) -> None:
        self.data_root = data_root

    def get_window(
        self,
        *,
        service: str,
        metric_name: str,
        start_timestamp: str,
        end_timestamp: str,
    ) -> list[TelemetryEvidence]:
        file_path = self.data_root / f"metrics/{service}.jsonl"

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        telemetry_evidences: list[TelemetryEvidence] = []
        with file_path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                record = json.loads(line)
                # Phase 6 will replace string comparison with parsed timestamp filtering.
                if (
                    record["service"] != service
                    or record["metric_name"] != metric_name
                    or record["timestamp"] < start_timestamp
                    or record["timestamp"] > end_timestamp
                ):
                    continue

                telemetry_evidences.append(
                    TelemetryEvidence(
                        evidence_id=f"metric-{service}-{line_number}",
                        service=service,
                        citation=f"{file_path.as_posix()}:{line_number}",
                        source=EvidenceSource.METRIC,
                        summary=(
                            f"Metric {record['metric_name']} from timestamp {record['timestamp']} "
                            f"for {record['service']} has value {record['value']}."
                        ),
                    )
                )
        return telemetry_evidences


class LocalFileDeploymentEventTool:
    def __init__(self, data_root: Path) -> None:
        self.data_root = data_root

    def find_changes(
        self,
        *,
        service: str,
        start_timestamp: str,
        end_timestamp: str,
    ) -> list[TelemetryEvidence]:
        file_path = self.data_root / f"deployments/{service}.jsonl"

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        telemetry_evidences: list[TelemetryEvidence] = []
        with file_path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                record = json.loads(line)
                # Phase 6 will replace string comparison with parsed timestamp filtering.
                if (
                    record["service"] != service
                    or record["timestamp"] < start_timestamp
                    or record["timestamp"] > end_timestamp
                ):
                    continue

                telemetry_evidences.append(
                    TelemetryEvidence(
                        evidence_id=f"deployment-{service}-{line_number}",
                        service=service,
                        citation=f"{file_path.as_posix()}:{line_number}",
                        source=EvidenceSource.DEPLOYMENT,
                        summary=(
                            f"Deployment {record['version']} for {record['service']} occurred at "
                            f"{record['timestamp']} with commit {record['commit']}: "
                            f"{record['change_summary']}"
                        ),
                    ),
                )
        return telemetry_evidences

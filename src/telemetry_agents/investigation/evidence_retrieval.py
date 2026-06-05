from collections import defaultdict
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from telemetry_agents.domain import EvidenceSource, TelemetryEvidence
from telemetry_agents.investigation.evidence_scoring import (
    EvidenceStrength,
    score_matching_log_line,
    score_matching_metric_sample,
    score_matching_trace_span,
)
from telemetry_agents.investigation.log_matching import (
    MatchDetail,
    MatchReason,
    get_matching_log_lines,
    get_trace_ids_from_seed_logs,
)
from telemetry_agents.investigation.metrics_matching import (
    MatchedMetricSample,
    get_matching_metric_samples,
)
from telemetry_agents.investigation.trace_matching import (
    MatchedTraceSpan,
    get_matching_trace_spans,
    TraceMatchReason,
)
from telemetry_agents.shared.time import parse_utc_timestamp
from telemetry_agents.telemetry.readers import LocalFileTelemetryReader


class CitationMetadata(BaseModel):
    source_file: str = Field(min_length=1)
    line_number: int | None = Field(default=None, ge=1)
    record_id: str | None = None
    timestamp: str | None = None
    service: str = Field(min_length=1)
    selection_reason: str = Field(min_length=1)


class RetrievedEvidence(BaseModel):
    evidence: TelemetryEvidence
    citation: CitationMetadata
    strength: EvidenceStrength
    relevance_score: float = Field(ge=0.0, le=1.0)


class EvidenceRetrievalRequest(BaseModel):
    data_root: str = Field(min_length=1)
    incident_id: str = Field(min_length=1)
    service: str = Field(min_length=1)
    query_terms: list[str] = Field(default_factory=list)
    start_timestamp: str = Field(min_length=1)
    end_timestamp: str = Field(min_length=1)
    trace_id: str | None = None


def _missing_evidence(
    *,
    request: EvidenceRetrievalRequest,
    source: EvidenceSource,
    source_file: Path,
    summary: str,
    selection_reason: str,
) -> list[RetrievedEvidence]:
    return [
        RetrievedEvidence(
            evidence=TelemetryEvidence(
                evidence_id=f"missing-{source.value}-{request.incident_id}",
                service=request.service,
                source=source,
                citation=source_file.as_posix(),
                summary=summary,
            ),
            citation=CitationMetadata(
                source_file=source_file.as_posix(),
                line_number=None,
                service=request.service,
                timestamp=None,
                record_id=None,
                selection_reason=selection_reason,
            ),
            strength=EvidenceStrength.MISSING,
            relevance_score=0,
        )
    ]


def _format_selection_reason(
    match_details: list[MatchDetail],
) -> str:
    result_parts: list[str] = []
    grouped_matches: dict[MatchReason, list[str]] = defaultdict(list)
    for match_detail in match_details:
        grouped_matches[match_detail.reason].append(match_detail.value)

    if trace_ids := grouped_matches.get(MatchReason.REQUEST_TRACE_ID):
        result_parts.append(f"request trace ID {trace_ids[0]}")
    if discovered_trace_ids := grouped_matches.get(MatchReason.DISCOVERED_TRACE_ID):
        result_parts.append(f"discovered trace ID {discovered_trace_ids[0]}")
    if query_terms := grouped_matches.get(MatchReason.QUERY_TERM):
        query_terms_text = ", ".join(query_terms)
        result_parts.append(f"query terms: {query_terms_text}")
    if severity := grouped_matches.get(MatchReason.SEVERITY):
        result_parts.append(f"discovered logs with severity {', '.join(severity)}")
    if not result_parts:
        raise ValueError("selection reason requires at least one match detail")

    return f"Matched {', '.join(result_parts)}."


def _format_trace_selection_reason(
    match_reason: TraceMatchReason, trace_id: str
) -> str:
    if match_reason == TraceMatchReason.REQUEST_TRACE_ID:
        return f"Matched request trace ID {trace_id}."
    elif match_reason == TraceMatchReason.DISCOVERED_TRACE_ID:
        return (
            f"Matched discovered trace ID {trace_id} from query-matched log evidence."
        )
    raise ValueError("Unknown match reason.")


def _retrieve_log_evidence(
    *,
    reader: LocalFileTelemetryReader,
    start_timestamp: datetime,
    end_timestamp: datetime,
    request: EvidenceRetrievalRequest,
) -> tuple[list[RetrievedEvidence], set[str]]:
    retrieved_log_evidence: list[RetrievedEvidence] = []
    source_file = Path(request.data_root) / "logs" / f"{request.service}.log"

    try:
        log_records = reader.read_logs(service=request.service)
    except FileNotFoundError:
        return (
            _missing_evidence(
                request=request,
                source=EvidenceSource.LOG,
                source_file=source_file,
                summary="Log source file is unavailable for this incident.",
                selection_reason="Log source file was not found.",
            ),
            set(),
        )

    trace_ids_from_query_seed_logs = get_trace_ids_from_seed_logs(
        log_records=log_records,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        service=request.service,
        query_terms=request.query_terms,
    )

    matching_log_lines = get_matching_log_lines(
        log_records=log_records,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        service=request.service,
        query_terms=request.query_terms,
        trace_id=request.trace_id,
        trace_ids_from_query_seed_logs=trace_ids_from_query_seed_logs,
    )

    for matching_log_line in matching_log_lines:
        telemetry_evidence = TelemetryEvidence(
            evidence_id=f"log-{matching_log_line.log_line.service}-{matching_log_line.line_number}",
            service=matching_log_line.log_line.service,
            citation=f"{matching_log_line.source_file.as_posix()}:{matching_log_line.line_number}",
            source=EvidenceSource.LOG,
            summary=f"{matching_log_line.log_line.level} log from {matching_log_line.log_line.service}: {matching_log_line.log_line.message}",
        )
        citation_metadata = CitationMetadata(
            line_number=matching_log_line.line_number,
            source_file=matching_log_line.source_file.as_posix(),
            service=matching_log_line.log_line.service,
            timestamp=matching_log_line.log_line.timestamp.isoformat(),
            record_id=None,
            selection_reason=_format_selection_reason(matching_log_line.match_details),
        )

        evidence_strength, relevance_score = score_matching_log_line(matching_log_line)

        retrieved_log_evidence.append(
            RetrievedEvidence(
                evidence=telemetry_evidence,
                citation=citation_metadata,
                strength=evidence_strength,
                relevance_score=relevance_score,
            )
        )

    if not retrieved_log_evidence:
        return (
            _missing_evidence(
                request=request,
                source=EvidenceSource.LOG,
                source_file=source_file,
                summary="No matching log evidence found for the incident filters.",
                selection_reason="No log records matched the incident time window, IDs, severity or query terms.",
            ),
            set(),
        )
    return retrieved_log_evidence, trace_ids_from_query_seed_logs


def _retrieve_trace_evidence(
    *,
    reader: LocalFileTelemetryReader,
    start_timestamp: datetime,
    end_timestamp: datetime,
    request: EvidenceRetrievalRequest,
    trace_ids_from_query_seed_logs: set[str],
) -> list[RetrievedEvidence]:
    retrieved_trace_evidence: list[RetrievedEvidence] = []
    source_file = Path(request.data_root) / "traces" / f"{request.service}.jsonl"

    try:
        matching_trace_spans: list[MatchedTraceSpan] = get_matching_trace_spans(
            trace_span_records=reader.read_traces(service=request.service),
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            trace_id=request.trace_id,
            trace_ids_from_query_seed_logs=trace_ids_from_query_seed_logs,
        )
    except FileNotFoundError:
        return _missing_evidence(
            request=request,
            source=EvidenceSource.TRACE,
            source_file=source_file,
            summary="Trace source file is unavailable for this incident.",
            selection_reason="Trace source file was not found.",
        )

    for matching_trace_span in matching_trace_spans:
        telemetry_evidence = TelemetryEvidence(
            evidence_id=f"trace-{request.service}-{matching_trace_span.line_number}",
            service=matching_trace_span.trace_span.service,
            citation=f"{matching_trace_span.source_file.as_posix()}:{matching_trace_span.line_number}",
            source=EvidenceSource.TRACE,
            summary=(
                f"Trace {matching_trace_span.trace_span.trace_id} span {matching_trace_span.trace_span.span_id} "
                f"for {matching_trace_span.trace_span.operation} ended with status {matching_trace_span.trace_span.status} "
                f"in {matching_trace_span.trace_span.duration_ms}ms."
            ),
        )
        citation_metadata = CitationMetadata(
            line_number=matching_trace_span.line_number,
            source_file=matching_trace_span.source_file.as_posix(),
            service=matching_trace_span.trace_span.service,
            timestamp=matching_trace_span.trace_span.timestamp.isoformat(),
            record_id=None,
            selection_reason=_format_trace_selection_reason(
                matching_trace_span.match_reason,
                matching_trace_span.trace_span.trace_id,
            ),
        )

        (evidence_strength, relevance_score) = score_matching_trace_span(
            matching_trace_span.match_reason
        )

        retrieved_trace_evidence.append(
            RetrievedEvidence(
                evidence=telemetry_evidence,
                citation=citation_metadata,
                strength=evidence_strength,
                relevance_score=relevance_score,
            )
        )

    if not retrieved_trace_evidence:
        return _missing_evidence(
            request=request,
            source=EvidenceSource.TRACE,
            source_file=source_file,
            summary="No matching trace spans found for the incident filters.",
            selection_reason="No trace spans matched the incident time window or IDs.",
        )
    return retrieved_trace_evidence


def _retrieve_metric_evidence(
    *,
    reader: LocalFileTelemetryReader,
    start_timestamp: datetime,
    end_timestamp: datetime,
    request: EvidenceRetrievalRequest,
) -> list[RetrievedEvidence]:
    retrieved_metric_evidence: list[RetrievedEvidence] = []
    source_file = Path(request.data_root) / "metrics" / f"{request.service}.jsonl"

    try:
        matching_metric_samples: list[MatchedMetricSample] = (
            get_matching_metric_samples(
                metric_sample_records=reader.read_metrics(service=request.service),
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                service=request.service,
            )
        )
    except FileNotFoundError:
        return _missing_evidence(
            request=request,
            source=EvidenceSource.METRIC,
            source_file=source_file,
            summary="Metric source file is unavailable for this incident.",
            selection_reason="Metric source file was not found.",
        )

    for matching_metric_sample in matching_metric_samples:
        telemetry_evidence = TelemetryEvidence(
            evidence_id=f"metric-{request.service}-{matching_metric_sample.line_number}",
            service=matching_metric_sample.metric_sample.service,
            citation=f"{matching_metric_sample.source_file.as_posix()}:{matching_metric_sample.line_number}",
            source=EvidenceSource.METRIC,
            summary=(
                f"Metric {matching_metric_sample.metric_sample.metric_name} from timestamp {matching_metric_sample.metric_sample.timestamp} "
                f"for {matching_metric_sample.metric_sample.service} has value {matching_metric_sample.metric_sample.value}."
            ),
        )
        citation_metadata = CitationMetadata(
            line_number=matching_metric_sample.line_number,
            source_file=matching_metric_sample.source_file.as_posix(),
            service=matching_metric_sample.metric_sample.service,
            timestamp=matching_metric_sample.metric_sample.timestamp.isoformat(),
            record_id=None,
            selection_reason=f"Matched metric {matching_metric_sample.metric_sample.metric_name} for service {matching_metric_sample.metric_sample.service} inside incident time window.",
        )

        (evidence_strength, relevance_score) = score_matching_metric_sample()

        retrieved_metric_evidence.append(
            RetrievedEvidence(
                evidence=telemetry_evidence,
                citation=citation_metadata,
                strength=evidence_strength,
                relevance_score=relevance_score,
            )
        )

    if not retrieved_metric_evidence:
        return _missing_evidence(
            request=request,
            source=EvidenceSource.METRIC,
            source_file=source_file,
            summary="No matching metric samples found for the incident filters.",
            selection_reason="No metric samples matched the incident time window.",
        )
    return retrieved_metric_evidence


def retrieve_evidence(request: EvidenceRetrievalRequest) -> list[RetrievedEvidence]:
    """Retrieve and rank cited evidence for one incident investigation."""
    try:
        start_timestamp = parse_utc_timestamp(request.start_timestamp)
        end_timestamp = parse_utc_timestamp(request.end_timestamp)
    except ValueError as exc:
        raise ValueError("Wrong timestamp value") from exc

    reader = LocalFileTelemetryReader(Path(request.data_root))

    log_evidence, trace_ids_from_query_seed_logs = _retrieve_log_evidence(
        reader=reader,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        request=request,
    )
    trace_span_evidence = _retrieve_trace_evidence(
        reader=reader,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        request=request,
        trace_ids_from_query_seed_logs=trace_ids_from_query_seed_logs,
    )

    metric_sample_evidence = _retrieve_metric_evidence(
        reader=reader,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        request=request,
    )

    retrieved_evidence = log_evidence + trace_span_evidence + metric_sample_evidence
    return sorted(
        retrieved_evidence,
        key=lambda item: item.relevance_score,
        reverse=True,
    )

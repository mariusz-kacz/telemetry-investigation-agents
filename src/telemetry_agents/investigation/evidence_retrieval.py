from collections import defaultdict
from dataclasses import dataclass
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
from telemetry_agents.shared.observability import (
    emit_event,
    EVENT_EVIDENCE_RETRIEVAL_COMPLETED,
    EVENT_TELEMETRY_SOURCE_UNAVAILABLE,
)
from telemetry_agents.shared.time import parse_utc_timestamp
from telemetry_agents.shared.tracing import get_tracer
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
    run_id: str = Field(min_length=1)
    data_root: str = Field(min_length=1)
    incident_id: str = Field(min_length=1)
    service: str = Field(min_length=1)
    query_terms: list[str] = Field(default_factory=list)
    start_timestamp: str = Field(min_length=1)
    end_timestamp: str = Field(min_length=1)
    trace_id: str | None = None


@dataclass(frozen=True)
class EvidenceRetrievalSummary:
    log_count: int
    trace_count: int
    metric_count: int
    strong_count: int
    medium_count: int
    weak_count: int
    missing_count: int


def _evidence_citation(source_file: Path, line_number: int) -> str:
    return f"{source_file.as_posix()}:{line_number}"


def _retrieved_evidence(
    *,
    evidence_id: str,
    source: EvidenceSource,
    service: str,
    summary: str,
    source_file: Path,
    line_number: int,
    timestamp: datetime,
    selection_reason: str,
    strength: EvidenceStrength,
    relevance_score: float,
) -> RetrievedEvidence:
    return RetrievedEvidence(
        evidence=TelemetryEvidence(
            evidence_id=evidence_id,
            service=service,
            citation=_evidence_citation(source_file, line_number),
            source=source,
            summary=summary,
        ),
        citation=CitationMetadata(
            line_number=line_number,
            source_file=source_file.as_posix(),
            service=service,
            timestamp=timestamp.isoformat(),
            record_id=None,
            selection_reason=selection_reason,
        ),
        strength=strength,
        relevance_score=relevance_score,
    )


def _summarize_retrieved_evidence(
    *,
    log_evidence: list[RetrievedEvidence],
    trace_evidence: list[RetrievedEvidence],
    metric_evidence: list[RetrievedEvidence],
) -> EvidenceRetrievalSummary:
    retrieved_evidence = log_evidence + trace_evidence + metric_evidence
    return EvidenceRetrievalSummary(
        log_count=len(log_evidence),
        trace_count=len(trace_evidence),
        metric_count=len(metric_evidence),
        strong_count=sum(
            item.strength == EvidenceStrength.STRONG for item in retrieved_evidence
        ),
        medium_count=sum(
            item.strength == EvidenceStrength.MEDIUM for item in retrieved_evidence
        ),
        weak_count=sum(
            item.strength == EvidenceStrength.WEAK for item in retrieved_evidence
        ),
        missing_count=sum(
            item.strength == EvidenceStrength.MISSING for item in retrieved_evidence
        ),
    )


def _missing_evidence(
    *,
    request: EvidenceRetrievalRequest,
    source: EvidenceSource,
    source_file: Path,
    summary: str,
    selection_reason: str,
    emit_source_unavailable: bool = False,
) -> list[RetrievedEvidence]:
    if emit_source_unavailable:
        emit_event(
            EVENT_TELEMETRY_SOURCE_UNAVAILABLE,
            run_id=request.run_id,
            incident_id=request.incident_id,
            source=source.value,
            source_file=source_file.as_posix(),
            reason=selection_reason,
        )
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
                emit_source_unavailable=True,
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
        evidence_strength, relevance_score = score_matching_log_line(matching_log_line)

        retrieved_log_evidence.append(
            _retrieved_evidence(
                evidence_id=(
                    f"log-{matching_log_line.log_line.service}-"
                    f"{matching_log_line.line_number}"
                ),
                service=matching_log_line.log_line.service,
                source=EvidenceSource.LOG,
                source_file=matching_log_line.source_file,
                line_number=matching_log_line.line_number,
                timestamp=matching_log_line.log_line.timestamp,
                summary=(
                    f"{matching_log_line.log_line.level} log from "
                    f"{matching_log_line.log_line.service}: "
                    f"{matching_log_line.log_line.message}"
                ),
                selection_reason=_format_selection_reason(
                    matching_log_line.match_details
                ),
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
            emit_source_unavailable=True,
        )

    for matching_trace_span in matching_trace_spans:
        evidence_strength, relevance_score = score_matching_trace_span(
            matching_trace_span.match_reason
        )

        retrieved_trace_evidence.append(
            _retrieved_evidence(
                evidence_id=f"trace-{request.service}-{matching_trace_span.line_number}",
                service=matching_trace_span.trace_span.service,
                source=EvidenceSource.TRACE,
                source_file=matching_trace_span.source_file,
                line_number=matching_trace_span.line_number,
                timestamp=matching_trace_span.trace_span.timestamp,
                summary=(
                    f"Trace {matching_trace_span.trace_span.trace_id} span "
                    f"{matching_trace_span.trace_span.span_id} for "
                    f"{matching_trace_span.trace_span.operation} ended with status "
                    f"{matching_trace_span.trace_span.status} in "
                    f"{matching_trace_span.trace_span.duration_ms}ms."
                ),
                selection_reason=_format_trace_selection_reason(
                    matching_trace_span.match_reason,
                    matching_trace_span.trace_span.trace_id,
                ),
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
            emit_source_unavailable=True,
        )

    for matching_metric_sample in matching_metric_samples:
        evidence_strength, relevance_score = score_matching_metric_sample()

        retrieved_metric_evidence.append(
            _retrieved_evidence(
                evidence_id=(
                    f"metric-{request.service}-{matching_metric_sample.line_number}"
                ),
                service=matching_metric_sample.metric_sample.service,
                source=EvidenceSource.METRIC,
                source_file=matching_metric_sample.source_file,
                line_number=matching_metric_sample.line_number,
                timestamp=matching_metric_sample.metric_sample.timestamp,
                summary=(
                    f"Metric {matching_metric_sample.metric_sample.metric_name} "
                    f"from timestamp {matching_metric_sample.metric_sample.timestamp} "
                    f"for {matching_metric_sample.metric_sample.service} has value "
                    f"{matching_metric_sample.metric_sample.value}."
                ),
                selection_reason=(
                    f"Matched metric {matching_metric_sample.metric_sample.metric_name} "
                    f"for service {matching_metric_sample.metric_sample.service} "
                    "inside incident time window."
                ),
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
    tracer = get_tracer()
    with tracer.start_as_current_span("evidence.retrieval") as retrieval_span:
        retrieval_span.set_attribute("run_id", request.run_id)
        retrieval_span.set_attribute("incident_id", request.incident_id)
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
        evidence_summary = _summarize_retrieved_evidence(
            log_evidence=log_evidence,
            trace_evidence=trace_span_evidence,
            metric_evidence=metric_sample_evidence,
        )
        retrieval_span.set_attribute("evidence.log_count", evidence_summary.log_count)
        retrieval_span.set_attribute(
            "evidence.trace_count", evidence_summary.trace_count
        )
        retrieval_span.set_attribute(
            "evidence.metric_count", evidence_summary.metric_count
        )
        retrieval_span.set_attribute(
            "evidence.strong_count", evidence_summary.strong_count
        )
        retrieval_span.set_attribute(
            "evidence.medium_count", evidence_summary.medium_count
        )
        retrieval_span.set_attribute(
            "evidence.weak_count", evidence_summary.weak_count
        )
        retrieval_span.set_attribute(
            "evidence.missing_count", evidence_summary.missing_count
        )

        _emit_evidence_retrieval_completed_event(
            run_id=request.run_id,
            incident_id=request.incident_id,
            evidence_summary=evidence_summary,
        )
        return sorted(
            retrieved_evidence,
            key=lambda item: item.relevance_score,
            reverse=True,
        )


def _emit_evidence_retrieval_completed_event(
    run_id: str,
    incident_id: str,
    evidence_summary: EvidenceRetrievalSummary,
) -> None:
    emit_event(
        EVENT_EVIDENCE_RETRIEVAL_COMPLETED,
        run_id=run_id,
        incident_id=incident_id,
        log_count=evidence_summary.log_count,
        trace_count=evidence_summary.trace_count,
        metric_count=evidence_summary.metric_count,
        strong_count=evidence_summary.strong_count,
        medium_count=evidence_summary.medium_count,
        weak_count=evidence_summary.weak_count,
        missing_count=evidence_summary.missing_count,
    )

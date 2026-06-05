from enum import StrEnum

from telemetry_agents.investigation.log_matching import MatchedLogLine, MatchReason
from telemetry_agents.investigation.trace_matching import TraceMatchReason


class EvidenceStrength(StrEnum):
    STRONG = "strong"
    MEDIUM = "medium"
    WEAK = "weak"
    MISSING = "missing"


ClassificationRule = tuple[frozenset[MatchReason], EvidenceStrength, float]


LOG_CLASSIFICATION_RULES: tuple[ClassificationRule, ...] = (
    (
        frozenset(
            {
                MatchReason.QUERY_TERM,
                MatchReason.REQUEST_TRACE_ID,
            }
        ),
        EvidenceStrength.STRONG,
        1.0,
    ),
    (
        frozenset(
            {
                MatchReason.QUERY_TERM,
                MatchReason.SEVERITY,
            }
        ),
        EvidenceStrength.STRONG,
        0.8,
    ),
    (
        frozenset({MatchReason.REQUEST_TRACE_ID}),
        EvidenceStrength.MEDIUM,
        0.8,
    ),
    (
        frozenset(
            {
                MatchReason.SEVERITY,
            }
        ),
        EvidenceStrength.MEDIUM,
        0.6,
    ),
    (
        frozenset({MatchReason.QUERY_TERM}),
        EvidenceStrength.MEDIUM,
        0.6,
    ),
    (
        frozenset({MatchReason.DISCOVERED_TRACE_ID}),
        EvidenceStrength.MEDIUM,
        0.6,
    ),
)


def score_matching_log_line(
    matching_log_line: MatchedLogLine,
) -> tuple[EvidenceStrength, float]:
    found_reasons = {detail.reason for detail in matching_log_line.match_details}

    for required_reasons, strength, relevance_score in LOG_CLASSIFICATION_RULES:
        if required_reasons <= found_reasons:
            return strength, relevance_score

    raise ValueError("matched log line has no match reasons")


def score_matching_trace_span(
    match_reason: TraceMatchReason,
) -> tuple[EvidenceStrength, float]:
    if match_reason == TraceMatchReason.REQUEST_TRACE_ID:
        return EvidenceStrength.STRONG, 1.0
    if match_reason == TraceMatchReason.DISCOVERED_TRACE_ID:
        return EvidenceStrength.MEDIUM, 0.6

    raise ValueError("matched trace has no match reasons")


def score_matching_metric_sample() -> tuple[EvidenceStrength, float]:
    return EvidenceStrength.MEDIUM, 0.6

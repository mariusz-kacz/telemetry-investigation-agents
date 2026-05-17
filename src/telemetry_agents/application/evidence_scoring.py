from enum import StrEnum

from telemetry_agents.application.log_matching import MatchedLogLine, MatchReason


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
                MatchReason.CORRELATION_ID,
                MatchReason.TRACE_ID,
            }
        ),
        EvidenceStrength.STRONG,
        1.0,
    ),
    (
        frozenset({MatchReason.QUERY_TERM, MatchReason.CORRELATION_ID}),
        EvidenceStrength.STRONG,
        0.8,
    ),
    (
        frozenset({MatchReason.QUERY_TERM, MatchReason.TRACE_ID}),
        EvidenceStrength.STRONG,
        0.8,
    ),
    (
        frozenset({MatchReason.CORRELATION_ID, MatchReason.TRACE_ID}),
        EvidenceStrength.MEDIUM,
        0.6,
    ),
    (
        frozenset({MatchReason.CORRELATION_ID}),
        EvidenceStrength.MEDIUM,
        0.4,
    ),
    (
        frozenset({MatchReason.TRACE_ID}),
        EvidenceStrength.MEDIUM,
        0.4,
    ),
    (
        frozenset({MatchReason.QUERY_TERM}),
        EvidenceStrength.WEAK,
        0.2,
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


def score_matching_trace_span() -> tuple[EvidenceStrength, float]:
    return EvidenceStrength.STRONG, 1.0


def score_matching_metric_sample() -> tuple[EvidenceStrength, float]:
    return EvidenceStrength.MEDIUM, 0.6

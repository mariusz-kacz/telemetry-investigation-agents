from datetime import UTC, datetime
from pathlib import Path

import pytest

from telemetry_agents.investigation.evidence_scoring import (
    EvidenceStrength,
    score_matching_log_line,
)
from telemetry_agents.investigation.log_matching import (
    MatchDetail,
    MatchedLogLine,
    MatchReason,
)

from telemetry_agents.telemetry.models import ParsedLogRecord


def _matched_log_line(match_reasons: list[MatchReason]) -> MatchedLogLine:
    return MatchedLogLine(
        log_line=ParsedLogRecord(
            timestamp=datetime(2026, 5, 11, 10, 1, tzinfo=UTC),
            level="ERROR",
            service="checkout-api",
            message="DatabaseTimeoutException while calling orders-db",
            correlation_id="cart-123",
            trace_id="trace-001",
        ),
        source_file=Path("sample_data/logs/checkout-api.log"),
        line_number=1,
        match_details=[
            MatchDetail(reason=reason, value=reason.value) for reason in match_reasons
        ],
    )


@pytest.mark.parametrize(
    ("match_reasons", "expected_strength", "expected_score"),
    [
        (
            [
                MatchReason.QUERY_TERM,
                MatchReason.CORRELATION_ID,
                MatchReason.TRACE_ID,
            ],
            EvidenceStrength.STRONG,
            1.0,
        ),
        (
            [MatchReason.QUERY_TERM, MatchReason.CORRELATION_ID],
            EvidenceStrength.STRONG,
            0.8,
        ),
        (
            [MatchReason.CORRELATION_ID, MatchReason.TRACE_ID],
            EvidenceStrength.MEDIUM,
            0.6,
        ),
        ([MatchReason.QUERY_TERM], EvidenceStrength.WEAK, 0.2),
    ],
)
def test_score_matching_log_line_uses_strongest_matching_rule(
    match_reasons: list[MatchReason],
    expected_strength: EvidenceStrength,
    expected_score: float,
) -> None:
    (strength, relevance_score) = score_matching_log_line(
        _matched_log_line(match_reasons)
    )

    assert strength == expected_strength
    assert relevance_score == expected_score


def test_score_matching_log_line_rejects_match_without_reasons() -> None:
    with pytest.raises(ValueError, match="no match reasons"):
        score_matching_log_line(_matched_log_line([]))

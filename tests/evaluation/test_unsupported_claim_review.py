import pytest

from telemetry_agents.domain import (
    EvidenceSource,
    HypothesisCategory,
    InvestigationHypothesis,
    TelemetryEvidence,
)
from telemetry_agents.evaluation import GuardedUnsupportedClaimReviewer
from telemetry_agents.evaluation.unsupported_claim_review import (
    UnsupportedClaimFinding,
    UnsupportedClaimReviewRequest,
    UnsupportedClaimReviewResult,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


class FakeUnsupportedClaimReviewAdapter:
    def __init__(self, result: UnsupportedClaimReviewResult) -> None:
        self.result = result
        self.requests: list[UnsupportedClaimReviewRequest] = []

    def review(
        self,
        request: UnsupportedClaimReviewRequest,
    ) -> UnsupportedClaimReviewResult:
        self.requests.append(request)
        return self.result


def _accepted_hypothesis(supporting_evidence_id: str) -> InvestigationHypothesis:
    return InvestigationHypothesis(
        hypothesis_id="hyp-001",
        statement="A DNS outage caused checkout database timeouts.",
        category=HypothesisCategory.NETWORK_FAILURE,
        supporting_evidence_ids=[supporting_evidence_id],
        confidence=0.9,
    )


def _retrieved_evidence(evidence_strength: EvidenceStrength) -> RetrievedEvidence:
    return RetrievedEvidence(
        evidence=TelemetryEvidence(
            evidence_id="log-001",
            source=EvidenceSource.LOG,
            summary="Checkout API reports database timeout errors.",
            citation="sample_data/logs/checkout-api.log:1",
            service="checkout-api",
        ),
        citation=CitationMetadata(
            source_file="sample_data/logs/checkout-api.log",
            line_number=1,
            service="checkout-api",
            selection_reason="Matched incident query terms.",
        ),
        strength=evidence_strength,
        relevance_score=1.0,
    )


def _request(
    supporting_evidence_id: str = "log-001",
    evidence_strength: EvidenceStrength = EvidenceStrength.STRONG,
) -> UnsupportedClaimReviewRequest:
    return UnsupportedClaimReviewRequest(
        evidence=[_retrieved_evidence(evidence_strength=evidence_strength)],
        accepted_hypotheses=[
            _accepted_hypothesis(supporting_evidence_id=supporting_evidence_id)
        ],
    )


def test_review_unsupported_claims_returns_structured_findings() -> None:
    adapter = FakeUnsupportedClaimReviewAdapter(
        UnsupportedClaimReviewResult(
            findings=[
                UnsupportedClaimFinding(
                    hypothesis_id="hyp-001",
                    claim="A DNS outage caused checkout database timeouts.",
                    reason="The cited log reports a database timeout but does not support a DNS outage.",
                    evidence_ids=["log-001"],
                )
            ]
        )
    )
    reviewer = GuardedUnsupportedClaimReviewer(adapter=adapter)

    result = reviewer.review(request=_request())

    assert result == adapter.result
    assert adapter.requests == [_request()]


def test_review_unsupported_claims_rejects_unknown_hypothesis_id() -> None:
    adapter = FakeUnsupportedClaimReviewAdapter(
        UnsupportedClaimReviewResult(
            findings=[
                UnsupportedClaimFinding(
                    hypothesis_id="hyp-unknown",
                    claim="A DNS outage caused checkout database timeouts.",
                    reason="The hypothesis is unsupported.",
                )
            ]
        )
    )
    reviewer = GuardedUnsupportedClaimReviewer(adapter=adapter)

    with pytest.raises(ValueError, match="unknown hypothesis ID"):
        reviewer.review(request=_request())


def test_review_unsupported_claims_rejects_unknown_evidence_id() -> None:
    adapter = FakeUnsupportedClaimReviewAdapter(
        UnsupportedClaimReviewResult(
            findings=[
                UnsupportedClaimFinding(
                    hypothesis_id="hyp-001",
                    claim="A DNS outage caused checkout database timeouts.",
                    reason="The cited evidence does not support the claim.",
                    evidence_ids=["log-unknown"],
                )
            ]
        )
    )
    reviewer = GuardedUnsupportedClaimReviewer(adapter=adapter)

    with pytest.raises(ValueError, match="unknown evidence ID"):
        reviewer.review(request=_request())


def test_review_unsupported_claims_rejects_missing_evidence() -> None:
    adapter = FakeUnsupportedClaimReviewAdapter(
        UnsupportedClaimReviewResult(
            findings=[
                UnsupportedClaimFinding(
                    hypothesis_id="hyp-001",
                    claim="A DNS outage caused checkout database timeouts.",
                    reason="The cited evidence does not support the claim.",
                    evidence_ids=["log-001"],
                )
            ]
        )
    )
    reviewer = GuardedUnsupportedClaimReviewer(adapter=adapter)

    with pytest.raises(ValueError, match="missing evidence"):
        reviewer.review(
            request=_request(evidence_strength=EvidenceStrength.MISSING),
        )

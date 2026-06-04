from typing import Protocol

from pydantic import BaseModel, Field

from telemetry_agents.domain import InvestigationHypothesis
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


class UnsupportedClaimReviewerUnavailableError(RuntimeError):
    pass


class UnsupportedClaimFinding(BaseModel):
    hypothesis_id: str = Field(min_length=1)
    claim: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)


class UnsupportedClaimReviewRequest(BaseModel):
    evidence: list[RetrievedEvidence] = Field(default_factory=list)
    reviewed_accepted_hypotheses: list[InvestigationHypothesis] = Field(
        default_factory=list
    )


class UnsupportedClaimReviewResult(BaseModel):
    findings: list[UnsupportedClaimFinding] = Field(default_factory=list)


class _UnsupportedClaimReviewAdapter(Protocol):
    """Raw adapter boundary for semantic review. Use the guarded wrapper in application code."""

    def review(
        self,
        request: UnsupportedClaimReviewRequest,
    ) -> UnsupportedClaimReviewResult:
        """Provider call only. Prefer GuardedUnsupportedClaimReviewer to enforce ID guardrails."""
        ...


class GuardedUnsupportedClaimReviewer:
    def __init__(self, *, adapter: _UnsupportedClaimReviewAdapter) -> None:
        self.adapter = adapter

    def review(
        self,
        request: UnsupportedClaimReviewRequest,
    ) -> UnsupportedClaimReviewResult:
        result = self.adapter.review(request)
        validate_unsupported_claim_review(request=request, result=result)
        return result


def validate_unsupported_claim_review(
    *, request: UnsupportedClaimReviewRequest, result: UnsupportedClaimReviewResult
) -> None:
    """Run semantic unsupported-claim review and enforce result guardrails."""
    hypothesis_ids = {
        item.hypothesis_id for item in request.reviewed_accepted_hypotheses
    }
    evidence_by_id = {item.evidence.evidence_id: item for item in request.evidence}
    evidence_ids = set(evidence_by_id)

    for finding in result.findings:
        if finding.hypothesis_id not in hypothesis_ids:
            raise ValueError("Reviewer references unknown hypothesis ID.")
        if set(finding.evidence_ids) - evidence_ids:
            raise ValueError("Reviewer references unknown evidence ID.")
        for evidence_id in finding.evidence_ids:
            if evidence_by_id[evidence_id].strength == EvidenceStrength.MISSING:
                raise ValueError("Reviewer references missing evidence.")

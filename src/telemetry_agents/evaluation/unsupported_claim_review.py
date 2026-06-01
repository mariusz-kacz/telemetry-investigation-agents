from typing import Protocol

from pydantic import BaseModel, Field

from telemetry_agents.domain import InvestigationHypothesis
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


class UnsupportedClaimFinding(BaseModel):
    hypothesis_id: str = Field(min_length=1)
    claim: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)


class UnsupportedClaimReviewRequest(BaseModel):
    evidence: list[RetrievedEvidence] = Field(default_factory=list)
    accepted_hypotheses: list[InvestigationHypothesis] = Field(default_factory=list)


class UnsupportedClaimReviewResult(BaseModel):
    findings: list[UnsupportedClaimFinding] = Field(default_factory=list)


class UnsupportedClaimReviewer(Protocol):
    """Adapter boundary for semantic unsupported-claim review."""

    def review(
        self,
        request: UnsupportedClaimReviewRequest,
    ) -> UnsupportedClaimReviewResult:
        """Review accepted hypotheses for unsupported causal claims."""
        ...


def review_unsupported_claims(
    *,
    request: UnsupportedClaimReviewRequest,
    reviewer: UnsupportedClaimReviewer,
) -> UnsupportedClaimReviewResult:
    """Run semantic unsupported-claim review and enforce result guardrails."""
    review_result = reviewer.review(
        request=request,
    )

    hypothesis_ids = {item.hypothesis_id for item in request.accepted_hypotheses}
    evidence_by_id = {item.evidence.evidence_id: item for item in request.evidence}
    evidence_ids = set(evidence_by_id)

    for finding in review_result.findings:
        if finding.hypothesis_id not in hypothesis_ids:
            raise ValueError("Reviewer references unknown hypothesis ID.")
        if set(finding.evidence_ids) - evidence_ids:
            raise ValueError("Reviewer references unknown evidence ID.")
        for evidence_id in finding.evidence_ids:
            if evidence_by_id[evidence_id].strength == EvidenceStrength.MISSING:
                raise ValueError("Reviewer references missing evidence.")
    return review_result

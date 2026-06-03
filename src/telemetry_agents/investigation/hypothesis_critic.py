from typing import Protocol

from pydantic import BaseModel, Field

from telemetry_agents.domain.models import (
    HypothesisValidationResult,
    HypothesisCritiqueResult,
)
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


class HypothesisCritiqueRequest(BaseModel):
    evidence: list[RetrievedEvidence] = Field(default_factory=list)
    validation_result: HypothesisValidationResult


class HypothesisCriticUnavailableError(RuntimeError):
    pass


class HypothesisCritic(Protocol):
    """Adapter boundary for an LLM-backed structured hypothesis critic."""

    def critique(
        self,
        request: HypothesisCritiqueRequest,
    ) -> HypothesisCritiqueResult:
        """Review validated hypotheses for semantic concerns."""
        ...


def critique_hypotheses(
    request: HypothesisCritiqueRequest,
    critic: HypothesisCritic,
) -> HypothesisCritiqueResult:
    """Critique validated hypotheses using an LLM-backed critic adapter."""
    critique_result = critic.critique(
        request=request,
    )

    validation_result = request.validation_result
    hypothesis_ids = {
        item.hypothesis_id for item in validation_result.validated_hypotheses
    }
    evidence_by_id = {item.evidence.evidence_id: item for item in request.evidence}
    evidence_ids = set(evidence_by_id)

    for finding in critique_result.critique_findings:
        if finding.hypothesis_id not in hypothesis_ids:
            raise ValueError("Critique references unknown hypothesis ID.")
        if set(finding.evidence_ids) - evidence_ids:
            raise ValueError("Critique references unknown evidence ID.")
        for evidence_id in finding.evidence_ids:
            if evidence_by_id[evidence_id].strength == EvidenceStrength.MISSING:
                raise ValueError("Critique references missing evidence.")

    return critique_result

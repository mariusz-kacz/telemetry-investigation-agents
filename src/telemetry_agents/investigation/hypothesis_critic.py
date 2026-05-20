from typing import Protocol

from pydantic import BaseModel, Field

from telemetry_agents.domain.models import (
    HypothesisValidationResult,
    HypothesisCritiqueResult,
)
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence


class HypothesisCritiqueRequest(BaseModel):
    evidence: list[RetrievedEvidence] = Field(default_factory=list)
    validation_result: HypothesisValidationResult


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
    return critic.critique(request)

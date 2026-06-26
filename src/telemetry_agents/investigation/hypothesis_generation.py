from typing import Protocol

from pydantic import BaseModel, Field

from telemetry_agents.domain import Incident, InvestigationHypothesis
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence


class HypothesisGenerationRequest(BaseModel):
    run_id: str | None = Field(default=None, min_length=1)
    incident: Incident
    evidence: list[RetrievedEvidence] = Field(default_factory=list)


class HypothesisGenerator(Protocol):
    """Adapter boundary for an LLM-backed structured hypothesis generator."""

    def generate(
        self,
        request: HypothesisGenerationRequest,
    ) -> list[InvestigationHypothesis]:
        """Return candidate hypotheses from bounded incident and evidence context."""
        ...


class HypothesisGeneratorUnavailableError(Exception):
    pass


def generate_hypotheses(
    request: HypothesisGenerationRequest,
    generator: HypothesisGenerator,
) -> list[InvestigationHypothesis]:
    """Generate typed candidate hypotheses from bounded incident and evidence context."""
    return generator.generate(request)

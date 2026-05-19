from typing import Protocol

from pydantic import BaseModel, Field

from telemetry_agents.domain import Incident, InvestigationHypothesis
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


class HypothesisGenerationRequest(BaseModel):
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


def generate_hypotheses(
    request: HypothesisGenerationRequest,
    generator: HypothesisGenerator,
) -> list[InvestigationHypothesis]:
    """Generate hypotheses and enforce deterministic citation/confidence guardrails"""

    generated_hypotheses = generator.generate(request)
    validated_hypotheses: list[InvestigationHypothesis] = []
    known_evidence_ids: set[str] = {
        item.evidence.evidence_id for item in request.evidence
    }
    evidences_lookup: dict[str, RetrievedEvidence] = {
        item.evidence.evidence_id: item for item in request.evidence
    }
    for hypothesis in generated_hypotheses:
        if not hypothesis.supporting_evidence_ids:
            raise ValueError("missing evidence IDs")

        unknown_ids = set(hypothesis.supporting_evidence_ids) - known_evidence_ids
        if unknown_ids:
            raise ValueError("unknown evidence")

        supporting_evidences: list[RetrievedEvidence] = [
            evidences_lookup[supporting_evidence_id]
            for supporting_evidence_id in hypothesis.supporting_evidence_ids
        ]

        strengths = {item.strength for item in supporting_evidences}

        if EvidenceStrength.MISSING in strengths:
            raise ValueError("missing evidence")

        validated_hypotheses.append(hypothesis)

    return validated_hypotheses

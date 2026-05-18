from typing import Protocol

from pydantic import BaseModel, Field

from telemetry_agents.domain import Incident, InvestigationHypothesis
from telemetry_agents.domain.models import LOW_CONFIDENCE_THRESHOLD
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


def _max_confidence_for_evidence_strengths(strengths: set[EvidenceStrength]) -> float:
    if not strengths or EvidenceStrength.MISSING in strengths:
        return 0.0

    if strengths <= {EvidenceStrength.WEAK}:
        return 0.4

    if strengths <= {EvidenceStrength.WEAK, EvidenceStrength.MEDIUM}:
        return 0.8

    return 1.0


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

        max_confidence = _max_confidence_for_evidence_strengths(strengths)

        if hypothesis.confidence > max_confidence:
            updates: dict[str, str | float] = {"confidence": max_confidence}
            if max_confidence < LOW_CONFIDENCE_THRESHOLD and not hypothesis.uncertainty.strip():
                updates["uncertainty"] = "Confidence was reduced because the cited evidence is not strong enough to support a higher-confidence hypothesis."
            hypothesis = hypothesis.model_copy(update=updates)

        validated_hypotheses.append(hypothesis)

    return validated_hypotheses

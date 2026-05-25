from pydantic import BaseModel, Field

from telemetry_agents.domain import (
    CritiqueFindingType,
    HumanReviewAssessment,
    HypothesisValidationResult,
    HypothesisCritiqueFinding, Incident,
)
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


class HumanReviewIncident(BaseModel):
    incident_id: str
    title: str
    service: str
    impact: str


class HumanReviewEvidence(BaseModel):
    evidence_id: str
    summary: str
    citation: str
    strength: EvidenceStrength


class HumanReviewHypothesis(BaseModel):
    hypothesis_id: str
    statement: str
    confidence: float
    uncertainty: str | None = None
    supporting_evidence: list[HumanReviewEvidence] = Field(default_factory=list)


class HumanReviewCriticFinding(BaseModel):
    hypothesis_id: str
    finding_type: CritiqueFindingType
    reason: str
    evidence: list[HumanReviewEvidence] = Field(default_factory=list)


class HumanReviewPacket(BaseModel):
    incident: HumanReviewIncident
    reason: str = "report_review_required"
    escalation_reason: str
    hypotheses: list[HumanReviewHypothesis] = Field(default_factory=list)
    critic_findings: list[HumanReviewCriticFinding] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def build_human_review_packet(
    incident: Incident,
    assessment: HumanReviewAssessment,
    validation_result: HypothesisValidationResult,
    critique_findings: list[HypothesisCritiqueFinding],
    collected_evidence: list[RetrievedEvidence],
    warnings: list[str],
) -> HumanReviewPacket:
    evidence_by_id = {item.evidence.evidence_id: item for item in collected_evidence}
    mapped_hypotheses = []
    for hypothesis in validation_result.accepted_hypotheses:
        mapped_evidence = []
        for evidence_id in hypothesis.supporting_evidence_ids:
            source_evidence = evidence_by_id[evidence_id]
            mapped_evidence.append(
                HumanReviewEvidence(
                    strength=source_evidence.strength,
                    evidence_id=evidence_id,
                    summary=source_evidence.evidence.summary,
                    citation=source_evidence.evidence.citation,
                )
            )
        mapped_hypotheses.append(
            HumanReviewHypothesis(
                hypothesis_id=hypothesis.hypothesis_id,
                uncertainty=hypothesis.uncertainty,
                confidence=hypothesis.confidence,
                statement=hypothesis.statement,
                supporting_evidence=mapped_evidence,
            )
        )

    mapped_critique_findings = []
    for critique_finding in critique_findings:
        mapped_evidence = []
        for evidence_id in critique_finding.evidence_ids:
            source_evidence = evidence_by_id[evidence_id]
            mapped_evidence.append(
                HumanReviewEvidence(
                    strength=source_evidence.strength,
                    evidence_id=evidence_id,
                    summary=source_evidence.evidence.summary,
                    citation=source_evidence.evidence.citation,
                )
            )

        mapped_critique_findings.append(
            HumanReviewCriticFinding(
                hypothesis_id=critique_finding.hypothesis_id,
                reason=critique_finding.reason,
                evidence=mapped_evidence,
                finding_type=critique_finding.finding_type,
            )
        )

    if not assessment.human_review_reason:
        raise ValueError("human_review_reason is required before report review")

    incident = HumanReviewIncident(
        incident_id=incident.incident_id,
        service=incident.service,
        title=incident.title,
        impact=incident.impact,
    )

    return HumanReviewPacket(
        incident=incident,
        escalation_reason=assessment.human_review_reason,
        hypotheses=mapped_hypotheses,
        critic_findings=mapped_critique_findings,
        warnings=warnings,
    )

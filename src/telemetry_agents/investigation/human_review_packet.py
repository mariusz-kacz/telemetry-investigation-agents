from dataclasses import dataclass

from telemetry_agents.domain import (
    CritiqueFindingType,
    HumanReviewAssessment,
    HypothesisValidationResult,
    HypothesisCritiqueFinding,
    Incident,
    HypothesisCategory,
)
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


@dataclass(frozen=True)
class HumanReviewIncident:
    incident_id: str
    title: str
    service: str
    impact: str


@dataclass(frozen=True)
class HumanReviewEvidence:
    evidence_id: str
    summary: str
    citation: str
    strength: EvidenceStrength


@dataclass(frozen=True)
class HumanReviewHypothesis:
    hypothesis_id: str
    statement: str
    category: HypothesisCategory
    confidence: float
    supporting_evidence: list[HumanReviewEvidence]
    uncertainty: str | None = None


@dataclass(frozen=True)
class HumanReviewCriticFinding:
    hypothesis_id: str
    finding_type: CritiqueFindingType
    reason: str
    evidence: list[HumanReviewEvidence]


@dataclass(frozen=True)
class HumanReviewPacket:
    incident: HumanReviewIncident
    escalation_reason: str
    hypotheses: list[HumanReviewHypothesis]
    critic_findings: list[HumanReviewCriticFinding]
    warnings: list[str]
    reason: str = "report_review_required"


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
    for hypothesis in validation_result.validated_hypotheses:
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
                category=hypothesis.category,
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

    human_review_incident = HumanReviewIncident(
        incident_id=incident.incident_id,
        service=incident.service,
        title=incident.title,
        impact=incident.impact,
    )

    return HumanReviewPacket(
        incident=human_review_incident,
        escalation_reason=assessment.human_review_reason,
        hypotheses=mapped_hypotheses,
        critic_findings=mapped_critique_findings,
        warnings=warnings,
    )

from telemetry_agents.domain import (
    ReviewedHypothesis,
    InvestigationReport,
    Incident,
    HypothesisReviewStatus,
    HumanReviewStatus,
)
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence


def build_investigation_report(
    incident: Incident,
    reviewed_hypotheses: list[ReviewedHypothesis],
    collected_evidence: list[RetrievedEvidence],
    human_review_status: HumanReviewStatus,
) -> InvestigationReport:
    evidence_by_id = {item.evidence.evidence_id: item for item in collected_evidence}
    accepted_hypotheses = [
        item
        for item in reviewed_hypotheses
        if item.status is HypothesisReviewStatus.ACCEPTED
    ]
    top_hypothesis = (
        max(
            accepted_hypotheses,
            key=lambda item: item.hypothesis.confidence,
        )
        if accepted_hypotheses
        else None
    )

    if not top_hypothesis:
        return InvestigationReport(
            incident_id=incident.incident_id,
            summary="No accepted hypothesis is available for automatic reporting.",
            confidence=0,
            uncertainty="All candidate hypotheses were blocked, disputed, or unavailable.",
            evidence_citations=[],
            selected_hypothesis_id=None,
            category=None,
            human_review_status=human_review_status,
        )

    mapped_evidence = []
    for evidence_id in top_hypothesis.hypothesis.supporting_evidence_ids:
        source_evidence = evidence_by_id.get(evidence_id)
        if source_evidence is None:
            raise ValueError(
                f"Hypothesis references unknown evidence ID: {evidence_id}"
            )

        mapped_evidence.append(source_evidence.evidence)

    return InvestigationReport(
        incident_id=incident.incident_id,
        summary=top_hypothesis.hypothesis.statement,
        confidence=top_hypothesis.hypothesis.confidence,
        uncertainty=top_hypothesis.hypothesis.uncertainty,
        evidence_citations=mapped_evidence,
        selected_hypothesis_id=top_hypothesis.hypothesis.hypothesis_id,
        category=top_hypothesis.hypothesis.category,
        human_review_status=human_review_status,
    )

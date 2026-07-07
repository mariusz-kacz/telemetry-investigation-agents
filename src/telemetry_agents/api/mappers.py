from telemetry_agents.api.schemas import (
    EvidenceResponse,
    FinalReportResponse,
    HypothesisResponse,
    IncidentResponse,
    InvestigationResponse,
    InvestigationRunResponse,
    InvestigationRunSummaryResponse,
    ReportCitationResponse,
    TopHypothesisResponse,
)
from telemetry_agents.app.demo_investigation_service import (
    DemoInvestigationResult,
    InvestigationRunResult,
)
from telemetry_agents.domain import HypothesisReviewStatus, ReviewedHypothesis


def _top_accepted_hypothesis(
    hypotheses: list[ReviewedHypothesis],
) -> ReviewedHypothesis | None:
    accepted_hypotheses = [
        item for item in hypotheses if item.status is HypothesisReviewStatus.ACCEPTED
    ]
    return (
        max(accepted_hypotheses, key=lambda item: item.hypothesis.confidence)
        if accepted_hypotheses
        else None
    )


def to_investigation_response(result: DemoInvestigationResult) -> InvestigationResponse:
    top_hypothesis = _top_accepted_hypothesis(result.hypotheses)

    return InvestigationResponse(
        run_id=result.run_id,
        case_id=result.case_id,
        demo_provider=result.demo_provider,
        incident=IncidentResponse(
            id=result.incident.incident_id,
            service=result.incident.service,
            impact=result.incident.impact,
            title=result.incident.title,
        ),
        evidence=[
            EvidenceResponse(
                evidence_id=retrieved_evidence.evidence.evidence_id,
                summary=retrieved_evidence.evidence.summary,
                citation=retrieved_evidence.evidence.citation,
                strength=retrieved_evidence.strength,
                source=retrieved_evidence.evidence.source,
            )
            for retrieved_evidence in result.evidence
        ],
        status=result.status.value.lower(),
        hypotheses=[
            HypothesisResponse(
                id=reviewed.hypothesis.hypothesis_id,
                summary=reviewed.hypothesis.statement,
                confidence=reviewed.hypothesis.confidence,
                status=reviewed.status,
                evidence_ids=list(reviewed.hypothesis.supporting_evidence_ids),
            )
            for reviewed in result.hypotheses
        ],
        top_hypothesis=(
            TopHypothesisResponse(
                id=top_hypothesis.hypothesis.hypothesis_id,
                statement=top_hypothesis.hypothesis.statement,
                category=top_hypothesis.hypothesis.category,
                confidence=top_hypothesis.hypothesis.confidence,
                review_status=top_hypothesis.status,
                evidence_ids=list(top_hypothesis.hypothesis.supporting_evidence_ids),
            )
            if top_hypothesis
            else None
        ),
        human_review_required=result.human_review_required,
        review_reasons=list(result.review_reasons),
        warnings=list(result.warnings),
        report_ready=result.report_ready,
        final_report=(
            FinalReportResponse(
                incident_id=result.final_report.incident_id,
                summary=result.final_report.summary,
                confidence=result.final_report.confidence,
                uncertainty=result.final_report.uncertainty,
                selected_hypothesis_id=result.final_report.selected_hypothesis_id,
                category=result.final_report.category,
                human_review_status=result.final_report.human_review_status,
                evidence_citations=[
                    ReportCitationResponse(
                        evidence_id=evidence.evidence_id,
                        source=evidence.source,
                        summary=evidence.summary,
                        citation=evidence.citation,
                    )
                    for evidence in result.final_report.evidence_citations
                ],
            )
            if result.final_report
            else None
        ),
    )


def to_run_summary_response(
    runs: list[InvestigationRunResult],
) -> InvestigationRunSummaryResponse:
    return InvestigationRunSummaryResponse(
        runs=[
            InvestigationRunResponse(
                run_id=run.run_id,
                case_id=run.case_id,
                demo_provider=run.demo_provider,
                incident_id=run.incident_id,
                status=run.status.value.lower(),
            )
            for run in runs
        ]
    )

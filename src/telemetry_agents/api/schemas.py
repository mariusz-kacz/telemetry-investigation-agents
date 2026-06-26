from pydantic import BaseModel, Field


class InvestigationRequest(BaseModel):
    case_id: str = Field(min_length=1)


class HypothesisResponse(BaseModel):
    id: str
    summary: str
    confidence: float
    status: str
    evidence_ids: list[str]


class HumanReviewRequest(BaseModel):
    approved: bool


class IncidentResponse(BaseModel):
    id: str
    title: str
    service: str
    impact: str


class TopHypothesisResponse(BaseModel):
    id: str
    statement: str
    category: str
    confidence: float
    review_status: str
    evidence_ids: list[str]


class EvidenceResponse(BaseModel):
    evidence_id: str
    source: str
    summary: str
    citation: str
    strength: str


class ReportCitationResponse(BaseModel):
    evidence_id: str
    source: str
    summary: str
    citation: str


class FinalReportResponse(BaseModel):
    incident_id: str
    summary: str
    confidence: float
    uncertainty: str | None
    selected_hypothesis_id: str | None
    category: str | None
    human_review_status: str
    evidence_citations: list[ReportCitationResponse]


class InvestigationResponse(BaseModel):
    run_id: str
    case_id: str
    demo_provider: str
    status: str
    incident: IncidentResponse
    top_hypothesis: TopHypothesisResponse | None
    hypotheses: list[HypothesisResponse]
    evidence: list[EvidenceResponse]
    human_review_required: bool
    review_reasons: list[str]
    warnings: list[str]
    report_ready: bool
    final_report: FinalReportResponse | None


class InvestigationRunResponse(BaseModel):
    run_id: str
    case_id: str
    demo_provider: str
    incident_id: str
    status: str


class InvestigationRunSummaryResponse(BaseModel):
    runs: list[InvestigationRunResponse]

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


class InvestigationResponse(BaseModel):
    run_id: str
    case_id: str
    status: str
    incident: IncidentResponse
    top_hypothesis: TopHypothesisResponse | None
    hypotheses: list[HypothesisResponse]
    evidence: list[EvidenceResponse]
    human_review_required: bool
    review_reasons: list[str]
    warnings: list[str]
    report_ready: bool


class InvestigationRunResponse(BaseModel):
    run_id: str
    case_id: str
    incident_id: str
    status: str


class InvestigationRunSummaryResponse(BaseModel):
    runs: list[InvestigationRunResponse]

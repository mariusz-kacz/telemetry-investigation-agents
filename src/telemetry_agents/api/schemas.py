from pydantic import BaseModel, Field


class InvestigationRequest(BaseModel):
    case_id: str = Field(min_length=1)


class HypothesisResponse(BaseModel):
    id: str
    summary: str
    confidence: float
    status: str
    evidence_ids: list[str]


class InvestigationResponse(BaseModel):
    run_id: str
    incident_id: str
    hypotheses: list[HypothesisResponse]
    human_review_required: bool
    review_reasons: list[str]


class HumanReviewRequest(BaseModel):
    approved: bool

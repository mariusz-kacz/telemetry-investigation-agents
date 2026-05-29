from pydantic import BaseModel, Field

from telemetry_agents.domain import EvidenceSource
from telemetry_agents.domain.models import HypothesisValidationResult
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence


class EvalExpectedEvidenceSource(BaseModel):
    source: EvidenceSource
    source_file: str = Field(min_length=1)


class EvalCase(BaseModel):
    case_id: str = Field(min_length=1)
    incident_file: str = Field(min_length=1)
    expected_category: str = Field(min_length=1)
    expected_evidence_sources: list[EvalExpectedEvidenceSource]
    acceptable_hypothesis_terms: list[str] = Field(default_factory=list)
    forbidden_unsupported_claims: list[str] = Field(default_factory=list)
    expected_human_review_required: bool


class EvaluationRunOutput(BaseModel):
    retrieved_evidence: list[RetrievedEvidence] = Field(default_factory=list)
    validation_result: HypothesisValidationResult | None = None
    warnings: list[str] = Field(default_factory=list)


class ExpectedEvidenceSourceDetail(BaseModel):
    source_file: str
    source: EvidenceSource


class ExpectedEvidenceSourcesScore(BaseModel):
    passed: bool
    matched_expected_sources: list[ExpectedEvidenceSourceDetail] = Field(
        default_factory=list
    )
    missing_expected_sources: list[ExpectedEvidenceSourceDetail] = Field(
        default_factory=list
    )


class HypothesisCategoryCorrectnessScore(BaseModel):
    passed: bool
    expected_category: str
    matched_hypothesis_ids: list[str] = Field(default_factory=list)
    observed_categories: list[str] = Field(default_factory=list)

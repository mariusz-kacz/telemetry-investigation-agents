from enum import StrEnum

from pydantic import BaseModel, Field

from telemetry_agents.domain import EvidenceSource
from telemetry_agents.domain.models import HypothesisValidationResult
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence


class HypothesisCategory(StrEnum):
    DATABASE_TIMEOUT = "database_timeout"
    AUTHENTICATION_FAILURE = "authentication_failure"
    DOWNSTREAM_DEPENDENCY_LATENCY = "downstream_dependency_latency"
    METRIC_ANOMALY = "metric_anomaly"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class EvalExpectedEvidenceSource(BaseModel):
    source: EvidenceSource
    source_file: str = Field(min_length=1)


class EvalCase(BaseModel):
    case_id: str = Field(min_length=1)
    incident_file: str = Field(min_length=1)
    expected_category: HypothesisCategory = Field(min_length=1)
    expected_evidence_sources: list[EvalExpectedEvidenceSource]
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


class ExpectedHypothesisCategoryScore(BaseModel):
    passed: bool
    expected_category: str
    matched_hypothesis_ids: list[str] = Field(default_factory=list)
    observed_categories: list[HypothesisCategory] = Field(default_factory=list)


class EvaluationScorecard(BaseModel):
    case_id: str = Field(min_length=1)
    passed: bool
    expected_evidence_sources_score: ExpectedEvidenceSourcesScore
    expected_category_score: ExpectedHypothesisCategoryScore

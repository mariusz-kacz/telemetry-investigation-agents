from pydantic import BaseModel, Field

from telemetry_agents.domain import (
    EvidenceSource,
    HumanReviewAssessment,
    HypothesisCategory,
    HypothesisValidationResult,
)
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence
from telemetry_agents.evaluation.unsupported_claim_review import UnsupportedClaimFinding


class EvalExpectedEvidenceSource(BaseModel):
    source: EvidenceSource
    source_file: str = Field(min_length=1)


class EvalCase(BaseModel):
    case_id: str = Field(min_length=1)
    incident_file: str = Field(min_length=1)

    expected_category: HypothesisCategory = Field(min_length=1)
    expected_evidence_sources: list[EvalExpectedEvidenceSource]
    expected_human_review_required: bool


class EvaluationRunOutput(BaseModel):
    retrieved_evidence: list[RetrievedEvidence] = Field(default_factory=list)
    validation_result: HypothesisValidationResult | None = None
    human_review_assessment: HumanReviewAssessment | None = None
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


class ExpectedHumanReviewScore(BaseModel):
    passed: bool
    expected_human_review_required: bool
    actual_human_review_required: bool | None


class CitationCorrectnessScore(BaseModel):
    passed: bool
    hypotheses_without_citations: list[str] = Field(default_factory=list)
    unknown_evidence_references: dict[str, list[str]] = Field(default_factory=dict)
    missing_evidence_references: dict[str, list[str]] = Field(default_factory=dict)


class UnsupportedClaimScore(BaseModel):
    passed: bool
    findings: list[UnsupportedClaimFinding] = Field(default_factory=list)


class EvaluationScorecard(BaseModel):
    case_id: str = Field(min_length=1)
    passed: bool
    expected_evidence_sources_score: ExpectedEvidenceSourcesScore
    expected_category_score: ExpectedHypothesisCategoryScore
    expected_human_review_score: ExpectedHumanReviewScore
    citation_correctness_score: CitationCorrectnessScore
    unsupported_claim_score: UnsupportedClaimScore

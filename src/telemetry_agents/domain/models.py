from enum import StrEnum
from typing import Annotated

from pydantic import (
    BaseModel,
    Field,
    model_validator,
    StringConstraints,
    AfterValidator,
)

LOW_CONFIDENCE_THRESHOLD = 0.8

NonEmptyStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
    ),
]


def ensure_unique_ids(values: list[str]) -> list[str]:
    if len(values) != len(set(values)):
        raise ValueError("must not contain duplicate IDs")
    return values


UniqueIdList = Annotated[
    list[NonEmptyStr],
    AfterValidator(ensure_unique_ids),
]


def ensure_unique(values: list[str], *, label: str) -> set[str]:
    unique = set(values)
    if len(unique) != len(values):
        raise ValueError(f"duplicate {label} IDs are not allowed")
    return unique


class EvidenceSource(StrEnum):
    LOG = "log"
    TRACE = "trace"
    METRIC = "metric"


class CritiqueFindingType(StrEnum):
    CONTRADICTION = "contradiction"
    UNSUPPORTED_CAUSAL_LEAP = "unsupported_causal_leap"
    ALTERNATIVE_INTERPRETATION = "alternative_interpretation"
    OVERSTATED_CONFIDENCE = "overstated_confidence"


class HumanReviewStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    APPROVED = "approved"
    REJECTED = "rejected"


class IncidentImpact(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class HypothesisCategory(StrEnum):
    DATABASE_FAILURE = "database_failure"
    AUTHENTICATION_FAILURE = "authentication_failure"
    DOWNSTREAM_DEPENDENCY_FAILURE = "downstream_dependency_failure"
    RESOURCE_SATURATION = "resource_saturation"
    NETWORK_FAILURE = "network_failure"
    CONFIGURATION_ERROR = "configuration_error"
    APPLICATION_ERROR = "application_error"
    METRIC_ANOMALY = "metric_anomaly"
    OTHER = "other"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class Incident(BaseModel):
    incident_id: NonEmptyStr
    title: NonEmptyStr
    service: NonEmptyStr
    impact: IncidentImpact


class TelemetryEvidence(BaseModel):
    evidence_id: NonEmptyStr
    source: EvidenceSource
    summary: NonEmptyStr
    citation: NonEmptyStr
    service: NonEmptyStr


class InvestigationHypothesis(BaseModel):
    hypothesis_id: NonEmptyStr
    statement: NonEmptyStr
    category: HypothesisCategory
    supporting_evidence_ids: UniqueIdList = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainty: NonEmptyStr | None = None

    @model_validator(mode="after")
    def must_have_uncertainty_if_not_confident(self) -> "InvestigationHypothesis":
        if self.confidence < LOW_CONFIDENCE_THRESHOLD and self.uncertainty is None:
            raise ValueError(
                f"uncertainty is required when confidence is below {LOW_CONFIDENCE_THRESHOLD}"
            )
        return self


class RejectedHypothesis(BaseModel):
    hypothesis: InvestigationHypothesis
    reason: NonEmptyStr


class ConfidenceAdjustment(BaseModel):
    hypothesis_id: NonEmptyStr
    original_confidence: float = Field(ge=0.0, le=1.0)
    adjusted_confidence: float = Field(ge=0.0, le=1.0)
    reason: NonEmptyStr

    @model_validator(mode="after")
    def adjusted_confidence_should_be_smaller_than_original_confidence(
        self,
    ) -> "ConfidenceAdjustment":
        if self.adjusted_confidence >= self.original_confidence:
            raise ValueError(
                "Adjusted confidence must be lower than original confidence"
            )
        return self


class HypothesisValidationResult(BaseModel):
    accepted_hypotheses: list[InvestigationHypothesis] = Field(default_factory=list)
    rejected_hypotheses: list[RejectedHypothesis] = Field(default_factory=list)
    confidence_adjustments: list[ConfidenceAdjustment] = Field(default_factory=list)

    @model_validator(mode="after")
    def references_must_be_consistent(self) -> "HypothesisValidationResult":
        accepted_ids = ensure_unique(
            [item.hypothesis_id for item in self.accepted_hypotheses],
            label="accepted hypothesis",
        )
        rejected_ids = ensure_unique(
            [item.hypothesis.hypothesis_id for item in self.rejected_hypotheses],
            label="rejected hypothesis",
        )
        adjusted_ids = ensure_unique(
            [item.hypothesis_id for item in self.confidence_adjustments],
            label="confidence adjustment hypothesis",
        )

        if accepted_ids & rejected_ids:
            raise ValueError(
                "same hypothesis ids found in accepted and rejected hypotheses"
            )

        if not adjusted_ids <= accepted_ids:
            raise ValueError(
                "confidence adjustments should refer to accepted hypotheses"
            )

        return self


class HypothesisCritiqueFinding(BaseModel):
    hypothesis_id: NonEmptyStr
    evidence_ids: UniqueIdList = Field(min_length=1)
    finding_type: CritiqueFindingType
    reason: NonEmptyStr


class HypothesisCritiqueResult(BaseModel):
    critique_findings: list[HypothesisCritiqueFinding] = Field(default_factory=list)


class HumanReviewAssessment(BaseModel):
    human_review_required: bool
    human_review_reason: NonEmptyStr | None = None

    @model_validator(mode="after")
    def must_have_reason_if_review_required(self) -> "HumanReviewAssessment":
        if self.human_review_required and self.human_review_reason is None:
            raise ValueError("reason is required if human review is required")
        return self

    @model_validator(mode="after")
    def must_not_have_reason_if_review_not_required(self) -> "HumanReviewAssessment":
        if (
            not self.human_review_required
            and self.human_review_reason
            and self.human_review_reason.strip()
        ):
            raise ValueError("Reason must not be added if human review is not required")
        return self


class InvestigationReport(BaseModel):
    incident_id: NonEmptyStr
    summary: NonEmptyStr
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainty: NonEmptyStr | None = None

    @model_validator(mode="after")
    def must_have_uncertainty_if_not_confident(self) -> "InvestigationReport":
        if self.confidence < LOW_CONFIDENCE_THRESHOLD and self.uncertainty is None:
            raise ValueError(
                f"uncertainty is required when confidence is below {LOW_CONFIDENCE_THRESHOLD}"
            )
        return self

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator

LOW_CONFIDENCE_THRESHOLD = 0.8


class EvidenceSource(StrEnum):
    LOG = "log"
    TRACE = "trace"
    METRIC = "metric"


class CritiqueFindingType(StrEnum):
    CONTRADICTION = "contradiction"
    UNSUPPORTED_CAUSAL_LEAP = "unsupported_causal_leap"
    ALTERNATIVE_INTERPRETATION = "alternative_interpretation"
    OVERSTATED_CONFIDENCE = "overstated_confidence"


class Incident(BaseModel):
    incident_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    service: str = Field(min_length=1)

    @field_validator("incident_id", "title", "service")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class TelemetryEvidence(BaseModel):
    evidence_id: str = Field(min_length=1)
    source: EvidenceSource
    summary: str = Field(min_length=1)
    citation: str = Field(min_length=1)
    service: str = Field(min_length=1)

    @field_validator("evidence_id", "summary", "citation", "service")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class InvestigationHypothesis(BaseModel):
    hypothesis_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainty: str = ""

    @field_validator("hypothesis_id", "statement")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @model_validator(mode="after")
    def must_have_uncertainty_if_not_confident(self) -> "InvestigationHypothesis":
        if self.confidence < LOW_CONFIDENCE_THRESHOLD and not self.uncertainty.strip():
            raise ValueError("uncertainty is required when confidence is below 0.8")
        return self


class RejectedHypothesis(BaseModel):
    hypothesis: InvestigationHypothesis
    reason: str = Field(min_length=1)

    @field_validator("reason")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class ConfidenceAdjustment(BaseModel):
    hypothesis_id: str = Field(min_length=1)
    original_confidence: float = Field(ge=0.0, le=1.0)
    adjusted_confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)

    @field_validator("hypothesis_id", "reason")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

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
        accepted_ids = {item.hypothesis_id for item in self.accepted_hypotheses}
        rejected_ids = {
            item.hypothesis.hypothesis_id for item in self.rejected_hypotheses
        }

        if accepted_ids & rejected_ids:
            raise ValueError(
                "same hypothesis ids found in accepted and rejected hypotheses"
            )

        adjusted_ids = {item.hypothesis_id for item in self.confidence_adjustments}
        if not adjusted_ids <= accepted_ids:
            raise ValueError(
                "confidence adjustments should refer to accepted hypotheses"
            )

        return self


class HypothesisCritiqueFinding(BaseModel):
    hypothesis_id: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    finding_type: CritiqueFindingType
    reason: str = Field(min_length=1)

    @field_validator("hypothesis_id", "reason")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @field_validator("evidence_ids")
    @classmethod
    def items_must_not_be_blank(cls, value: list[str]) -> list[str]:
        for evidence_id in value:
            if not evidence_id.strip():
                raise ValueError("must not have blank items")
        return value


class HypothesisCritiqueResult(BaseModel):
    critique_findings: list[HypothesisCritiqueFinding] = Field(default_factory=list)


class InvestigationReport(BaseModel):
    incident_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainty: str

    @field_validator("incident_id", "summary")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @model_validator(mode="after")
    def must_have_uncertainty_if_not_confident(self) -> "InvestigationReport":
        if self.confidence < LOW_CONFIDENCE_THRESHOLD and not self.uncertainty.strip():
            raise ValueError("uncertainty is required when confidence is below 0.8")
        return self

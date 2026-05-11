from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator

LOW_CONFIDENCE_THRESHOLD = 0.8


class EvidenceSource(StrEnum):
    LOG = "log"
    TRACE = "trace"
    METRIC = "metric"
    DEPLOYMENT = "deployment"


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

    @field_validator("hypothesis_id", "statement")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


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

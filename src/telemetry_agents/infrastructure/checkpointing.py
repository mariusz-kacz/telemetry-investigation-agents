import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from telemetry_agents.domain.models import (
    ConfidenceAdjustment,
    CritiqueFindingType,
    EvidenceSource,
    HumanReviewAssessment,
    HumanReviewStatus,
    HypothesisCategory,
    HypothesisCritiqueFinding,
    HypothesisReviewResult,
    HypothesisReviewStatus,
    HypothesisValidationResult,
    Incident,
    IncidentImpact,
    IncidentInvestigationWindow,
    IncidentRetrievalHints,
    InvestigationHypothesis,
    InvestigationReport,
    RejectedHypothesis,
    ReviewedHypothesis,
    TelemetryEvidence,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


def create_checkpoint_serializer() -> JsonPlusSerializer:
    return JsonPlusSerializer(
        allowed_msgpack_modules=[
            ConfidenceAdjustment,
            CritiqueFindingType,
            EvidenceSource,
            HumanReviewAssessment,
            HumanReviewStatus,
            HypothesisCategory,
            HypothesisCritiqueFinding,
            HypothesisReviewResult,
            HypothesisReviewStatus,
            HypothesisValidationResult,
            Incident,
            IncidentImpact,
            IncidentInvestigationWindow,
            IncidentRetrievalHints,
            InvestigationHypothesis,
            InvestigationReport,
            RejectedHypothesis,
            ReviewedHypothesis,
            TelemetryEvidence,
            CitationMetadata,
            RetrievedEvidence,
            EvidenceStrength,
        ]
    )


def create_sqlite_checkpointer(
    db_path: Path,
) -> SqliteSaver:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    return SqliteSaver(conn, serde=create_checkpoint_serializer())

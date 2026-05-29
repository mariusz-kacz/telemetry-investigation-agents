"""Evaluation contracts for investigation workflow regression checks."""

from telemetry_agents.evaluation.models import (
    ExpectedEvidenceSourcesScore,
    ExpectedEvidenceSourceDetail,
    EvalCase,
    EvalExpectedEvidenceSource,
    EvaluationRunOutput,
    HypothesisCategory,
    HypothesisCategoryCorrectnessScore,
)
from telemetry_agents.evaluation.scoring import (
    score_expected_evidence_sources,
    score_expected_category,
)

__all__ = [
    "ExpectedEvidenceSourcesScore",
    "ExpectedEvidenceSourceDetail",
    "EvalCase",
    "EvalExpectedEvidenceSource",
    "EvaluationRunOutput",
    "HypothesisCategory",
    "HypothesisCategoryCorrectnessScore",
    "score_expected_evidence_sources",
    "score_expected_category",
]

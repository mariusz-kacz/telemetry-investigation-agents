"""Evaluation contracts for investigation workflow regression checks."""

from telemetry_agents.evaluation.models import (
    ExpectedEvidenceSourcesScore,
    ExpectedEvidenceSourceDetail,
    EvalCase,
    EvalExpectedEvidenceSource,
    EvaluationScorecard,
    EvaluationRunOutput,
    HypothesisCategory,
    ExpectedHypothesisCategoryScore,
)
from telemetry_agents.evaluation.runner import evaluate_case_output
from telemetry_agents.evaluation.scoring import (
    score_expected_evidence_sources,
    score_expected_category,
)

__all__ = [
    "ExpectedEvidenceSourcesScore",
    "ExpectedEvidenceSourceDetail",
    "EvalCase",
    "EvalExpectedEvidenceSource",
    "EvaluationScorecard",
    "EvaluationRunOutput",
    "HypothesisCategory",
    "ExpectedHypothesisCategoryScore",
    "evaluate_case_output",
    "score_expected_evidence_sources",
    "score_expected_category",
]

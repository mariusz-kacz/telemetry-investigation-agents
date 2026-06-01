"""Evaluation contracts for investigation workflow regression checks."""

from telemetry_agents.evaluation.models import (
    CitationCorrectnessScore,
    ExpectedEvidenceSourcesScore,
    ExpectedEvidenceSourceDetail,
    ExpectedHumanReviewScore,
    EvalCase,
    EvalExpectedEvidenceSource,
    EvaluationScorecard,
    EvaluationRunOutput,
    ExpectedHypothesisCategoryScore,
)
from telemetry_agents.evaluation.runner import evaluate_case_output
from telemetry_agents.evaluation.scoring import (
    score_citation_correctness,
    score_expected_evidence_sources,
    score_expected_category,
    score_expected_human_review,
)

__all__ = [
    "CitationCorrectnessScore",
    "ExpectedEvidenceSourcesScore",
    "ExpectedEvidenceSourceDetail",
    "ExpectedHumanReviewScore",
    "EvalCase",
    "EvalExpectedEvidenceSource",
    "EvaluationScorecard",
    "EvaluationRunOutput",
    "ExpectedHypothesisCategoryScore",
    "evaluate_case_output",
    "score_citation_correctness",
    "score_expected_evidence_sources",
    "score_expected_category",
    "score_expected_human_review",
]

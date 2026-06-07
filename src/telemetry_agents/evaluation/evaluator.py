from typing import Callable

from telemetry_agents.evaluation import (
    EvalCase,
    GuardedUnsupportedClaimReviewer,
    EvaluationRunOutput,
    EvaluationScorecard,
    score_expected_evidence_sources,
    score_expected_category,
    score_expected_human_review,
    score_citation_correctness,
    score_unsupported_claims,
)
from telemetry_agents.shared.observability import EVENT_EVAL_CASE_SCORED, emit_event


def _failed_dimensions(scorecard: EvaluationScorecard) -> list[str]:
    failed_dimensions: list[str] = []
    if not scorecard.expected_evidence_sources_score.passed:
        failed_dimensions.append("expected_evidence_sources")
    if not scorecard.expected_category_score.passed:
        failed_dimensions.append("expected_category")
    if not scorecard.expected_human_review_score.passed:
        failed_dimensions.append("expected_human_review")
    if not scorecard.citation_correctness_score.passed:
        failed_dimensions.append("citation_correctness")
    if not scorecard.unsupported_claim_score.passed:
        failed_dimensions.append("unsupported_claims")
    return failed_dimensions


def evaluate_case_output(
    *,
    case: EvalCase,
    output: EvaluationRunOutput,
    reviewer: GuardedUnsupportedClaimReviewer,
) -> EvaluationScorecard:
    """Build one evaluation scorecard for an eval case output."""
    sources_score = score_expected_evidence_sources(case=case, output=output)
    category_score = score_expected_category(case=case, output=output)
    human_review_score = score_expected_human_review(case=case, output=output)
    correctness_score = score_citation_correctness(output=output)
    unsupported_claim_score = score_unsupported_claims(output=output, reviewer=reviewer)
    scorecard = EvaluationScorecard(
        passed=sources_score.passed
        and category_score.passed
        and human_review_score.passed
        and correctness_score.passed
        and unsupported_claim_score.passed,
        case_id=case.case_id,
        expected_evidence_sources_score=sources_score,
        expected_category_score=category_score,
        expected_human_review_score=human_review_score,
        citation_correctness_score=correctness_score,
        unsupported_claim_score=unsupported_claim_score,
    )
    emit_event(
        EVENT_EVAL_CASE_SCORED,
        case_id=scorecard.case_id,
        passed=scorecard.passed,
        failed_dimensions=_failed_dimensions(scorecard),
    )
    return scorecard


def run_batch_evaluation(
    *,
    cases: list[EvalCase],
    run_case: Callable[[EvalCase], EvaluationRunOutput],
    reviewer: GuardedUnsupportedClaimReviewer,
) -> list[EvaluationScorecard]:
    eval_results: list[EvaluationScorecard] = []

    for case in cases:
        output = run_case(case)
        eval_results.append(
            evaluate_case_output(case=case, output=output, reviewer=reviewer)
        )

    return eval_results

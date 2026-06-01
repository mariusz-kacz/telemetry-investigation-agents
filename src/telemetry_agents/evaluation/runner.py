from telemetry_agents.evaluation.unsupported_claim_review import GuardedUnsupportedClaimReviewer
from telemetry_agents.evaluation.scoring import (
    score_expected_evidence_sources,
    score_expected_category,
    score_expected_human_review,
    score_citation_correctness,
    score_unsupported_claims,
)
from telemetry_agents.evaluation.models import (
    EvalCase,
    EvaluationRunOutput,
    EvaluationScorecard,
)


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
    return EvaluationScorecard(
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

from telemetry_agents.evaluation.models import (
    EvalCase,
    EvaluationRunOutput,
    ExpectedEvidenceSourceDetail,
    ExpectedEvidenceSourcesScore,
    ExpectedHumanReviewScore,
    ExpectedHypothesisCategoryScore,
)


def score_expected_evidence_sources(
    *,
    case: EvalCase,
    output: EvaluationRunOutput,
) -> ExpectedEvidenceSourcesScore:
    """Score whether retrieved evidence cites the expected source files."""
    expected_sources = {
        (item.source_file, item.source) for item in case.expected_evidence_sources
    }
    output_sources = {
        (item.citation.source_file, item.evidence.source)
        for item in output.retrieved_evidence
    }

    matched_expected_sources = sorted(output_sources & expected_sources)
    missing_expected_sources = sorted(expected_sources - output_sources)

    return ExpectedEvidenceSourcesScore(
        passed=not bool(missing_expected_sources),
        matched_expected_sources=[
            ExpectedEvidenceSourceDetail(source_file=source_file, source=source)
            for (source_file, source) in matched_expected_sources
        ],
        missing_expected_sources=[
            ExpectedEvidenceSourceDetail(source_file=source_file, source=source)
            for (source_file, source) in missing_expected_sources
        ],
    )


def score_expected_category(
    *,
    case: EvalCase,
    output: EvaluationRunOutput,
) -> ExpectedHypothesisCategoryScore:
    expected_category = case.expected_category
    matched_hypothesis_ids = []
    if output.validation_result:
        for hypothesis in output.validation_result.accepted_hypotheses:
            if expected_category == hypothesis.category:
                matched_hypothesis_ids.append(hypothesis.hypothesis_id)

    return ExpectedHypothesisCategoryScore(
        passed=bool(matched_hypothesis_ids),
        expected_category=expected_category,
        matched_hypothesis_ids=matched_hypothesis_ids,
    )


def score_expected_human_review(
    *,
    case: EvalCase,
    output: EvaluationRunOutput,
) -> ExpectedHumanReviewScore:
    """Score whether the workflow produced the expected human-review decision."""
    if output.human_review_assessment is None:
        return ExpectedHumanReviewScore(
            passed=False,
            expected_human_review_required=case.expected_human_review_required,
            actual_human_review_required=None,
        )

    actual_human_review_required = output.human_review_assessment.human_review_required

    return ExpectedHumanReviewScore(
        passed=case.expected_human_review_required == actual_human_review_required,
        expected_human_review_required=case.expected_human_review_required,
        actual_human_review_required=actual_human_review_required,
    )

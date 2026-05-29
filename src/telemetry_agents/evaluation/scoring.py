from telemetry_agents.evaluation.models import (
    EvalCase,
    EvaluationRunOutput,
    ExpectedEvidenceSourceDetail,
    ExpectedEvidenceSourcesScore,
    HypothesisCategory,
    HypothesisCategoryCorrectnessScore,
)


GenericTermsRule = tuple[frozenset[str], HypothesisCategory]


GENERIC_TERMS_TO_CATEGORIES: tuple[GenericTermsRule, ...] = (
    (frozenset({"timeout", "database", "db"}), HypothesisCategory.DATABASE_TIMEOUT),
    (
        frozenset({"auth", "unauthorized", "token", "401", "403"}),
        HypothesisCategory.AUTHENTICATION_FAILURE,
    ),
    (
        frozenset({"downstream", "dependency", "upstream", "external"}),
        HypothesisCategory.DOWNSTREAM_DEPENDENCY_LATENCY,
    ),
    (frozenset({"metric", "anomaly", "spike"}), HypothesisCategory.METRIC_ANOMALY),
)


def _classify_hypothesis_categories(statement: str) -> set[HypothesisCategory]:
    normalized = statement.lower()
    categories: set[HypothesisCategory] = set()

    for keywords, category in GENERIC_TERMS_TO_CATEGORIES:
        if any(keyword in normalized for keyword in keywords):
            categories.add(category)

    if not categories:
        categories.add(HypothesisCategory.INSUFFICIENT_EVIDENCE)

    return categories


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
) -> HypothesisCategoryCorrectnessScore:
    expected_category = case.expected_category
    matched_hypothesis_ids = []
    observed_categories: set[HypothesisCategory] = set()
    if output.validation_result:
        for hypothesis in output.validation_result.accepted_hypotheses:
            categories = _classify_hypothesis_categories(hypothesis.statement)
            if expected_category in categories:
                matched_hypothesis_ids.append(hypothesis.hypothesis_id)
            observed_categories.update(categories)

    return HypothesisCategoryCorrectnessScore(
        passed=bool(matched_hypothesis_ids),
        expected_category=expected_category,
        matched_hypothesis_ids=matched_hypothesis_ids,
        observed_categories=sorted(observed_categories),
    )

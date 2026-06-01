from telemetry_agents.domain import (
    EvidenceSource,
    HypothesisValidationResult,
    InvestigationHypothesis,
    TelemetryEvidence,
    HumanReviewAssessment,
    HypothesisCategory,
)
from telemetry_agents.evaluation import (
    EvalCase,
    EvalExpectedEvidenceSource,
    EvaluationRunOutput,
    evaluate_case_output,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


def _eval_case() -> EvalCase:
    return EvalCase(
        case_id="checkout-database-timeout",
        incident_file="sample_data/incidents/checkout-database-timeout.json",
        expected_category=HypothesisCategory.DATABASE_FAILURE,
        expected_evidence_sources=[
            EvalExpectedEvidenceSource(
                source=EvidenceSource.LOG,
                source_file="sample_data/logs/checkout-api.log",
            )
        ],
        forbidden_unsupported_claims=["cache poisoning"],
        expected_human_review_required=False,
    )


def _evaluation_run_output(
    statement: str = "Checkout latency is caused by database timeout errors.",
    category: HypothesisCategory = HypothesisCategory.DATABASE_FAILURE,
    source: EvidenceSource = EvidenceSource.LOG,
    human_review_required: bool = False,
) -> EvaluationRunOutput:
    return EvaluationRunOutput(
        retrieved_evidence=[
            RetrievedEvidence(
                evidence=TelemetryEvidence(
                    evidence_id="log-checkout-api-1",
                    source=source,
                    summary="Checkout API reports database timeout errors.",
                    citation="sample_data/logs/checkout-api.log:1",
                    service="checkout-api",
                ),
                citation=CitationMetadata(
                    source_file="sample_data/logs/checkout-api.log",
                    line_number=1,
                    service="checkout-api",
                    selection_reason="Matched incident query terms.",
                ),
                strength=EvidenceStrength.STRONG,
                relevance_score=1.0,
            )
        ],
        validation_result=HypothesisValidationResult(
            accepted_hypotheses=[
                InvestigationHypothesis(
                    hypothesis_id="hyp-001",
                    statement=statement,
                    category=category,
                    supporting_evidence_ids=["log-checkout-api-1"],
                    confidence=0.9,
                )
            ]
        ),
        human_review_assessment=HumanReviewAssessment(
            human_review_required=human_review_required,
            human_review_reason="Review reason" if human_review_required else None,
        ),
    )


def test_evaluate_case_output_combines_existing_scores() -> None:
    case = _eval_case()
    output = _evaluation_run_output()

    scorecard = evaluate_case_output(case=case, output=output)

    assert scorecard.case_id == "checkout-database-timeout"
    assert scorecard.passed is True
    assert scorecard.expected_category_score.passed is True
    assert scorecard.expected_evidence_sources_score.passed is True
    assert scorecard.expected_human_review_score.passed is True


def test_evaluate_case_output_fails_if_expected_category_score_fails() -> None:
    case = _eval_case()
    output = _evaluation_run_output(
        category=HypothesisCategory.DOWNSTREAM_DEPENDENCY_FAILURE
    )

    scorecard = evaluate_case_output(case=case, output=output)

    assert scorecard.case_id == "checkout-database-timeout"
    assert scorecard.passed is False
    assert scorecard.expected_category_score.passed is False
    assert scorecard.expected_evidence_sources_score.passed is True
    assert scorecard.expected_human_review_score.passed is True


def test_evaluate_case_output_fails_if_expected_evidence_sources_score_fails() -> None:
    case = _eval_case()
    output = _evaluation_run_output(source=EvidenceSource.METRIC)

    scorecard = evaluate_case_output(case=case, output=output)

    assert scorecard.case_id == "checkout-database-timeout"
    assert scorecard.passed is False
    assert scorecard.expected_category_score.passed is True
    assert scorecard.expected_evidence_sources_score.passed is False
    assert scorecard.expected_human_review_score.passed is True


def test_evaluate_case_output_fails_if_expected_human_review_score_fails() -> None:
    case = _eval_case()
    output = _evaluation_run_output(human_review_required=True)

    scorecard = evaluate_case_output(case=case, output=output)

    assert scorecard.case_id == "checkout-database-timeout"
    assert scorecard.passed is False
    assert scorecard.expected_category_score.passed is True
    assert scorecard.expected_evidence_sources_score.passed is True
    assert scorecard.expected_human_review_score.passed is False

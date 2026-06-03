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
from telemetry_agents.evaluation.unsupported_claim_review import (
    UnsupportedClaimReviewResult,
    UnsupportedClaimReviewRequest,
    GuardedUnsupportedClaimReviewer,
    UnsupportedClaimFinding,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


class FakeUnsupportedClaimAdapter:
    def __init__(self, result: UnsupportedClaimReviewResult) -> None:
        self.result = result
        self.requests: list[UnsupportedClaimReviewRequest] = []

    def review(
        self,
        request: UnsupportedClaimReviewRequest,
    ) -> UnsupportedClaimReviewResult:
        self.requests.append(request)
        return self.result


def _reviewer() -> GuardedUnsupportedClaimReviewer:
    adapter = FakeUnsupportedClaimAdapter(result=_review_result())
    return GuardedUnsupportedClaimReviewer(adapter=adapter)


def _review_result() -> UnsupportedClaimReviewResult:
    return UnsupportedClaimReviewResult(findings=[])


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
        expected_human_review_required=False,
    )


def _evaluation_run_output(
    statement: str = "Checkout latency is caused by database timeout errors.",
    category: HypothesisCategory = HypothesisCategory.DATABASE_FAILURE,
    source: EvidenceSource = EvidenceSource.LOG,
    supporting_evidence_id: str = "log-checkout-api-1",
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
            validated_hypotheses=[
                InvestigationHypothesis(
                    hypothesis_id="hyp-001",
                    statement=statement,
                    category=category,
                    supporting_evidence_ids=[supporting_evidence_id],
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
    reviewer = _reviewer()
    case = _eval_case()
    output = _evaluation_run_output()

    scorecard = evaluate_case_output(case=case, output=output, reviewer=reviewer)

    assert scorecard.case_id == "checkout-database-timeout"
    assert scorecard.passed is True
    assert scorecard.expected_category_score.passed is True
    assert scorecard.expected_evidence_sources_score.passed is True
    assert scorecard.expected_human_review_score.passed is True
    assert scorecard.citation_correctness_score.passed is True
    assert scorecard.unsupported_claim_score.passed is True


def test_evaluate_case_output_fails_if_expected_category_score_fails() -> None:
    reviewer = _reviewer()
    case = _eval_case()
    output = _evaluation_run_output(
        category=HypothesisCategory.DOWNSTREAM_DEPENDENCY_FAILURE
    )

    scorecard = evaluate_case_output(case=case, output=output, reviewer=reviewer)

    assert scorecard.case_id == "checkout-database-timeout"
    assert scorecard.passed is False
    assert scorecard.expected_category_score.passed is False
    assert scorecard.expected_evidence_sources_score.passed is True
    assert scorecard.expected_human_review_score.passed is True
    assert scorecard.citation_correctness_score.passed is True
    assert scorecard.unsupported_claim_score.passed is True


def test_evaluate_case_output_fails_if_expected_evidence_sources_score_fails() -> None:
    reviewer = _reviewer()
    case = _eval_case()
    output = _evaluation_run_output(source=EvidenceSource.METRIC)

    scorecard = evaluate_case_output(case=case, output=output, reviewer=reviewer)

    assert scorecard.case_id == "checkout-database-timeout"
    assert scorecard.passed is False
    assert scorecard.expected_category_score.passed is True
    assert scorecard.expected_evidence_sources_score.passed is False
    assert scorecard.expected_human_review_score.passed is True
    assert scorecard.citation_correctness_score.passed is True
    assert scorecard.unsupported_claim_score.passed is True


def test_evaluate_case_output_fails_if_expected_human_review_score_fails() -> None:
    reviewer = _reviewer()
    case = _eval_case()
    output = _evaluation_run_output(human_review_required=True)

    scorecard = evaluate_case_output(case=case, output=output, reviewer=reviewer)

    assert scorecard.case_id == "checkout-database-timeout"
    assert scorecard.passed is False
    assert scorecard.expected_category_score.passed is True
    assert scorecard.expected_evidence_sources_score.passed is True
    assert scorecard.expected_human_review_score.passed is False
    assert scorecard.citation_correctness_score.passed is True
    assert scorecard.unsupported_claim_score.passed is True


def test_evaluate_case_output_fails_if_citation_correctness_score_fails() -> None:
    reviewer = _reviewer()
    case = _eval_case()
    output = _evaluation_run_output(supporting_evidence_id="unknown-evidence-id")

    scorecard = evaluate_case_output(case=case, output=output, reviewer=reviewer)

    assert scorecard.case_id == "checkout-database-timeout"
    assert scorecard.passed is False
    assert scorecard.expected_category_score.passed is True
    assert scorecard.expected_evidence_sources_score.passed is True
    assert scorecard.expected_human_review_score.passed is True
    assert scorecard.citation_correctness_score.passed is False
    assert scorecard.unsupported_claim_score.passed is True


def test_evaluate_case_output_fails_if_unsupported_claim_score_fails() -> None:
    adapter = FakeUnsupportedClaimAdapter(
        result=UnsupportedClaimReviewResult(
            findings=[
                UnsupportedClaimFinding(
                    hypothesis_id="hyp-001",
                    evidence_ids=["log-checkout-api-1"],
                    reason=(
                        "The log reports database timeout errors, but it does not prove "
                        "that database resource exhaustion caused them."
                    ),
                    claim=(
                        "Database resource exhaustion caused checkout latency and "
                        "timeout errors."
                    ),
                )
            ],
        )
    )
    reviewer = GuardedUnsupportedClaimReviewer(adapter=adapter)

    case = _eval_case()
    output = _evaluation_run_output()

    scorecard = evaluate_case_output(case=case, output=output, reviewer=reviewer)

    assert scorecard.case_id == "checkout-database-timeout"
    assert scorecard.passed is False
    assert scorecard.expected_category_score.passed is True
    assert scorecard.expected_evidence_sources_score.passed is True
    assert scorecard.expected_human_review_score.passed is True
    assert scorecard.citation_correctness_score.passed is True
    assert scorecard.unsupported_claim_score.passed is False

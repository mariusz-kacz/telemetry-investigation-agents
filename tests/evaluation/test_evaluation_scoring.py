import pytest

from telemetry_agents.domain import (
    EvidenceSource,
    HumanReviewAssessment,
    TelemetryEvidence,
    InvestigationHypothesis,
    HypothesisValidationResult,
    HypothesisCategory,
)
from telemetry_agents.evaluation import (
    EvalCase,
    EvalExpectedEvidenceSource,
    EvaluationRunOutput,
    score_citation_correctness,
    score_expected_evidence_sources,
    score_expected_category,
    score_expected_human_review,
)
from telemetry_agents.evaluation.models import ExpectedEvidenceSourceDetail
from telemetry_agents.evaluation.scoring import score_unsupported_claims
from telemetry_agents.evaluation.unsupported_claim_review import (
    UnsupportedClaimFinding,
    UnsupportedClaimReviewRequest,
    UnsupportedClaimReviewResult,
    GuardedUnsupportedClaimReviewer,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.shared.paths import PROJECT_ROOT


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


def _eval_case(
    expected_evidence_sources: list[EvalExpectedEvidenceSource] | None = None,
    expected_category: HypothesisCategory = HypothesisCategory.DATABASE_FAILURE,
) -> EvalCase:
    if expected_evidence_sources is None:
        expected_evidence_sources = [
            EvalExpectedEvidenceSource(
                source=EvidenceSource.LOG,
                source_file="sample_data/logs/checkout-api.log",
            )
        ]

    return EvalCase(
        case_id="checkout-database-timeout",
        incident_file="sample_data/incidents/checkout-database-timeout.json",
        expected_category=expected_category,
        expected_evidence_sources=expected_evidence_sources,
        expected_human_review_required=False,
    )


def _retrieved_evidence(
    *,
    evidence_id: str = "log-checkout-api-1",
    source: EvidenceSource = EvidenceSource.LOG,
    source_file: str = "sample_data/logs/checkout-api.log",
    line_number: int = 1,
    service: str = "checkout-api",
) -> RetrievedEvidence:
    return RetrievedEvidence(
        evidence=TelemetryEvidence(
            evidence_id=evidence_id,
            source=source,
            summary="Checkout API reports database timeout errors.",
            citation=f"{source_file}:{line_number}",
            service=service,
        ),
        citation=CitationMetadata(
            source_file=source_file,
            line_number=line_number,
            service=service,
            selection_reason="Matched incident query terms.",
        ),
        strength=EvidenceStrength.STRONG,
        relevance_score=1.0,
    )


def _output(
    *,
    retrieved_evidence: list[RetrievedEvidence] | None = None,
    validated_hypotheses: list[InvestigationHypothesis] | None = None,
) -> EvaluationRunOutput:
    validation_result = None
    if validated_hypotheses is not None:
        validation_result = HypothesisValidationResult(
            validated_hypotheses=validated_hypotheses
        )

    return EvaluationRunOutput(
        retrieved_evidence=retrieved_evidence or [],
        validation_result=validation_result,
    )


def _hypothesis(
    hypothesis_id: str = "hyp-001",
    confidence: float = 0.9,
    uncertainty: str | None = None,
    statement: str = "Checkout latency is caused by database timeout errors.",
    category: HypothesisCategory = HypothesisCategory.DATABASE_FAILURE,
    supporting_evidence_ids: list[str] | None = None,
) -> InvestigationHypothesis:
    if supporting_evidence_ids is None:
        supporting_evidence_ids = ["log-001"]

    return InvestigationHypothesis(
        hypothesis_id=hypothesis_id,
        statement=statement,
        category=category,
        supporting_evidence_ids=supporting_evidence_ids,
        confidence=confidence,
        uncertainty=uncertainty,
    )


def test_expected_evidence_sources_passes_when_sources_are_present() -> None:
    case = _eval_case()
    output = _output(retrieved_evidence=[_retrieved_evidence()])

    score = score_expected_evidence_sources(case=case, output=output)

    assert score.passed is True
    assert score.matched_expected_sources == [
        ExpectedEvidenceSourceDetail(
            source_file="sample_data/logs/checkout-api.log", source=EvidenceSource.LOG
        )
    ]
    assert score.missing_expected_sources == []


def test_expected_evidence_sources_matches_absolute_output_to_relative_expected_path() -> None:
    case = _eval_case()
    output = _output(
        retrieved_evidence=[
            _retrieved_evidence(
                source_file=str(PROJECT_ROOT / "sample_data/logs/checkout-api.log")
            )
        ]
    )

    score = score_expected_evidence_sources(case=case, output=output)

    assert score.passed is True
    assert score.matched_expected_sources == [
        ExpectedEvidenceSourceDetail(
            source_file="sample_data/logs/checkout-api.log", source=EvidenceSource.LOG
        )
    ]
    assert score.missing_expected_sources == []


def test_citation_correctness_passes_when_validated_hypothesis_cites_retrieved_evidence() -> (
    None
):
    output = _output(
        retrieved_evidence=[_retrieved_evidence(evidence_id="log-001")],
        validated_hypotheses=[_hypothesis()],
    )

    score = score_citation_correctness(output=output)

    assert score.passed is True
    assert score.hypotheses_without_citations == []
    assert score.unknown_evidence_references == {}
    assert score.missing_evidence_references == {}


def test_citation_correctness_fails_when_validated_hypothesis_has_no_citations() -> None:
    output = _output(
        retrieved_evidence=[_retrieved_evidence(evidence_id="log-001")],
        validated_hypotheses=[_hypothesis(supporting_evidence_ids=[])],
    )

    score = score_citation_correctness(output=output)

    assert score.passed is False
    assert score.hypotheses_without_citations == ["hyp-001"]


def test_citation_correctness_fails_when_citation_is_not_retrieved() -> None:
    output = _output(
        retrieved_evidence=[_retrieved_evidence(evidence_id="log-001")],
        validated_hypotheses=[_hypothesis(supporting_evidence_ids=["unknown-log-001"])],
    )

    score = score_citation_correctness(output=output)

    assert score.passed is False
    assert score.unknown_evidence_references == {"hyp-001": ["unknown-log-001"]}


def test_citation_correctness_fails_when_citation_refers_to_missing_evidence() -> None:
    missing_evidence = _retrieved_evidence(evidence_id="missing-log-inc-001")
    missing_evidence.strength = EvidenceStrength.MISSING
    output = _output(
        retrieved_evidence=[missing_evidence],
        validated_hypotheses=[
            _hypothesis(supporting_evidence_ids=["missing-log-inc-001"])
        ],
    )

    score = score_citation_correctness(output=output)

    assert score.passed is False
    assert score.missing_evidence_references == {"hyp-001": ["missing-log-inc-001"]}


def test_citation_correctness_logs_all_defects() -> None:
    missing_evidence = _retrieved_evidence(evidence_id="missing-log-inc-001")
    missing_evidence.strength = EvidenceStrength.MISSING
    output = _output(
        retrieved_evidence=[missing_evidence],
        validated_hypotheses=[
            _hypothesis(
                supporting_evidence_ids=["missing-log-inc-001", "unknown-log-001"]
            )
        ],
    )

    score = score_citation_correctness(output=output)

    assert score.passed is False
    assert score.missing_evidence_references == {"hyp-001": ["missing-log-inc-001"]}
    assert score.unknown_evidence_references == {"hyp-001": ["unknown-log-001"]}


def test_citation_correctness_passes_when_validation_result_is_empty() -> None:
    output = _output(
        retrieved_evidence=[],
        validated_hypotheses=[],
    )

    score = score_citation_correctness(output=output)

    assert score.passed is True
    assert score.missing_evidence_references == {}
    assert score.unknown_evidence_references == {}


def test_citation_correctness_passes_when_validation_result_is_missing() -> None:
    output = _output(
        retrieved_evidence=[],
    )

    score = score_citation_correctness(output=output)

    assert score.passed is True
    assert score.missing_evidence_references == {}
    assert score.unknown_evidence_references == {}


def test_expected_evidence_sources_fails_when_expected_source_is_missing() -> None:
    case = _eval_case(
        expected_evidence_sources=[
            EvalExpectedEvidenceSource(
                source=EvidenceSource.LOG,
                source_file="sample_data/logs/cart-api.log",
            )
        ]
    )

    output = _output(retrieved_evidence=[_retrieved_evidence()])

    score = score_expected_evidence_sources(case=case, output=output)

    assert score.passed is False
    assert score.matched_expected_sources == []
    assert score.missing_expected_sources == [
        ExpectedEvidenceSourceDetail(
            source_file="sample_data/logs/cart-api.log", source=EvidenceSource.LOG
        )
    ]


def test_expected_evidence_sources_fails_when_not_all_sources_are_present() -> None:
    case = _eval_case(
        expected_evidence_sources=[
            EvalExpectedEvidenceSource(
                source=EvidenceSource.LOG,
                source_file="sample_data/logs/checkout-api.log",
            ),
            EvalExpectedEvidenceSource(
                source=EvidenceSource.METRIC,
                source_file="sample_data/metrics/checkout-api.jsonl",
            ),
        ]
    )
    output = _output(retrieved_evidence=[_retrieved_evidence()])

    score = score_expected_evidence_sources(case=case, output=output)

    assert score.passed is False
    assert score.matched_expected_sources == [
        ExpectedEvidenceSourceDetail(
            source_file="sample_data/logs/checkout-api.log", source=EvidenceSource.LOG
        )
    ]
    assert score.missing_expected_sources == [
        ExpectedEvidenceSourceDetail(
            source_file="sample_data/metrics/checkout-api.jsonl",
            source=EvidenceSource.METRIC,
        )
    ]


def test_expected_evidence_sources_fails_when_wrong_telemetry_source() -> None:
    case = _eval_case(
        expected_evidence_sources=[
            EvalExpectedEvidenceSource(
                source=EvidenceSource.LOG,
                source_file="sample_data/logs/checkout-api.log",
            )
        ]
    )
    output = _output(
        retrieved_evidence=[_retrieved_evidence(source=EvidenceSource.METRIC)]
    )

    score = score_expected_evidence_sources(case=case, output=output)

    assert score.passed is False
    assert score.matched_expected_sources == []
    assert score.missing_expected_sources == [
        ExpectedEvidenceSourceDetail(
            source_file="sample_data/logs/checkout-api.log", source=EvidenceSource.LOG
        )
    ]


def test_categorization_passes_when_all_hypotheses_match_category() -> None:
    case = _eval_case(
        expected_evidence_sources=[
            EvalExpectedEvidenceSource(
                source=EvidenceSource.LOG,
                source_file="sample_data/logs/checkout-api.log",
            )
        ]
    )

    output = EvaluationRunOutput(
        validation_result=HypothesisValidationResult(
            validated_hypotheses=[
                _hypothesis(
                    "hyp-001",
                    statement="Checkout latency is caused by database timeout errors.",
                ),
                _hypothesis("hyp-002", statement="Db thrown timeout exception"),
            ]
        )
    )

    score = score_expected_category(case=case, output=output)

    assert score.passed is True
    assert score.matched_hypothesis_ids == ["hyp-001", "hyp-002"]


def test_categorization_passes_when_any_hypotheses_match_category() -> None:
    case = _eval_case(
        expected_evidence_sources=[
            EvalExpectedEvidenceSource(
                source=EvidenceSource.LOG,
                source_file="sample_data/logs/checkout-api.log",
            )
        ]
    )

    output = EvaluationRunOutput(
        validation_result=HypothesisValidationResult(
            validated_hypotheses=[
                _hypothesis(
                    "hyp-001",
                    statement="Checkout latency is caused by database timeout errors.",
                ),
                _hypothesis(
                    "hyp-002",
                    statement="Downstream system unresponsive.",
                    category=HypothesisCategory.DOWNSTREAM_DEPENDENCY_FAILURE,
                ),
            ]
        )
    )

    score = score_expected_category(case=case, output=output)

    assert score.passed is True
    assert score.matched_hypothesis_ids == ["hyp-001"]


def test_categorization_fails_when_none_hypotheses_match_category() -> None:
    case = _eval_case(expected_category=HypothesisCategory.METRIC_ANOMALY)

    output = EvaluationRunOutput(
        validation_result=HypothesisValidationResult(
            validated_hypotheses=[
                _hypothesis(
                    "hyp-001",
                    statement="Checkout latency is caused by database timeout errors.",
                ),
                _hypothesis("hyp-002", statement="Downstream system unresponsive."),
            ]
        )
    )

    score = score_expected_category(case=case, output=output)

    assert score.passed is False
    assert score.matched_hypothesis_ids == []


def test_expected_human_review_passes_when_required_review_is_expected() -> None:
    case = _eval_case()
    case.expected_human_review_required = True
    output = _output()
    output.human_review_assessment = HumanReviewAssessment(
        human_review_required=True,
        human_review_reason="Low validated hypothesis confidence.",
    )

    score = score_expected_human_review(case=case, output=output)

    assert score.passed is True
    assert score.expected_human_review_required is True
    assert score.actual_human_review_required is True


def test_expected_human_review_passes_when_required_review_is_not_expected() -> None:
    case = _eval_case()
    case.expected_human_review_required = False
    output = _output()
    output.human_review_assessment = HumanReviewAssessment(
        human_review_required=False,
    )

    score = score_expected_human_review(case=case, output=output)

    assert score.passed is True
    assert score.expected_human_review_required is False
    assert score.actual_human_review_required is False


def test_expected_human_review_fails_when_human_review_assessment_is_missing() -> None:
    case = _eval_case()
    case.expected_human_review_required = True
    output = _output()

    score = score_expected_human_review(case=case, output=output)

    assert score.passed is False
    assert score.expected_human_review_required is True
    assert score.actual_human_review_required is None


def test_expected_human_review_fails_when_required_review_is_not_produced() -> None:
    case = _eval_case()
    case.expected_human_review_required = True
    output = _output()
    output.human_review_assessment = HumanReviewAssessment(
        human_review_required=False,
    )

    score = score_expected_human_review(case=case, output=output)

    assert score.passed is False
    assert score.expected_human_review_required is True
    assert score.actual_human_review_required is False


def test_unsupported_claims_passes_when_reviewer_returns_no_findings() -> None:
    output = _output(
        retrieved_evidence=[_retrieved_evidence(evidence_id="log-001")],
        validated_hypotheses=[_hypothesis()],
    )
    adapter = FakeUnsupportedClaimAdapter(UnsupportedClaimReviewResult())
    reviewer = GuardedUnsupportedClaimReviewer(adapter=adapter)

    score = score_unsupported_claims(output=output, reviewer=reviewer)

    assert score.passed is True
    assert score.findings == []
    assert output.validation_result is not None
    assert adapter.requests == [
        UnsupportedClaimReviewRequest(
            evidence=output.retrieved_evidence,
            vaidated_hypotheses=output.validation_result.validated_hypotheses,
        )
    ]


def test_unsupported_claims_fails_when_reviewer_returns_finding() -> None:
    finding = UnsupportedClaimFinding(
        hypothesis_id="hyp-001",
        claim="A DNS outage caused checkout database timeouts.",
        reason="The cited log reports a timeout but does not support a DNS outage.",
        evidence_ids=["log-001"],
    )
    output = _output(
        retrieved_evidence=[_retrieved_evidence(evidence_id="log-001")],
        validated_hypotheses=[_hypothesis()],
    )
    adapter = FakeUnsupportedClaimAdapter(
        UnsupportedClaimReviewResult(findings=[finding])
    )
    reviewer = GuardedUnsupportedClaimReviewer(adapter=adapter)

    score = score_unsupported_claims(output=output, reviewer=reviewer)

    assert score.passed is False
    assert score.findings == [finding]


def test_unsupported_claims_rejects_unknown_evidence_id_through_scoring() -> None:
    finding = UnsupportedClaimFinding(
        hypothesis_id="hyp-001",
        claim="A DNS outage caused checkout database timeouts.",
        reason="The cited evidence does not support the claim.",
        evidence_ids=["log-unknown"],
    )
    output = _output(
        retrieved_evidence=[_retrieved_evidence(evidence_id="log-001")],
        validated_hypotheses=[_hypothesis()],
    )
    adapter = FakeUnsupportedClaimAdapter(
        UnsupportedClaimReviewResult(findings=[finding])
    )
    reviewer = GuardedUnsupportedClaimReviewer(adapter=adapter)

    with pytest.raises(ValueError, match="unknown evidence ID"):
        score_unsupported_claims(output=output, reviewer=reviewer)


def test_unsupported_claims_skips_reviewer_when_no_hypotheses_are_validated() -> None:
    output = _output(
        retrieved_evidence=[_retrieved_evidence(evidence_id="log-001")],
        validated_hypotheses=[],
    )
    adapter = FakeUnsupportedClaimAdapter(UnsupportedClaimReviewResult())
    reviewer = GuardedUnsupportedClaimReviewer(adapter=adapter)

    score = score_unsupported_claims(output=output, reviewer=reviewer)

    assert score.passed is True
    assert score.findings == []
    assert adapter.requests == []

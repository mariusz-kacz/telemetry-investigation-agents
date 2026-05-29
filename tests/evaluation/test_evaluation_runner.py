from telemetry_agents.domain import (
    EvidenceSource,
    HypothesisValidationResult,
    InvestigationHypothesis,
    TelemetryEvidence,
)
from telemetry_agents.evaluation import (
    EvalCase,
    EvalExpectedEvidenceSource,
    EvaluationRunOutput,
    HypothesisCategory,
    evaluate_case_output,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


def test_evaluate_case_output_combines_existing_scores() -> None:
    case = EvalCase(
        case_id="checkout-database-timeout",
        incident_file="sample_data/incidents/checkout-database-timeout.json",
        expected_category=HypothesisCategory.DATABASE_TIMEOUT,
        expected_evidence_sources=[
            EvalExpectedEvidenceSource(
                source=EvidenceSource.LOG,
                source_file="sample_data/logs/checkout-api.log",
            )
        ],
        forbidden_unsupported_claims=["cache poisoning"],
        expected_human_review_required=False,
    )
    output = EvaluationRunOutput(
        retrieved_evidence=[
            RetrievedEvidence(
                evidence=TelemetryEvidence(
                    evidence_id="log-checkout-api-1",
                    source=EvidenceSource.LOG,
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
                    statement="Checkout latency is caused by database timeout errors.",
                    supporting_evidence_ids=["log-checkout-api-1"],
                    confidence=0.9,
                )
            ]
        ),
    )

    scorecard = evaluate_case_output(case=case, output=output)

    assert scorecard.case_id == "checkout-database-timeout"
    assert scorecard.passed is True
    assert scorecard.expected_category_score.passed is True
    assert scorecard.expected_evidence_sources_score.passed is True

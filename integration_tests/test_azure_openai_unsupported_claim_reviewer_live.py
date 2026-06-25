from telemetry_agents.app.config import get_settings
from telemetry_agents.domain import (
    EvidenceSource,
    HypothesisCategory,
    InvestigationHypothesis,
    TelemetryEvidence,
)
from telemetry_agents.evaluation.unsupported_claim_review import (
    UnsupportedClaimReviewRequest,
    UnsupportedClaimReviewResult,
    GuardedUnsupportedClaimReviewer,
)
from telemetry_agents.infrastructure.azure_openai_client import (
    create_azure_openai_client,
)
from telemetry_agents.infrastructure.azure_openai_unsupported_claim_adapter import (
    AzureOpenAIUnsupportedClaimAdapter,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


def test_live_azure_reviewer_returns_evidence_bounded_findings() -> None:
    settings = get_settings()

    client = create_azure_openai_client(
        endpoint=settings.azure_openai_endpoint,
    )
    adapter = AzureOpenAIUnsupportedClaimAdapter(
        client=client,
        deployment_name=settings.azure_openai_evaluation_deployment_name,
    )

    reviewer = GuardedUnsupportedClaimReviewer(
        adapter=adapter,
    )

    result = reviewer.review(request=_request())

    assert isinstance(result, UnsupportedClaimReviewResult)
    assert result.findings
    assert all(finding.hypothesis_id == "hyp-001" for finding in result.findings)
    assert all(set(finding.evidence_ids) <= {"log-001"} for finding in result.findings)


def _request() -> UnsupportedClaimReviewRequest:
    return UnsupportedClaimReviewRequest(
        evidence=[
            RetrievedEvidence(
                evidence=TelemetryEvidence(
                    evidence_id="log-001",
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
        reviewed_accepted_hypotheses=[
            InvestigationHypothesis(
                hypothesis_id="hyp-001",
                statement="A DNS outage caused checkout database timeouts.",
                category=HypothesisCategory.NETWORK_FAILURE,
                supporting_evidence_ids=["log-001"],
                confidence=0.9,
            )
        ],
    )

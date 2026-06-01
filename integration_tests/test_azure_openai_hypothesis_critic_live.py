import os

from dotenv import load_dotenv

from telemetry_agents.domain import (
    EvidenceSource,
    HypothesisCritiqueResult,
    HypothesisValidationResult,
    InvestigationHypothesis,
    TelemetryEvidence,
    HypothesisCategory,
)
from telemetry_agents.infrastructure.azure_openai_client import (
    create_azure_openai_client,
)
from telemetry_agents.infrastructure.azure_openai_hypothesis_critic import (
    AzureOpenAIHypothesisCritic,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.investigation.hypothesis_critic import HypothesisCritiqueRequest


def test_live_azure_critic_returns_evidence_bounded_findings() -> None:
    load_dotenv()

    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    deployment_name = os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]

    client = create_azure_openai_client(endpoint=endpoint)
    critic = AzureOpenAIHypothesisCritic(
        client=client,
        deployment_name=deployment_name,
    )
    evidence = _retrieved_evidence()
    validation_result = HypothesisValidationResult(
        accepted_hypotheses=[
            InvestigationHypothesis(
                hypothesis_id="hyp-001",
                statement=(
                    "Checkout API latency is definitively caused by database timeouts."
                ),
                category=HypothesisCategory.DATABASE_FAILURE,
                supporting_evidence_ids=["log-001"],
                confidence=0.9,
            )
        ]
    )
    request = HypothesisCritiqueRequest(
        evidence=[evidence],
        validation_result=validation_result,
    )

    result = critic.critique(request)

    known_hypothesis_ids = {
        hypothesis.hypothesis_id for hypothesis in validation_result.accepted_hypotheses
    }
    known_evidence_ids = {evidence.evidence.evidence_id}

    assert isinstance(result, HypothesisCritiqueResult)
    assert all(
        finding.hypothesis_id in known_hypothesis_ids
        for finding in result.critique_findings
    )
    assert all(
        set(finding.evidence_ids) <= known_evidence_ids
        for finding in result.critique_findings
    )


def _retrieved_evidence() -> RetrievedEvidence:
    return RetrievedEvidence(
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

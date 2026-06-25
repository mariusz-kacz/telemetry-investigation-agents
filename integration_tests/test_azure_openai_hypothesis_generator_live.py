from telemetry_agents.app.config import get_settings
from telemetry_agents.domain import (
    EvidenceSource,
    Incident,
    IncidentImpact,
    InvestigationHypothesis,
    TelemetryEvidence,
)
from telemetry_agents.infrastructure.azure_openai_client import (
    create_azure_openai_client,
)
from telemetry_agents.infrastructure.azure_openai_hypothesis_generator import (
    AzureOpenAIHypothesisGenerator,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.investigation.hypothesis_generation import (
    HypothesisGenerationRequest,
)


def test_azure_generator_returns_typed_candidate_hypotheses() -> None:
    settings = get_settings()

    client = create_azure_openai_client(
        endpoint=settings.azure_openai_endpoint,
    )
    generator = AzureOpenAIHypothesisGenerator(
        client=client,
        deployment_name=settings.azure_openai_hypothesis_deployment_name,
    )
    request = HypothesisGenerationRequest(
        incident=Incident.model_validate(
            {
                "incident_id": "inc-001",
                "title": "Checkout API latency spike",
                "service": "checkout-api",
                "impact": IncidentImpact.MEDIUM,
                "reported_at": "2026-05-11T10:05:00Z",
                "investigation_window": {
                    "start": "2026-05-11T09:40:00Z",
                    "end": "2026-05-11T10:10:00Z",
                },
                "retrieval": {"query_terms": ["timeout"], "trace_id": "trace-001"},
            }
        ),
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
    )

    result = generator.generate(request)

    assert all(isinstance(item, InvestigationHypothesis) for item in result)
    assert all(item.supporting_evidence_ids for item in result)
    assert all(set(item.supporting_evidence_ids) <= {"log-001"} for item in result)

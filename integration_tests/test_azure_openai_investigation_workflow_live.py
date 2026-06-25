from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from telemetry_agents.app.config import get_settings
from telemetry_agents.domain import (
    EvidenceSource,
    Incident,
    IncidentImpact,
    TelemetryEvidence,
)
from telemetry_agents.graph.investigation_workflow import build_investigation_workflow
from telemetry_agents.infrastructure.azure_openai_client import (
    create_azure_openai_client,
)
from telemetry_agents.infrastructure.azure_openai_hypothesis_critic import (
    AzureOpenAIHypothesisCritic,
)
from telemetry_agents.infrastructure.azure_openai_hypothesis_generator import (
    AzureOpenAIHypothesisGenerator,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


def _incident() -> Incident:
    return Incident.model_validate(
        {
            "incident_id": "inc-001",
            "title": "Checkout API latency spike",
            "service": "checkout-api",
            "impact": IncidentImpact.HIGH,
            "reported_at": "2026-05-11T10:05:00Z",
            "investigation_window": {
                "start": "2026-05-11T09:40:00Z",
                "end": "2026-05-11T10:10:00Z",
            },
            "retrieval": {"query_terms": ["timeout"], "trace_id": "trace-001"},
        }
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


def build_memory_investigation_workflow_graph():
    settings = get_settings()

    client = create_azure_openai_client(
        endpoint=settings.azure_openai_endpoint,
    )
    generator = AzureOpenAIHypothesisGenerator(
        client=client,
        deployment_name=settings.azure_openai_hypothesis_deployment_name,
    )

    critic = AzureOpenAIHypothesisCritic(
        client=client,
        deployment_name=settings.azure_openai_hypothesis_deployment_name,
    )

    checkpointer = InMemorySaver()

    return build_investigation_workflow(
        generator=generator,
        critic=critic,
        checkpointer=checkpointer,
    )


def test_azure_investigation_workflow_runs_graph_with_live_llm_adapters() -> None:
    graph = build_memory_investigation_workflow_graph()
    config: RunnableConfig = {"configurable": {"thread_id": "run-001"}}
    known_evidence_ids = {"log-001"}

    result = graph.invoke(
        {
            "normalized_incident": _incident(),
            "collected_evidence": [_retrieved_evidence()],
        },
        config=config,
    )

    assert result["__interrupt__"] is not None

    hypotheses = result["hypotheses"]
    validation_result = result["validation_result"]
    critique_findings = result["critique_findings"]

    assert all(
        set(hypothesis.supporting_evidence_ids) <= known_evidence_ids
        for hypothesis in hypotheses
    )
    assert all(
        set(hypothesis.supporting_evidence_ids) <= known_evidence_ids
        for hypothesis in validation_result.validated_hypotheses
    )
    assert all(
        set(finding.evidence_ids) <= known_evidence_ids for finding in critique_findings
    )

    result = graph.invoke(Command(resume={"approved": True}), config=config)

    assert result["report_ready"] is True

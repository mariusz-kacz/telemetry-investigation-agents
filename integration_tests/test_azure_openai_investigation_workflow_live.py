import os

from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

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
    return Incident(
        incident_id="inc-001",
        title="Checkout API latency spike",
        service="checkout-api",
        impact=IncidentImpact.HIGH,
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
    load_dotenv()

    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    deployment_name = os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]

    generator_client = create_azure_openai_client(
        endpoint=endpoint,
    )
    generator = AzureOpenAIHypothesisGenerator(
        client=generator_client,
        deployment_name=deployment_name,
    )

    critic_client = create_azure_openai_client(endpoint=endpoint)
    critic = AzureOpenAIHypothesisCritic(
        client=critic_client,
        deployment_name=deployment_name,
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
        for hypothesis in validation_result.accepted_hypotheses
    )
    assert all(
        set(finding.evidence_ids) <= known_evidence_ids
        for finding in critique_findings
    )

    result = graph.invoke(Command(resume={"approved": True}), config=config)

    assert result["report_ready"] is True

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from telemetry_agents.domain import IncidentImpact, InvestigationHypothesis
from telemetry_agents.domain.models import (
    EvidenceSource,
    HypothesisCritiqueResult,
    Incident,
    TelemetryEvidence,
    HumanReviewStatus,
)
from telemetry_agents.graph.investigation_workflow import build_investigation_workflow

from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.investigation.hypothesis_critic import HypothesisCritiqueRequest
from telemetry_agents.investigation.hypothesis_generation import (
    HypothesisGenerationRequest,
)


class FakeHypothesisGenerator:
    def __init__(self, hypotheses: list[InvestigationHypothesis]) -> None:
        self.hypotheses = hypotheses

    def generate(
        self, request: HypothesisGenerationRequest
    ) -> list[InvestigationHypothesis]:
        return self.hypotheses


class FakeHypothesisCritic:
    def __init__(self, result: HypothesisCritiqueResult) -> None:
        self.result = result
        self.request: HypothesisCritiqueRequest | None = None

    def critique(
        self,
        request: HypothesisCritiqueRequest,
    ) -> HypothesisCritiqueResult:
        self.request = request
        return self.result


def _incident() -> Incident:
    return Incident(
        incident_id="inc-001",
        title="Checkout API latency spike",
        service="checkout-api",
        impact=IncidentImpact.MEDIUM,
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
    checkpointer = InMemorySaver()
    fake_generator = FakeHypothesisGenerator([])
    fake_critic = FakeHypothesisCritic(HypothesisCritiqueResult())

    return build_investigation_workflow(
        generator=fake_generator,
        critic=fake_critic,
        checkpointer=checkpointer,
    )


def test_report_review_gate_handled() -> None:
    graph = build_memory_investigation_workflow_graph()
    config = {"configurable": {"thread_id": "run-001"}}

    result = graph.invoke(
        {
            "normalized_incident": _incident(),
            "collected_evidence": [_retrieved_evidence()],
        },
        config=config,
    )

    assert result["__interrupt__"] is not None

    result = graph.invoke(Command(resume={"approved": True}), config=config)

    assert result["human_review_status"] is HumanReviewStatus.APPROVED

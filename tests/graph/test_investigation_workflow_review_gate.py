import json
import logging

import pytest
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from telemetry_agents.domain import IncidentImpact, InvestigationHypothesis
from telemetry_agents.domain.models import (
    CritiqueFindingType,
    EvidenceSource,
    HypothesisCritiqueFinding,
    HypothesisCritiqueResult,
    Incident,
    TelemetryEvidence,
    HumanReviewStatus,
    HypothesisCategory,
)
from telemetry_agents.graph.investigation_workflow import build_investigation_workflow

from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.investigation.hypothesis_critic import (
    HypothesisCriticUnavailableError,
    HypothesisCritiqueRequest,
)
from telemetry_agents.investigation.hypothesis_generation import (
    HypothesisGenerationRequest,
)
from telemetry_agents.shared.observability import LOGGER_NAME


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


class UnavailableHypothesisCritic:
    def critique(
        self,
        request: HypothesisCritiqueRequest,
    ) -> HypothesisCritiqueResult:
        raise HypothesisCriticUnavailableError("critic unavailable")


def _incident() -> Incident:
    return Incident.model_validate(
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


def _contradicting_evidence() -> RetrievedEvidence:
    return RetrievedEvidence(
        evidence=TelemetryEvidence(
            evidence_id="metric-001",
            source=EvidenceSource.METRIC,
            summary="Database latency remained normal during the checkout slowdown.",
            citation="sample_data/metrics/database.jsonl:4",
            service="database",
        ),
        citation=CitationMetadata(
            source_file="sample_data/metrics/database.jsonl",
            line_number=4,
            service="database",
            selection_reason="Matched incident time window.",
        ),
        strength=EvidenceStrength.STRONG,
        relevance_score=0.9,
    )


def _supported_hypothesis() -> InvestigationHypothesis:
    return InvestigationHypothesis(
        hypothesis_id="hyp-001",
        statement="Checkout latency is caused by database timeout errors.",
        category=HypothesisCategory.DATABASE_FAILURE,
        supporting_evidence_ids=["log-001"],
        confidence=0.9,
    )


def _low_confidence_hypothesis() -> InvestigationHypothesis:
    return InvestigationHypothesis(
        hypothesis_id="hyp-001",
        statement="Checkout latency is caused by database timeout errors.",
        category=HypothesisCategory.DATABASE_FAILURE,
        supporting_evidence_ids=["log-001"],
        confidence=0.6,
        uncertainty="The timeout evidence does not prove the underlying database cause.",
    )


def _critique_finding() -> HypothesisCritiqueFinding:
    return HypothesisCritiqueFinding(
        hypothesis_id="hyp-001",
        evidence_ids=["metric-001"],
        finding_type=CritiqueFindingType.UNSUPPORTED_CAUSAL_LEAP,
        reason="Normal database latency contradicts the proposed database cause.",
    )


def build_memory_investigation_workflow_graph(
    hypotheses: list[InvestigationHypothesis] | None = None,
    critique_result: HypothesisCritiqueResult | None = None,
    critic: FakeHypothesisCritic | UnavailableHypothesisCritic | None = None,
):
    checkpointer = InMemorySaver()
    fake_generator = FakeHypothesisGenerator(hypotheses or [])
    selected_critic = critic or FakeHypothesisCritic(
        critique_result or HypothesisCritiqueResult()
    )

    return build_investigation_workflow(
        generator=fake_generator,
        critic=selected_critic,
        checkpointer=checkpointer,
    )


def test_report_review_gate_handled() -> None:
    graph = build_memory_investigation_workflow_graph()
    config: RunnableConfig = {"configurable": {"thread_id": "run-001"}}

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
    assert result["report_ready"] is True


def test_report_review_interrupt_exposes_decision_material() -> None:
    graph = build_memory_investigation_workflow_graph(
        hypotheses=[_low_confidence_hypothesis()],
        critique_result=HypothesisCritiqueResult(
            critique_findings=[_critique_finding()]
        ),
    )
    config: RunnableConfig = {"configurable": {"thread_id": "run-review-packet"}}

    result = graph.invoke(
        {
            "normalized_incident": _incident(),
            "collected_evidence": [_retrieved_evidence(), _contradicting_evidence()],
        },
        config=config,
    )

    payload = result["__interrupt__"][0].value

    assert payload["incident"] == {
        "incident_id": "inc-001",
        "title": "Checkout API latency spike",
        "service": "checkout-api",
        "impact": "medium",
    }
    assert payload["escalation_reason"] == (
        "top reviewed hypothesis is blocked or disputed; no accepted hypothesis exists"
    )
    assert payload["hypotheses"] == [
        {
            "hypothesis_id": "hyp-001",
            "category": "database_failure",
            "statement": "Checkout latency is caused by database timeout errors.",
            "confidence": 0.6,
            "uncertainty": (
                "The timeout evidence does not prove the underlying database cause."
            ),
            "supporting_evidence": [
                {
                    "evidence_id": "log-001",
                    "summary": "Checkout API reports database timeout errors.",
                    "citation": "sample_data/logs/checkout-api.log:1",
                    "strength": "strong",
                }
            ],
        }
    ]
    assert payload["critic_findings"] == [
        {
            "hypothesis_id": "hyp-001",
            "finding_type": "unsupported_causal_leap",
            "reason": "Normal database latency contradicts the proposed database cause.",
            "evidence": [
                {
                    "evidence_id": "metric-001",
                    "summary": (
                        "Database latency remained normal during the checkout slowdown."
                    ),
                    "citation": "sample_data/metrics/database.jsonl:4",
                    "strength": "strong",
                }
            ],
        }
    ]


def test_critic_unavailable_warning_requires_human_review() -> None:
    graph = build_memory_investigation_workflow_graph(
        hypotheses=[_supported_hypothesis()],
        critic=UnavailableHypothesisCritic(),
    )
    config: RunnableConfig = {"configurable": {"thread_id": "run-critic-unavailable"}}

    result = graph.invoke(
        {
            "normalized_incident": _incident(),
            "collected_evidence": [_retrieved_evidence()],
        },
        config=config,
    )

    payload = result["__interrupt__"][0].value

    assert payload["escalation_reason"] == "warnings present"
    assert payload["warnings"] == [
        "Hypothesis critic was unavailable; semantic review was skipped."
    ]
    assert payload["hypotheses"][0]["hypothesis_id"] == "hyp-001"


def test_rejected_human_review_does_not_mark_report_ready() -> None:
    graph = build_memory_investigation_workflow_graph()
    config: RunnableConfig = {"configurable": {"thread_id": "run-rejected"}}

    result = graph.invoke(
        {
            "normalized_incident": _incident(),
            "collected_evidence": [_retrieved_evidence()],
        },
        config=config,
    )

    assert result["__interrupt__"] is not None

    result = graph.invoke(Command(resume={"approved": False}), config=config)

    assert result["human_review_status"] is HumanReviewStatus.REJECTED
    assert result["report_ready"] is False


def test_safe_investigation_bypasses_human_review() -> None:
    graph = build_memory_investigation_workflow_graph([_supported_hypothesis()])
    config: RunnableConfig = {"configurable": {"thread_id": "run-not-required"}}

    result = graph.invoke(
        {
            "normalized_incident": _incident(),
            "collected_evidence": [_retrieved_evidence()],
        },
        config=config,
    )

    assert not result.get("__interrupt__")
    assert result["human_review_status"] is HumanReviewStatus.NOT_REQUIRED
    assert result["report_ready"] is True


def test_graph_run_emits_correlatable_node_telemetry(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    graph = build_memory_investigation_workflow_graph([_supported_hypothesis()])
    config: RunnableConfig = {"configurable": {"thread_id": "run-observable"}}

    result = graph.invoke(
        {
            "normalized_incident": _incident(),
            "collected_evidence": [_retrieved_evidence()],
        },
        config=config,
    )

    events = [json.loads(record.message) for record in caplog.records]
    completed_generation_events = [
        event
        for event in events
        if event["event"] == "graph.node.completed"
        and event["node_name"] == "hypothesis_generation"
    ]

    assert result["run_id"]
    assert completed_generation_events
    assert completed_generation_events[0]["run_id"] == result["run_id"]
    assert completed_generation_events[0]["incident_id"] == "inc-001"


def test_graph_events_reconstruct_safe_workflow_timeline(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    graph = build_memory_investigation_workflow_graph([_supported_hypothesis()])
    config: RunnableConfig = {"configurable": {"thread_id": "run-timeline"}}

    result = graph.invoke(
        {
            "run_id": "run-timeline",
            "normalized_incident": _incident(),
            "collected_evidence": [_retrieved_evidence()],
        },
        config=config,
    )

    events = [json.loads(record.message) for record in caplog.records]
    completed_nodes = [
        event["node_name"]
        for event in events
        if event["event"] == "graph.node.completed"
    ]

    assert completed_nodes == [
        "hypothesis_generation",
        "hypothesis_validation",
        "hypothesis_critic",
        "hypothesis_review",
        "human_review_assessment",
        "human_review_not_required_marker",
        "report_ready_marker",
    ]

    for event in events:
        assert event["run_id"] == "run-timeline"
        if event["event"].startswith("graph.node."):
            assert event["incident_id"] == "inc-001"
            assert event["node_name"]
        if event["event"] == "graph.node.completed":
            assert isinstance(event["duration_ms"], float)
            assert event["duration_ms"] >= 0

    critic_events = [
        event for event in events if event["event"] == "hypothesis.critic.completed"
    ]
    review_events = [
        event for event in events if event["event"] == "hypothesis.review.completed"
    ]
    routing_events = [
        event for event in events if event["event"] == "human_review.routing_decided"
    ]

    assert critic_events == [
        {
            "event": "hypothesis.critic.completed",
            "run_id": "run-timeline",
            "incident_id": "inc-001",
            "finding_count": 0,
            "finding_types": [],
            "affected_hypothesis_ids": [],
            "evidence_reference_count": 0,
        }
    ]
    assert review_events == [
        {
            "event": "hypothesis.review.completed",
            "run_id": "run-timeline",
            "incident_id": "inc-001",
            "accepted_count": 1,
            "disputed_count": 0,
            "blocked_count": 0,
            "critic_finding_count": 0,
        }
    ]
    assert routing_events == [
        {
            "event": "human_review.routing_decided",
            "run_id": "run-timeline",
            "incident_id": "inc-001",
            "human_review_required": False,
            "reason": None,
        }
    ]
    assert result["report_ready"] is True

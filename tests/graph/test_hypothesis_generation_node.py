import json
import logging

import pytest

from telemetry_agents.domain import (
    EvidenceSource,
    Incident,
    IncidentImpact,
    InvestigationHypothesis,
    TelemetryEvidence,
    HypothesisCategory,
)
from telemetry_agents.graph.hypothesis_generation import make_hypothesis_generation_node
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.investigation.hypothesis_generation import (
    HypothesisGenerationRequest,
    HypothesisGeneratorUnavailableError,
)
from telemetry_agents.shared.observability import LOGGER_NAME


class FakeHypothesisGenerator:
    def __init__(self, hypotheses: list[InvestigationHypothesis]) -> None:
        self.hypotheses = hypotheses
        self.request: HypothesisGenerationRequest | None = None

    def generate(
        self, request: HypothesisGenerationRequest
    ) -> list[InvestigationHypothesis]:
        self.request = request
        return self.hypotheses


class UnavailableHypothesisGenerator:
    def generate(
        self, request: HypothesisGenerationRequest
    ) -> list[InvestigationHypothesis]:
        raise HypothesisGeneratorUnavailableError("generator unavailable")


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


def test_hypothesis_generation_node_writes_hypotheses_to_state() -> None:
    hypothesis = InvestigationHypothesis(
        hypothesis_id="hyp-001",
        statement="Checkout API latency is caused by database timeout errors.",
        category=HypothesisCategory.DATABASE_FAILURE,
        supporting_evidence_ids=["log-001"],
        confidence=0.9,
    )
    generator = FakeHypothesisGenerator([hypothesis])
    node = make_hypothesis_generation_node(generator)
    incident = _incident()
    evidence = _retrieved_evidence()

    result = node(
        {
            "normalized_incident": incident,
            "collected_evidence": [evidence],
        }
    )

    assert result == {"hypotheses": [hypothesis]}
    assert generator.request == HypothesisGenerationRequest(
        incident=incident,
        evidence=[evidence],
    )


def test_hypothesis_generation_node_requires_normalized_incident() -> None:
    node = make_hypothesis_generation_node(FakeHypothesisGenerator([]))

    with pytest.raises(ValueError, match="normalized_incident"):
        node({"collected_evidence": [_retrieved_evidence()]})


def test_hypothesis_generation_node_requires_collected_evidence() -> None:
    node = make_hypothesis_generation_node(FakeHypothesisGenerator([]))

    with pytest.raises(ValueError, match="collected_evidence"):
        node({"normalized_incident": _incident()})


def test_hypothesis_generation_node_adds_warning_when_generator_unavailable(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    node = make_hypothesis_generation_node(UnavailableHypothesisGenerator())

    result = node(
        {
            "run_id": "run-001",
            "normalized_incident": _incident(),
            "collected_evidence": [_retrieved_evidence()],
        }
    )

    assert result == {
        "hypotheses": [],
        "warnings": [
            "Hypothesis generator was unavailable; no candidate hypotheses were generated."
        ],
    }
    events = [json.loads(record.message) for record in caplog.records]
    assert events == [
        {
            "event": "hypothesis.generation.fallback",
            "run_id": "run-001",
            "incident_id": "inc-001",
            "reason": "generator_unavailable",
            "fallback": "no_hypotheses_generated",
            "warning_added": True,
        }
    ]

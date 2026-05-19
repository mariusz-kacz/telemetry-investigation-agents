import pytest

from telemetry_agents.domain import (
    EvidenceSource,
    Incident,
    InvestigationHypothesis,
    TelemetryEvidence,
)
from telemetry_agents.graph.hypothesis_generation import make_hypothesis_generation_node
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.investigation.hypothesis_generation import (
    HypothesisGenerationRequest,
)


class FakeHypothesisGenerator:
    def __init__(self, hypotheses: list[InvestigationHypothesis]) -> None:
        self.hypotheses = hypotheses
        self.request: HypothesisGenerationRequest | None = None

    def generate(
        self, request: HypothesisGenerationRequest
    ) -> list[InvestigationHypothesis]:
        self.request = request
        return self.hypotheses


def _incident() -> Incident:
    return Incident(
        incident_id="inc-001",
        title="Checkout API latency spike",
        service="checkout-api",
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

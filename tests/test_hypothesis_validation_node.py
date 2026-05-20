import pytest

from telemetry_agents.domain import (
    EvidenceSource,
    InvestigationHypothesis,
    TelemetryEvidence,
)
from telemetry_agents.domain.models import HypothesisValidationResult
from telemetry_agents.graph.hypothesis_validation import make_hypothesis_validation_node
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


def _hypothesis() -> InvestigationHypothesis:
    return InvestigationHypothesis(
        hypothesis_id="hyp-001",
        statement="Checkout API latency is caused by database timeout errors.",
        supporting_evidence_ids=["log-001"],
        confidence=0.9,
    )


def _collected_evidence() -> RetrievedEvidence:
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


def test_hypothesis_validation_node_writes_validation_result_to_state() -> None:
    node = make_hypothesis_validation_node()
    hypothesis = _hypothesis()
    evidence = _collected_evidence()
    validation_result = HypothesisValidationResult(
        accepted_hypotheses=[hypothesis],
    )

    result = node(
        {
            "hypotheses": [hypothesis],
            "collected_evidence": [evidence],
        }
    )

    assert result == {"validation_result": validation_result}


def test_hypothesis_validation_node_requires_hypotheses() -> None:
    node = make_hypothesis_validation_node()

    with pytest.raises(ValueError, match="hypotheses"):
        node({"collected_evidence": [_collected_evidence()]})


def test_hypothesis_validation_node_requires_collected_evidence() -> None:
    node = make_hypothesis_validation_node()

    with pytest.raises(ValueError, match="collected_evidence"):
        node({"hypotheses": [_hypothesis()]})

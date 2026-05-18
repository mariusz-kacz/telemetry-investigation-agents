import pytest

from telemetry_agents.domain import (
    EvidenceSource,
    Incident,
    InvestigationHypothesis,
    TelemetryEvidence,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.investigation.hypothesis_generation import (
    HypothesisGenerationRequest,
    generate_hypotheses,
)


class FakeHypothesisGenerator:
    def __init__(self, hypotheses: list[InvestigationHypothesis]) -> None:
        self.hypotheses = hypotheses

    def generate(
        self, request: HypothesisGenerationRequest
    ) -> list[InvestigationHypothesis]:
        return self.hypotheses


def _retrieved_evidence(
    evidence_id: str,
    *,
    strength: EvidenceStrength = EvidenceStrength.STRONG,
) -> RetrievedEvidence:
    evidence = TelemetryEvidence(
        evidence_id=evidence_id,
        source=EvidenceSource.LOG,
        summary="Checkout API reports database timeout errors.",
        citation="sample_data/logs/checkout-api.log:1",
        service="checkout-api",
    )
    return RetrievedEvidence(
        evidence=evidence,
        citation=CitationMetadata(
            source_file="sample_data/logs/checkout-api.log",
            line_number=1,
            service="checkout-api",
            selection_reason="Matched incident query terms.",
        ),
        strength=strength,
        relevance_score=1.0 if strength == EvidenceStrength.STRONG else 0.2,
    )


def test_hypothesis_generation_rejects_unknown_evidence_references() -> None:
    request = HypothesisGenerationRequest(
        incident=Incident(
            incident_id="inc-001",
            title="Checkout API latency spike",
            service="checkout-api",
        ),
        evidence=[_retrieved_evidence("log-001")],
    )
    fake_generator = FakeHypothesisGenerator(
        [
            InvestigationHypothesis(
                hypothesis_id="hyp-001",
                statement="Checkout API latency is caused by database timeouts.",
                supporting_evidence_ids=["missing-evidence-id"],
                confidence=0.8,
            )
        ]
    )

    with pytest.raises(ValueError, match="unknown evidence"):
        generate_hypotheses(request, fake_generator)


def test_hypothesis_generation_rejects_mixed_known_and_unknown_evidence_references() -> (
    None
):
    request = HypothesisGenerationRequest(
        incident=Incident(
            incident_id="inc-001",
            title="Checkout API latency spike",
            service="checkout-api",
        ),
        evidence=[_retrieved_evidence("log-001")],
    )
    fake_generator = FakeHypothesisGenerator(
        [
            InvestigationHypothesis(
                hypothesis_id="hyp-001",
                statement="Checkout API latency is caused by database timeouts.",
                supporting_evidence_ids=["log-001", "hallucinated-evidence-id"],
                confidence=0.8,
            )
        ]
    )

    with pytest.raises(ValueError, match="unknown evidence"):
        generate_hypotheses(request, fake_generator)


def test_hypothesis_generation_rejects_missing_evidence_as_support() -> None:
    request = HypothesisGenerationRequest(
        incident=Incident(
            incident_id="inc-001",
            title="Checkout API latency spike",
            service="checkout-api",
        ),
        evidence=[
            _retrieved_evidence("log-001"),
            _retrieved_evidence(
                "missing-log-inc-001",
                strength=EvidenceStrength.MISSING,
            ),
        ],
    )
    fake_generator = FakeHypothesisGenerator(
        [
            InvestigationHypothesis(
                hypothesis_id="hyp-001",
                statement="Checkout API latency is caused by database timeouts.",
                supporting_evidence_ids=["log-001", "missing-log-inc-001"],
                confidence=0.8,
            )
        ]
    )

    with pytest.raises(ValueError, match="missing evidence"):
        generate_hypotheses(request, fake_generator)


def test_hypothesis_generation_caps_confidence_for_weak_evidence() -> None:
    request = HypothesisGenerationRequest(
        incident=Incident(
            incident_id="inc-001",
            title="Checkout API latency spike",
            service="checkout-api",
        ),
        evidence=[_retrieved_evidence("log-001", strength=EvidenceStrength.WEAK)],
    )
    fake_generator = FakeHypothesisGenerator(
        [
            InvestigationHypothesis(
                hypothesis_id="hyp-001",
                statement="Checkout API latency is probably caused by database timeouts.",
                supporting_evidence_ids=["log-001"],
                confidence=0.9,
            )
        ]
    )

    hypotheses = generate_hypotheses(request, fake_generator)

    assert hypotheses[0].confidence <= 0.4


def test_hypothesis_generation_caps_confidence_for_medium_without_strong_evidence() -> (
    None
):
    request = HypothesisGenerationRequest(
        incident=Incident(
            incident_id="inc-001",
            title="Checkout API latency spike",
            service="checkout-api",
        ),
        evidence=[_retrieved_evidence("metric-001", strength=EvidenceStrength.MEDIUM)],
    )
    fake_generator = FakeHypothesisGenerator(
        [
            InvestigationHypothesis(
                hypothesis_id="hyp-001",
                statement="Checkout API latency may be caused by elevated database latency.",
                supporting_evidence_ids=["metric-001"],
                confidence=0.95,
            )
        ]
    )

    hypotheses = generate_hypotheses(request, fake_generator)

    assert hypotheses[0].confidence <= 0.8


def test_hypothesis_generation_keeps_confidence_when_strong_evidence_supports_it() -> (
    None
):
    request = HypothesisGenerationRequest(
        incident=Incident(
            incident_id="inc-001",
            title="Checkout API latency spike",
            service="checkout-api",
        ),
        evidence=[_retrieved_evidence("log-001", strength=EvidenceStrength.STRONG)],
    )
    fake_generator = FakeHypothesisGenerator(
        [
            InvestigationHypothesis(
                hypothesis_id="hyp-001",
                statement="Checkout API latency is caused by database timeout errors.",
                supporting_evidence_ids=["log-001"],
                confidence=0.95,
            )
        ]
    )

    hypotheses = generate_hypotheses(request, fake_generator)

    assert hypotheses[0].confidence == 0.95


def test_hypothesis_generation_does_not_mutate_generator_owned_hypotheses() -> None:
    generated_hypothesis = InvestigationHypothesis(
        hypothesis_id="hyp-001",
        statement="Checkout API latency is probably caused by database timeouts.",
        supporting_evidence_ids=["log-001"],
        confidence=0.9,
    )
    request = HypothesisGenerationRequest(
        incident=Incident(
            incident_id="inc-001",
            title="Checkout API latency spike",
            service="checkout-api",
        ),
        evidence=[_retrieved_evidence("log-001", strength=EvidenceStrength.WEAK)],
    )
    fake_generator = FakeHypothesisGenerator([generated_hypothesis])

    hypotheses = generate_hypotheses(request, fake_generator)

    assert hypotheses[0].confidence <= 0.4
    assert generated_hypothesis.confidence == 0.9

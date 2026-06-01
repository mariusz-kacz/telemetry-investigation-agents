from telemetry_agents.domain import (
    Incident,
    IncidentImpact,
    InvestigationHypothesis,
    HypothesisCategory,
)
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


def _request() -> HypothesisGenerationRequest:
    return HypothesisGenerationRequest(
        incident=Incident(
            incident_id="inc-001",
            title="Checkout API latency spike",
            service="checkout-api",
            impact=IncidentImpact.MEDIUM,
        ),
        evidence=[],
    )


def test_hypothesis_generation_returns_generator_candidates_as_is() -> None:
    generated_hypothesis = InvestigationHypothesis(
        hypothesis_id="hyp-001",
        statement="Checkout API latency is probably caused by database timeouts.",
        category=HypothesisCategory.DATABASE_FAILURE,
        supporting_evidence_ids=["unknown-until-validation"],
        confidence=0.9,
    )
    fake_generator = FakeHypothesisGenerator([generated_hypothesis])

    hypotheses = generate_hypotheses(_request(), fake_generator)

    assert hypotheses == [generated_hypothesis]


def test_hypothesis_generation_allows_empty_candidate_list() -> None:
    fake_generator = FakeHypothesisGenerator([])

    hypotheses = generate_hypotheses(_request(), fake_generator)

    assert hypotheses == []

import pytest

from telemetry_agents.domain import (
    EvidenceSource,
    InvestigationHypothesis,
    TelemetryEvidence,
)
from telemetry_agents.domain.models import (
    CritiqueFindingType,
    HypothesisCritiqueFinding,
    HypothesisCritiqueResult,
    HypothesisValidationResult,
)
from telemetry_agents.graph.hypothesis_critic import make_hypothesis_critic_node
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.investigation.hypothesis_critic import (
    HypothesisCritiqueRequest,
    HypothesisCriticUnavailableError,
)


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


def _hypothesis() -> InvestigationHypothesis:
    return InvestigationHypothesis(
        hypothesis_id="hyp-001",
        statement="Checkout latency is caused by database timeout errors.",
        supporting_evidence_ids=["log-001"],
        confidence=0.9,
    )


def _validation_result() -> HypothesisValidationResult:
    return HypothesisValidationResult(accepted_hypotheses=[_hypothesis()])


def _retrieved_evidence() -> RetrievedEvidence:
    evidence = TelemetryEvidence(
        evidence_id="log-001",
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
        strength=EvidenceStrength.STRONG,
        relevance_score=1.0,
    )


def _finding() -> HypothesisCritiqueFinding:
    return HypothesisCritiqueFinding(
        hypothesis_id="hyp-001",
        evidence_ids=["log-001"],
        finding_type=CritiqueFindingType.UNSUPPORTED_CAUSAL_LEAP,
        reason="The evidence supports timeout symptoms but not the full causal claim.",
    )


def test_hypothesis_critic_node_writes_critique_findings_to_state() -> None:
    finding = _finding()
    result = HypothesisCritiqueResult(critique_findings=[finding])
    critic = FakeHypothesisCritic(result)
    node = make_hypothesis_critic_node(critic)
    evidence = _retrieved_evidence()
    validation_result = _validation_result()

    state_update = node(
        {
            "collected_evidence": [evidence],
            "validation_result": validation_result,
        }
    )

    assert state_update == {"critique_findings": [finding]}
    assert critic.request == HypothesisCritiqueRequest(
        evidence=[evidence],
        validation_result=validation_result,
    )


def test_hypothesis_critic_node_requires_collected_evidence() -> None:
    node = make_hypothesis_critic_node(FakeHypothesisCritic(HypothesisCritiqueResult()))

    with pytest.raises(ValueError, match="collected_evidence"):
        node({"validation_result": _validation_result()})


def test_hypothesis_critic_node_requires_validation_result() -> None:
    node = make_hypothesis_critic_node(FakeHypothesisCritic(HypothesisCritiqueResult()))

    with pytest.raises(ValueError, match="validation_result"):
        node({"collected_evidence": [_retrieved_evidence()]})


def test_hypothesis_critic_node_records_warning_when_critic_is_unavailable() -> None:
    node = make_hypothesis_critic_node(UnavailableHypothesisCritic())
    evidence = _retrieved_evidence()
    validation_result = _validation_result()

    state_update = node(
        {
            "collected_evidence": [evidence],
            "validation_result": validation_result,
        }
    )

    assert state_update == {
        "critique_findings": [],
        "warnings": ["Hypothesis critic was unavailable; semantic review was skipped."],
    }

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
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.investigation.hypothesis_critic import (
    HypothesisCritic,
    HypothesisCritiqueRequest,
    critique_hypotheses,
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


def _hypothesis() -> InvestigationHypothesis:
    return InvestigationHypothesis(
        hypothesis_id="hyp-001",
        statement="Checkout latency is caused by database timeout errors.",
        supporting_evidence_ids=["log-001"],
        confidence=0.9,
    )


def _validation_result() -> HypothesisValidationResult:
    return HypothesisValidationResult(accepted_hypotheses=[_hypothesis()])


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
        relevance_score=1.0 if strength == EvidenceStrength.STRONG else 0.0,
    )


def _finding(
    *,
    hypothesis_id: str = "hyp-001",
    evidence_ids: list[str] | None = None,
) -> HypothesisCritiqueFinding:
    return HypothesisCritiqueFinding(
        hypothesis_id=hypothesis_id,
        evidence_ids=evidence_ids or ["log-001"],
        finding_type=CritiqueFindingType.CONTRADICTION,
        reason="The cited evidence suggests the timeout may be a symptom rather than the root cause.",
    )


def test_critic_returns_structured_findings_from_adapter() -> None:
    result = HypothesisCritiqueResult(critique_findings=[_finding()])
    critic: HypothesisCritic = FakeHypothesisCritic(result)
    request = HypothesisCritiqueRequest(
        evidence=[_retrieved_evidence("log-001")],
        validation_result=_validation_result(),
    )

    critique_result = critique_hypotheses(request, critic)

    assert critique_result == result
    assert isinstance(critique_result, HypothesisCritiqueResult)
    assert critique_result.critique_findings[0].finding_type == (
        CritiqueFindingType.CONTRADICTION
    )


def test_critic_allows_empty_findings() -> None:
    critic = FakeHypothesisCritic(HypothesisCritiqueResult())
    request = HypothesisCritiqueRequest(
        evidence=[_retrieved_evidence("log-001")],
        validation_result=_validation_result(),
    )

    critique_result = critique_hypotheses(request, critic)

    assert critique_result.critique_findings == []


def test_critic_rejects_unknown_hypothesis_id() -> None:
    critic = FakeHypothesisCritic(
        HypothesisCritiqueResult(
            critique_findings=[_finding(hypothesis_id="hyp-hallucinated")]
        )
    )
    request = HypothesisCritiqueRequest(
        evidence=[_retrieved_evidence("log-001")],
        validation_result=_validation_result(),
    )

    with pytest.raises(ValueError, match="unknown hypothesis"):
        critique_hypotheses(request, critic)


def test_critic_rejects_unknown_evidence_id() -> None:
    critic = FakeHypothesisCritic(
        HypothesisCritiqueResult(
            critique_findings=[_finding(evidence_ids=["log-hallucinated"])]
        )
    )
    request = HypothesisCritiqueRequest(
        evidence=[_retrieved_evidence("log-001")],
        validation_result=_validation_result(),
    )

    with pytest.raises(ValueError, match="unknown evidence"):
        critique_hypotheses(request, critic)


def test_critic_rejects_missing_evidence_as_critique_support() -> None:
    critic = FakeHypothesisCritic(
        HypothesisCritiqueResult(
            critique_findings=[_finding(evidence_ids=["missing-log-001"])]
        )
    )
    request = HypothesisCritiqueRequest(
        evidence=[
            _retrieved_evidence("log-001"),
            _retrieved_evidence(
                "missing-log-001",
                strength=EvidenceStrength.MISSING,
            ),
        ],
        validation_result=_validation_result(),
    )

    with pytest.raises(ValueError, match="missing evidence"):
        critique_hypotheses(request, critic)

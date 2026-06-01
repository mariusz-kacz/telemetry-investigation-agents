from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from openai import APIConnectionError

from telemetry_agents.domain import (
    CritiqueFindingType,
    EvidenceSource,
    HypothesisCritiqueFinding,
    HypothesisCritiqueResult,
    HypothesisValidationResult,
    InvestigationHypothesis,
    TelemetryEvidence,
    HypothesisCategory,
)
from telemetry_agents.infrastructure.azure_openai_hypothesis_critic import (
    AzureOpenAIHypothesisCritic,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.investigation.hypothesis_critic import (
    HypothesisCritiqueRequest,
    HypothesisCriticUnavailableError,
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


def _hypothesis() -> InvestigationHypothesis:
    return InvestigationHypothesis(
        hypothesis_id="hyp-001",
        statement="Checkout API latency is definitively caused by database timeouts.",
        category=HypothesisCategory.DATABASE_FAILURE,
        supporting_evidence_ids=["log-001"],
        confidence=0.9,
    )


def _request() -> HypothesisCritiqueRequest:
    evidence = _retrieved_evidence()
    validation_result = HypothesisValidationResult(accepted_hypotheses=[_hypothesis()])
    return HypothesisCritiqueRequest(
        evidence=[evidence],
        validation_result=validation_result,
    )


def _critique_result() -> HypothesisCritiqueResult:
    return HypothesisCritiqueResult(
        critique_findings=[
            HypothesisCritiqueFinding(
                hypothesis_id="hyp-001",
                evidence_ids=["log-001"],
                finding_type=CritiqueFindingType.OVERSTATED_CONFIDENCE,
                reason=(
                    "The log evidence supports database timeout symptoms, but it does not "
                    "prove the database is the definitive root cause."
                ),
            )
        ]
    )


def test_critique_returns_findings_from_parsed_structured_response() -> None:
    client = Mock()
    expected_result = _critique_result()
    client.beta.chat.completions.parse.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=expected_result))]
    )

    critic = AzureOpenAIHypothesisCritic(
        client=client,
        deployment_name="hypothesis-model",
    )

    result = critic.critique(_request())

    assert result == expected_result

    call = client.beta.chat.completions.parse.call_args.kwargs
    assert call["model"] == "hypothesis-model"
    assert call["response_format"] is HypothesisCritiqueResult
    assert "log-001" in call["messages"][-1]["content"]


def test_critic_passes_system_prompt_to_model() -> None:
    client = Mock()
    expected_result = _critique_result()
    client.beta.chat.completions.parse.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=expected_result))]
    )

    critic = AzureOpenAIHypothesisCritic(
        client=client,
        deployment_name="hypothesis-model",
    )

    result = critic.critique(_request())

    assert result == expected_result

    call = client.beta.chat.completions.parse.call_args.kwargs
    system_message = next(
        (item["content"] for item in call["messages"] if item["role"] == "system"), None
    )
    assert system_message is not None
    assert "category" in system_message
    assert "statement" in system_message


def test_critic_raises_value_error_from_empty_response() -> None:
    client = Mock()

    client.beta.chat.completions.parse.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=None))]
    )

    critic = AzureOpenAIHypothesisCritic(
        client=client,
        deployment_name="hypothesis-model",
    )

    with pytest.raises(ValueError):
        critic.critique(_request())


def test_critic_passes_valid_empty_structured_response() -> None:
    client = Mock()

    client.beta.chat.completions.parse.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    parsed=HypothesisCritiqueResult(critique_findings=[])
                )
            )
        ]
    )

    critic = AzureOpenAIHypothesisCritic(
        client=client,
        deployment_name="hypothesis-model",
    )

    result = critic.critique(_request())
    assert result.critique_findings == []


def test_critic_translates_provider_connection_failure_to_unavailable() -> None:
    client = Mock()
    client.beta.chat.completions.parse.side_effect = APIConnectionError(request=Mock())
    critic = AzureOpenAIHypothesisCritic(
        client=client,
        deployment_name="hypothesis-model",
    )

    with pytest.raises(HypothesisCriticUnavailableError):
        critic.critique(_request())

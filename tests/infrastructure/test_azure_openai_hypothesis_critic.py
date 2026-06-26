import json
import logging
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
from telemetry_agents.infrastructure.prompt_loader import load_prompt
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.investigation.hypothesis_critic import (
    HypothesisCritiqueRequest,
    HypothesisCriticUnavailableError,
)
from telemetry_agents.shared.observability import LOGGER_NAME


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
    validation_result = HypothesisValidationResult(validated_hypotheses=[_hypothesis()])
    return HypothesisCritiqueRequest(
        run_id="run-001",
        incident_id="inc-001",
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


def _observability_events(caplog: pytest.LogCaptureFixture) -> list[dict[str, object]]:
    return [json.loads(record.message) for record in caplog.records]


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


def test_critique_emits_safe_llm_event_shape(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    client = Mock()
    client.beta.chat.completions.parse.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=_critique_result()))]
    )
    critic = AzureOpenAIHypothesisCritic(
        client=client,
        deployment_name="hypothesis-model",
    )

    critic.critique(_request())

    events = _observability_events(caplog)
    assert [event["event"] for event in events] == [
        "llm.call.started",
        "llm.call.completed",
    ]
    assert events[0] == {
        "event": "llm.call.started",
        "run_id": "run-001",
        "incident_id": "inc-001",
        "provider": "azure_openai",
        "operation": "hypothesis_critic",
        "deployment_name": "hypothesis-model",
        "output_schema": "HypothesisCritiqueResult",
    }
    assert events[1] | {"duration_ms": 0.0} == {
        "event": "llm.call.completed",
        "run_id": "run-001",
        "incident_id": "inc-001",
        "provider": "azure_openai",
        "operation": "hypothesis_critic",
        "deployment_name": "hypothesis-model",
        "output_schema": "HypothesisCritiqueResult",
        "finding_count": 1,
        "finding_types": ["overstated_confidence"],
        "duration_ms": 0.0,
    }
    assert isinstance(events[1]["duration_ms"], float)
    assert events[1]["duration_ms"] >= 0


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
    assert system_message == load_prompt("hypothesis_critic.md")
    assert "category" in system_message
    assert "statement" in system_message
    assert "Causal mechanism" in system_message
    assert "timeout or retry configuration" in system_message
    assert (
        "configuration, change-log, deployment, code, or explicit log evidence"
        in system_message
    )
    assert "Copy hypothesis IDs and evidence IDs exactly as supplied" in system_message
    assert "do not rename, normalize, reformat, translate" in system_message
    assert "change hyphens and underscores in IDs" in system_message
    assert "materially different competing cause" in system_message
    assert "ALTERNATIVE_INTERPRETATION" in system_message
    assert "plausible alternative" in system_message
    assert "temporal correlation" in system_message
    assert "UNSUPPORTED_CAUSAL_LEAP" in system_message
    assert "correlation, not causation" in system_message
    assert "direct causal path" in system_message
    assert "For UNCERTAIN_ROOT_CAUSE hypotheses" in system_message
    assert "possible rather than definitive" in system_message
    assert "do not emit UNSUPPORTED_CAUSAL_LEAP merely because" in system_message
    assert "supported by correlation or symptoms" in system_message
    assert "Use CONTRADICTION when cited evidence conflicts" in system_message
    assert "Use OVERSTATED_CONFIDENCE" in system_message
    assert "If none of the finding definitions apply, return no findings" in system_message


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


def test_critic_translates_provider_connection_failure_to_unavailable(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    client = Mock()
    client.beta.chat.completions.parse.side_effect = APIConnectionError(request=Mock())
    critic = AzureOpenAIHypothesisCritic(
        client=client,
        deployment_name="hypothesis-model",
    )

    with pytest.raises(HypothesisCriticUnavailableError):
        critic.critique(_request())

    events = _observability_events(caplog)
    assert [event["event"] for event in events] == [
        "llm.call.started",
        "llm.call.failed",
    ]
    assert events[1] | {"duration_ms": 0.0} == {
        "event": "llm.call.failed",
        "run_id": "run-001",
        "incident_id": "inc-001",
        "provider": "azure_openai",
        "operation": "hypothesis_critic",
        "deployment_name": "hypothesis-model",
        "output_schema": "HypothesisCritiqueResult",
        "error_type": "APIConnectionError",
        "duration_ms": 0.0,
    }
    assert isinstance(events[1]["duration_ms"], float)
    assert events[1]["duration_ms"] >= 0

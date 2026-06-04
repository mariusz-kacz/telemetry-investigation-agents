from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from openai import APIConnectionError

from telemetry_agents.domain import (
    EvidenceSource,
    Incident,
    IncidentImpact,
    InvestigationHypothesis,
    TelemetryEvidence,
    HypothesisCategory,
)
from telemetry_agents.infrastructure.azure_openai_hypothesis_generator import (
    AzureOpenAIHypothesisGenerator,
    InvestigationHypothesisResponse,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.investigation.hypothesis_generation import (
    HypothesisGenerationRequest,
)


def _request() -> HypothesisGenerationRequest:
    return HypothesisGenerationRequest(
        incident=Incident(
            incident_id="inc-001",
            title="Checkout API latency spike",
            service="checkout-api",
            impact=IncidentImpact.MEDIUM,
            reported_at="2026-05-11T10:05:00Z",
            investigation_window={
                "start": "2026-05-11T09:40:00Z",
                "end": "2026-05-11T10:10:00Z",
            },
            retrieval={"query_terms": ["timeout"], "trace_id": "trace-001"},
        ),
        evidence=[
            RetrievedEvidence(
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
        ],
    )


def test_generate_returns_hypotheses_from_parsed_structured_response() -> None:
    client = Mock()
    expected_hypothesis = InvestigationHypothesis(
        hypothesis_id="hyp-001",
        statement="Database timeouts may explain checkout latency.",
        category=HypothesisCategory.DATABASE_FAILURE,
        supporting_evidence_ids=["log-001"],
        confidence=0.7,
        uncertainty="Database metrics are not available.",
    )
    client.beta.chat.completions.parse.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    parsed=InvestigationHypothesisResponse(
                        hypotheses=[expected_hypothesis]
                    )
                )
            )
        ]
    )

    generator = AzureOpenAIHypothesisGenerator(
        client=client,
        deployment_name="hypothesis-model",
    )

    result = generator.generate(_request())

    assert result == [expected_hypothesis]

    call = client.beta.chat.completions.parse.call_args.kwargs
    assert call["model"] == "hypothesis-model"
    assert call["response_format"] is InvestigationHypothesisResponse
    assert "log-001" in call["messages"][-1]["content"]


def test_generate_passes_system_prompt_to_model() -> None:
    client = Mock()
    expected_hypothesis = InvestigationHypothesis(
        hypothesis_id="hyp-001",
        statement="Database timeouts may explain checkout latency.",
        category=HypothesisCategory.DATABASE_FAILURE,
        supporting_evidence_ids=["log-001"],
        confidence=0.7,
        uncertainty="Database metrics are not available.",
    )
    client.beta.chat.completions.parse.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    parsed=InvestigationHypothesisResponse(
                        hypotheses=[expected_hypothesis]
                    )
                )
            )
        ]
    )

    generator = AzureOpenAIHypothesisGenerator(
        client=client,
        deployment_name="hypothesis-model",
    )

    result = generator.generate(_request())

    assert result == [expected_hypothesis]

    call = client.beta.chat.completions.parse.call_args.kwargs
    system_message = next(
        (item["content"] for item in call["messages"] if item["role"] == "system"), None
    )
    assert system_message is not None
    assert "category" in system_message
    assert "coarse" in system_message
    assert "DATABASE_FAILURE" in system_message
    assert "DOWNSTREAM_DEPENDENCY_FAILURE" in system_message
    assert "orders-db" in system_message
    assert "non-database external services or APIs" in system_message
    assert "timeout or retry policy problems" in system_message
    assert "configuration was too aggressive or changed" in system_message


def test_generate_raises_value_error_from_empty_response() -> None:
    client = Mock()

    client.beta.chat.completions.parse.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=None))]
    )

    generator = AzureOpenAIHypothesisGenerator(
        client=client,
        deployment_name="hypothesis-model",
    )

    with pytest.raises(ValueError):
        generator.generate(_request())


def test_generate_propagates_provider_connection_failure() -> None:
    client = Mock()
    client.beta.chat.completions.parse.side_effect = APIConnectionError(request=Mock())
    generator = AzureOpenAIHypothesisGenerator(
        client=client,
        deployment_name="hypothesis-model",
    )

    with pytest.raises(APIConnectionError):
        generator.generate(_request())

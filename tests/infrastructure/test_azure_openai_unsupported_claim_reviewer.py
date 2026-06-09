from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from openai import APIConnectionError

from telemetry_agents.domain import (
    EvidenceSource,
    HypothesisCategory,
    InvestigationHypothesis,
    TelemetryEvidence,
)
from telemetry_agents.evaluation.unsupported_claim_review import (
    UnsupportedClaimFinding,
    UnsupportedClaimReviewRequest,
    UnsupportedClaimReviewResult,
    UnsupportedClaimReviewerUnavailableError,
)
from telemetry_agents.infrastructure.azure_openai_unsupported_claim_adapter import (
    AzureOpenAIUnsupportedClaimAdapter,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


def _request() -> UnsupportedClaimReviewRequest:
    return UnsupportedClaimReviewRequest(
        run_id="run-001",
        case_id="case-001",
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
        reviewed_accepted_hypotheses=[
            InvestigationHypothesis(
                hypothesis_id="hyp-001",
                statement="A DNS outage caused checkout database timeouts.",
                category=HypothesisCategory.NETWORK_FAILURE,
                supporting_evidence_ids=["log-001"],
                confidence=0.9,
            )
        ],
    )


def test_review_returns_findings_from_parsed_structured_response() -> None:
    client = Mock()
    expected_result = UnsupportedClaimReviewResult(
        findings=[
            UnsupportedClaimFinding(
                hypothesis_id="hyp-001",
                claim="A DNS outage caused checkout database timeouts.",
                reason="The cited log reports a timeout but does not support a DNS outage.",
                evidence_ids=["log-001"],
            )
        ]
    )
    client.beta.chat.completions.parse.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=expected_result))]
    )
    reviewer = AzureOpenAIUnsupportedClaimAdapter(
        client=client,
        deployment_name="evaluation-model",
    )

    result = reviewer.review(_request())

    assert result == expected_result

    call = client.beta.chat.completions.parse.call_args.kwargs
    assert call["model"] == "evaluation-model"
    assert call["response_format"] is UnsupportedClaimReviewResult
    assert "hyp-001" in call["messages"][-1]["content"]
    assert "log-001" in call["messages"][-1]["content"]


def test_review_passes_bounded_system_prompt_to_model() -> None:
    client = Mock()
    client.beta.chat.completions.parse.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(parsed=UnsupportedClaimReviewResult())
            )
        ]
    )
    reviewer = AzureOpenAIUnsupportedClaimAdapter(
        client=client,
        deployment_name="evaluation-model",
    )

    reviewer.review(_request())

    call = client.beta.chat.completions.parse.call_args.kwargs
    system_message = next(
        item["content"] for item in call["messages"] if item["role"] == "system"
    )
    assert "unsupported causal claims" in system_message
    assert "only hypothesis IDs" in system_message
    assert "only evidence IDs" in system_message
    assert "Copy hypothesis IDs and evidence IDs exactly as supplied" in system_message
    assert "do not rename, normalize, reformat, translate" in system_message
    assert "change hyphens and underscores in IDs" in system_message
    assert "Do not change workflow state" in system_message


def test_review_raises_value_error_from_empty_response() -> None:
    client = Mock()
    client.beta.chat.completions.parse.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=None))]
    )
    reviewer = AzureOpenAIUnsupportedClaimAdapter(
        client=client,
        deployment_name="evaluation-model",
    )

    with pytest.raises(ValueError, match="Invalid empty response"):
        reviewer.review(_request())


def test_review_translates_provider_connection_failure_to_unavailable() -> None:
    client = Mock()
    client.beta.chat.completions.parse.side_effect = APIConnectionError(request=Mock())
    reviewer = AzureOpenAIUnsupportedClaimAdapter(
        client=client,
        deployment_name="evaluation-model",
    )

    with pytest.raises(UnsupportedClaimReviewerUnavailableError):
        reviewer.review(_request())

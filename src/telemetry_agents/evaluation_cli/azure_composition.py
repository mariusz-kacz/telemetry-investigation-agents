from dataclasses import dataclass

from telemetry_agents.app.config import Settings, require_azure_setting
from telemetry_agents.evaluation import GuardedUnsupportedClaimReviewer
from telemetry_agents.evaluation_cli.graph_case_runner import (
    RunEvaluationCase,
    build_graph_case_runner,
)

from telemetry_agents.infrastructure.azure_openai_client import (
    create_azure_openai_client,
)
from telemetry_agents.infrastructure.azure_openai_hypothesis_critic import (
    AzureOpenAIHypothesisCritic,
)
from telemetry_agents.infrastructure.azure_openai_hypothesis_generator import (
    AzureOpenAIHypothesisGenerator,
)
from telemetry_agents.infrastructure.azure_openai_unsupported_claim_adapter import (
    AzureOpenAIUnsupportedClaimAdapter,
)


@dataclass(frozen=True)
class AzureComposition:
    run_case: RunEvaluationCase
    reviewer: GuardedUnsupportedClaimReviewer


def build_azure_evaluation_composition(
    settings: Settings,
) -> AzureComposition:
    openai_client = create_azure_openai_client(
        endpoint=require_azure_setting(
            settings.azure_openai_endpoint,
            "TELEMETRY_AGENTS_AZURE_OPENAI_ENDPOINT",
        ),
    )
    generator = AzureOpenAIHypothesisGenerator(
        client=openai_client,
        deployment_name=require_azure_setting(
            settings.azure_openai_hypothesis_deployment_name,
            "TELEMETRY_AGENTS_AZURE_OPENAI_HYPOTHESIS_DEPLOYMENT_NAME",
        ),
    )

    critic = AzureOpenAIHypothesisCritic(
        client=openai_client,
        deployment_name=require_azure_setting(
            settings.azure_openai_hypothesis_deployment_name,
            "TELEMETRY_AGENTS_AZURE_OPENAI_HYPOTHESIS_DEPLOYMENT_NAME",
        ),
    )

    adapter = AzureOpenAIUnsupportedClaimAdapter(
        client=openai_client,
        deployment_name=require_azure_setting(
            settings.azure_openai_evaluation_deployment_name,
            "TELEMETRY_AGENTS_AZURE_OPENAI_EVALUATION_DEPLOYMENT_NAME",
        ),
    )

    reviewer = GuardedUnsupportedClaimReviewer(
        adapter=adapter,
    )

    run_case = build_graph_case_runner(
        generator=generator,
        critic=critic,
        data_root=settings.eval_data_root,
    )

    return AzureComposition(run_case=run_case, reviewer=reviewer)

from dataclasses import dataclass
from telemetry_agents.app.config import AzureEvaluationConfig
from telemetry_agents.evaluation import GuardedUnsupportedClaimReviewer
from telemetry_agents.app.graph_case_runner import (
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
    config: AzureEvaluationConfig,
) -> AzureComposition:
    openai_client = create_azure_openai_client(
        endpoint=config.endpoint,
    )
    generator = AzureOpenAIHypothesisGenerator(
        client=openai_client,
        deployment_name=config.deployment_name,
    )

    critic = AzureOpenAIHypothesisCritic(
        client=openai_client,
        deployment_name=config.deployment_name,
    )

    adapter = AzureOpenAIUnsupportedClaimAdapter(
        client=openai_client,
        deployment_name=config.deployment_name,
    )

    reviewer = GuardedUnsupportedClaimReviewer(
        adapter=adapter,
    )

    run_case = build_graph_case_runner(
        generator=generator,
        critic=critic,
        data_root=config.eval_data_root,
    )

    return AzureComposition(run_case=run_case, reviewer=reviewer)

from telemetry_agents.app.config import Settings
from telemetry_agents.app.demo_investigation_service import (
    RunDemoInvestigation,
    build_demo_investigation_service,
)
from telemetry_agents.app.workflow_runner import build_workflow_runner
from telemetry_agents.infrastructure.azure_openai_client import create_azure_openai_client
from telemetry_agents.infrastructure.azure_openai_hypothesis_critic import AzureOpenAIHypothesisCritic
from telemetry_agents.infrastructure.azure_openai_hypothesis_generator import AzureOpenAIHypothesisGenerator


def build_azure_demo_investigation_service(
    settings: Settings,
) -> RunDemoInvestigation:
    openai_client = create_azure_openai_client(
        endpoint=settings.azure_openai_endpoint,
    )

    generator = AzureOpenAIHypothesisGenerator(
        client=openai_client,
        deployment_name=settings.azure_openai_hypothesis_deployment_name,
    )

    critic = AzureOpenAIHypothesisCritic(
        client=openai_client,
        deployment_name=settings.azure_openai_hypothesis_deployment_name,
    )

    run_workflow = build_workflow_runner(
        generator=generator,
        critic=critic
    )

    return build_demo_investigation_service(
        run_workflow=run_workflow,
        demo_data_root=settings.data_root,
    )
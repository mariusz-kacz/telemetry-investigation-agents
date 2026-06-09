from telemetry_agents.app.config import Settings
from telemetry_agents.app.demo_investigation_service import (
    build_demo_investigation_service,
    DemoInvestigationService,
)
from telemetry_agents.app.workflow_runner import build_workflow_service
from telemetry_agents.infrastructure.azure_openai_client import (
    create_azure_openai_client,
)
from telemetry_agents.infrastructure.azure_openai_hypothesis_critic import (
    AzureOpenAIHypothesisCritic,
)
from telemetry_agents.infrastructure.azure_openai_hypothesis_generator import (
    AzureOpenAIHypothesisGenerator,
)
from telemetry_agents.infrastructure.checkpointing import create_sqlite_checkpointer
from telemetry_agents.infrastructure.run_registry import initialize_run_registry


def build_azure_demo_investigation_service(
    settings: Settings,
) -> DemoInvestigationService:
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

    checkpointer = create_sqlite_checkpointer(settings.checkpoint_db_path)

    workflow = build_workflow_service(
        generator=generator, critic=critic, checkpointer=checkpointer
    )

    initialize_run_registry(settings.run_registry_db_path)

    return build_demo_investigation_service(
        run_workflow=workflow.run,
        resume_workflow=workflow.resume,
        demo_data_root=settings.data_root,
        run_registry_db_path=settings.run_registry_db_path,
    )

from functools import lru_cache

from telemetry_agents.app.azure_demo_composition import (
    build_azure_demo_investigation_service,
)
from telemetry_agents.app.config import get_settings
from telemetry_agents.app.demo_investigation_service import DemoInvestigationService
from telemetry_agents.app.local_demo_composition import (
    build_local_demo_investigation_service,
)


@lru_cache
def get_demo_investigation_service() -> DemoInvestigationService:
    settings = get_settings()
    if settings.demo_provider == "azure":
        return build_azure_demo_investigation_service(settings)
    return build_local_demo_investigation_service(settings)

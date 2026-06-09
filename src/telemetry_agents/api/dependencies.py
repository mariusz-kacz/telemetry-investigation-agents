from functools import lru_cache

from telemetry_agents.app.azure_demo_composition import (
    build_azure_demo_investigation_service,
)
from telemetry_agents.app.config import get_settings
from telemetry_agents.app.demo_investigation_service import DemoInvestigationService


@lru_cache
def get_demo_investigation_service() -> DemoInvestigationService:
    return build_azure_demo_investigation_service(get_settings())

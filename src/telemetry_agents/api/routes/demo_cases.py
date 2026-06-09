from fastapi import APIRouter, Depends

from telemetry_agents.app.config import Settings, get_settings
from telemetry_agents.app.demo_cases import get_demo_cases

router = APIRouter(tags=["demo-cases"])


@router.get("/demo-cases")
def demo_cases(
    settings: Settings = Depends(get_settings),
) -> list[str]:
    return get_demo_cases(settings)

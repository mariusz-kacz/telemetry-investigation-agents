from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from telemetry_agents.api.routes import demo_cases, investigations, health
from telemetry_agents.shared.logging_config import configure_observability_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_observability_logging()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Telemetry Investigation Agents",
        version="0.1.0",
        lifespan=lifespan,
        redoc_url=None,
    )

    app.include_router(health.router)
    app.include_router(demo_cases.router, prefix="/api/v1")
    app.include_router(investigations.router, prefix="/api/v1")

    return app


app = create_app()

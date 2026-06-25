from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from telemetry_agents.api.routes import demo_cases, investigations, health
from telemetry_agents.app.config import get_settings
from telemetry_agents.shared.logging_config import configure_observability_logging
from telemetry_agents.shared.tracing import configure_local_tracing


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    configure_observability_logging()
    configure_local_tracing(tracing_enabled=settings.tracing_enabled)

    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Telemetry Investigation Agents",
        version="0.1.0",
        lifespan=lifespan,
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["content-type"],
    )

    app.include_router(health.router)
    app.include_router(demo_cases.router, prefix="/api/v1")
    app.include_router(investigations.router, prefix="/api/v1")

    return app


app = create_app()

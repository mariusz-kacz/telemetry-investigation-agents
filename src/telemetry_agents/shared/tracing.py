from __future__ import annotations

from typing import Literal

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.trace import Tracer


TRACER_NAME = "telemetry_agents.local_tracer"
SERVICE_NAME = "telemetry-investigation-agents"

TracingExporter = Literal["console", "otlp"]

_CONFIGURED = False
_PROVIDER: TracerProvider | None = None


def configure_local_tracing(
    tracing_enabled: bool,
    exporter: TracingExporter,
    otlp_endpoint: str | None = None,
) -> None:
    global _CONFIGURED, _PROVIDER

    if _CONFIGURED or not tracing_enabled:
        return

    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": SERVICE_NAME,
            }
        )
    )

    if exporter == "console":
        provider.add_span_processor(
            SimpleSpanProcessor(ConsoleSpanExporter())
        )

    elif exporter == "otlp":
        provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(
                    endpoint=otlp_endpoint,
                    insecure=True,
                )
            )
        )

    else:
        raise ValueError(f"Unsupported tracing exporter: {exporter}")

    trace.set_tracer_provider(provider)
    _PROVIDER = provider
    _CONFIGURED = True


def get_tracer() -> Tracer:
    return trace.get_tracer(TRACER_NAME)


def force_flush_local_tracing() -> None:
    if _PROVIDER is None:
        return
    _PROVIDER.force_flush()

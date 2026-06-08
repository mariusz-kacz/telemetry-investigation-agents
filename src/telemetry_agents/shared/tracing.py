from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Tracer

TRACER_NAME = "telemetry_agents.local_tracer"
_CONFIGURED = False


def configure_local_tracing(tracing_enabled: bool) -> None:
    global _CONFIGURED
    if _CONFIGURED or not tracing_enabled:
        return

    provider = TracerProvider(
        resource=Resource.create({"service.name": "telemetry-investigation-agents"})
    )

    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)

    _CONFIGURED = True


def get_tracer() -> Tracer:
    return trace.get_tracer(TRACER_NAME)

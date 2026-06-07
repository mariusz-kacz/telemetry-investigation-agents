from collections.abc import Callable
from time import perf_counter

from telemetry_agents.graph.investigation_state import InvestigationGraphState
from telemetry_agents.shared.observability import (
    EVENT_NODE_COMPLETED,
    EVENT_NODE_FAILED,
    EVENT_NODE_STARTED,
    emit_event,
    new_run_id,
)


def observe_graph_node(
    node_name: str,
    action: Callable[[InvestigationGraphState], InvestigationGraphState],
) -> Callable[[InvestigationGraphState], InvestigationGraphState]:
    """Wrap a graph node with generic start/end/error telemetry."""

    def observed_node(state: InvestigationGraphState) -> InvestigationGraphState:
        run_id = state.get("run_id") or new_run_id()
        incident = state.get("normalized_incident")
        incident_id = incident.incident_id if incident is not None else None

        emit_event(
            EVENT_NODE_STARTED,
            run_id=run_id,
            incident_id=incident_id,
            node_name=node_name,
        )

        started_at = perf_counter()
        try:
            result = action(state)
        except Exception as exc:
            emit_event(
                EVENT_NODE_FAILED,
                run_id=run_id,
                incident_id=incident_id,
                node_name=node_name,
                duration_ms=round((perf_counter() - started_at) * 1000, 3),
                error_type=type(exc).__name__,
            )
            raise

        result.setdefault("run_id", run_id)
        emit_event(
            EVENT_NODE_COMPLETED,
            run_id=run_id,
            incident_id=incident_id,
            node_name=node_name,
            duration_ms=round((perf_counter() - started_at) * 1000, 3),
        )
        return result

    return observed_node


def graph_correlation_fields(state: InvestigationGraphState) -> dict[str, str | None]:
    incident = state.get("normalized_incident")
    return {
        "run_id": state.get("run_id"),
        "incident_id": incident.incident_id if incident is not None else None,
    }

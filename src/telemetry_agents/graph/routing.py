from telemetry_agents.graph.investigation_state import (
    InvestigationGraphState,
    InvestigationRoute,
)

RULES = {
    InvestigationRoute.LOG_FOCUSED: ["logs", "errors", "exceptions"],
    InvestigationRoute.TRACE_FOCUSED: ["traces", "timeouts", "downstream"],
    InvestigationRoute.METRIC_FOCUSED: ["latency", "cpu", "memory", "spike"],
}


def classify_incident_route(state: InvestigationGraphState) -> InvestigationRoute:
    """Choose the next investigation branch from explicit state."""
    incident_input = state.get("incident_input")
    if incident_input is None:
        raise ValueError("incident_input is required")

    normalized = incident_input.lower()

    for investigation_route, keywords in RULES.items():
        if any(keyword in normalized for keyword in keywords):
            return investigation_route

    return InvestigationRoute.BROAD

import pytest

from telemetry_agents.graph.investigation_state import (
    InvestigationGraphState,
    InvestigationRoute,
)
from telemetry_agents.graph.routing import classify_incident_route


def test_graph_state_captures_routing_decision() -> None:
    assert "routing_decision" in InvestigationGraphState.__annotations__


@pytest.mark.parametrize(
    ("incident_input", "expected_route"),
    [
        (
            "Checkout API logs show NullReferenceException errors",
            InvestigationRoute.LOG_FOCUSED,
        ),
        (
            "Payment request timeout appears in distributed traces",
            InvestigationRoute.TRACE_FOCUSED,
        ),
        (
            "Orders service has a sudden p95 latency spike",
            InvestigationRoute.METRIC_FOCUSED,
        ),
        ("Users report checkout is unreliable", InvestigationRoute.BROAD),
    ],
)
def test_classify_incident_route_uses_deterministic_rules(
    incident_input: str,
    expected_route: InvestigationRoute,
) -> None:
    state: InvestigationGraphState = {"incident_input": incident_input}

    assert classify_incident_route(state) == expected_route

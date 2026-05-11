import pytest

from telemetry_agents.graph.routed_investigation import build_routed_investigation_graph


@pytest.mark.parametrize(
    ("incident_input", "expected_finding"),
    [
        (
            "Checkout API logs show NullReferenceException errors",
            "log-focused investigation selected",
        ),
        (
            "Payment request timeout appears in distributed traces",
            "trace-focused investigation selected",
        ),
        (
            "Orders service has a sudden p95 latency spike",
            "metric-focused investigation selected",
        ),
        (
            "Users report checkout is unreliable",
            "broad investigation selected",
        ),
    ],
)
def test_routed_investigation_graph_follows_conditional_branch(
    incident_input: str,
    expected_finding: str,
) -> None:
    graph = build_routed_investigation_graph()

    result = graph.invoke({"incident_input": incident_input})

    assert expected_finding in result["intermediate_findings"]

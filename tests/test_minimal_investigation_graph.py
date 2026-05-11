from telemetry_agents.graph.minimal_investigation import (
    build_minimal_investigation_graph,
)


def test_minimal_investigation_graph_normalizes_title_and_creates_summary() -> None:
    graph = build_minimal_investigation_graph()

    result = graph.invoke(
        {
            "incident_title": "  Checkout API latency spike  ",
        }
    )

    assert result["incident_title"] == "  Checkout API latency spike  "
    assert result["normalized_title"] == "checkout api latency spike"
    assert (
        result["investigation_summary"]
        == "Initial investigation created for checkout api latency spike."
    )


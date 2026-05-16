from typing import Any

from langgraph.constants import START, END
from langgraph.graph.state import CompiledStateGraph, StateGraph

from telemetry_agents.graph.investigation_state import (
    InvestigationGraphState,
    InvestigationRoute,
)
from telemetry_agents.graph.routing import classify_incident_route


def record_routing_decision(
    state: InvestigationGraphState,
) -> InvestigationGraphState:
    """Record the deterministic route in graph state."""
    route = classify_incident_route(state)

    return {"routing_decision": route}


def route_from_state(state: InvestigationGraphState) -> InvestigationRoute:
    route = state.get("routing_decision")
    if route is None:
        raise ValueError("routing_decision is required")

    return route


def log_focused_findings(state: InvestigationGraphState) -> InvestigationGraphState:
    """Record that the log-focused branch was selected."""
    return {"intermediate_findings": ["log-focused investigation selected"]}


def trace_focused_findings(state: InvestigationGraphState) -> InvestigationGraphState:
    """Record that the trace-focused branch was selected."""
    return {"intermediate_findings": ["trace-focused investigation selected"]}


def metric_focused_findings(state: InvestigationGraphState) -> InvestigationGraphState:
    """Record that the metric-focused branch was selected."""
    return {"intermediate_findings": ["metric-focused investigation selected"]}


def broad_focused_findings(state: InvestigationGraphState) -> InvestigationGraphState:
    """Record that the broad branch was selected."""
    return {"intermediate_findings": ["broad investigation selected"]}


def build_routed_investigation_graph() -> CompiledStateGraph[Any, None, Any, Any]:
    """Build a graph that branches by routing_decision."""

    builder = StateGraph(InvestigationGraphState)
    builder.add_node("record_routing_decision", record_routing_decision)
    builder.add_node("log_focused_findings", log_focused_findings)
    builder.add_node("trace_focused_findings", trace_focused_findings)
    builder.add_node("metric_focused_findings", metric_focused_findings)
    builder.add_node("broad_focused_findings", broad_focused_findings)

    builder.add_edge(START, "record_routing_decision")
    builder.add_conditional_edges(
        "record_routing_decision",
        route_from_state,
        {
            InvestigationRoute.LOG_FOCUSED: "log_focused_findings",
            InvestigationRoute.TRACE_FOCUSED: "trace_focused_findings",
            InvestigationRoute.METRIC_FOCUSED: "metric_focused_findings",
            InvestigationRoute.BROAD: "broad_focused_findings",
        },
    )

    builder.add_edge("log_focused_findings", END)
    builder.add_edge("trace_focused_findings", END)
    builder.add_edge("metric_focused_findings", END)
    builder.add_edge("broad_focused_findings", END)
    return builder.compile()

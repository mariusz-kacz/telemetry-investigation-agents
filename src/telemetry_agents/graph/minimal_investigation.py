from typing import Any, TypedDict

from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph


class MinimalInvestigationState(TypedDict, total=False):
    """Workflow context for the smallest incident-investigation graph."""

    incident_title: str
    normalized_title: str
    investigation_summary: str


def normalize_incident_title(
    state: MinimalInvestigationState,
) -> MinimalInvestigationState:
    """Return a state update containing a normalized incident title."""
    incident_title = state.get("incident_title")
    if incident_title is None:
        raise ValueError("incident_title is required")

    return {"normalized_title": incident_title.strip().lower()}


def create_initial_summary(
    state: MinimalInvestigationState,
) -> MinimalInvestigationState:
    """Return a state update containing an initial investigation summary."""
    normalized_title = state.get("normalized_title")
    if normalized_title is None:
        raise ValueError("normalized_title is required")

    return {
        "investigation_summary": f"Initial investigation created for {normalized_title}."
    }


def build_minimal_investigation_graph() -> CompiledStateGraph[Any, None, Any, Any]:
    """Build and compile the smallest LangGraph StateGraph."""
    builder = StateGraph(MinimalInvestigationState)
    builder.add_node("normalize_incident_title", normalize_incident_title)
    builder.add_node("create_initial_summary", create_initial_summary)

    builder.add_edge(START, "normalize_incident_title")
    builder.add_edge("normalize_incident_title", "create_initial_summary")
    builder.add_edge("create_initial_summary", END)

    return builder.compile()

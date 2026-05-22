from typing import Any

from langgraph.constants import START, END
from langgraph.graph.state import CompiledStateGraph, StateGraph

from telemetry_agents.graph.hypothesis_critic import make_hypothesis_critic_node
from telemetry_agents.graph.hypothesis_generation import make_hypothesis_generation_node
from telemetry_agents.graph.hypothesis_validation import make_hypothesis_validation_node
from telemetry_agents.graph.investigation_state import InvestigationGraphState
from telemetry_agents.graph.report_ready_marker import make_report_ready_marker_node
from telemetry_agents.graph.report_review_gate import make_report_review_gate_node
from telemetry_agents.investigation.hypothesis_critic import HypothesisCritic
from telemetry_agents.investigation.hypothesis_generation import HypothesisGenerator


def build_investigation_workflow(
    *,
    generator: HypothesisGenerator,
    critic: HypothesisCritic,
    checkpointer: Any | None = None,
) -> CompiledStateGraph[Any, None, Any, Any]:
    builder = StateGraph(InvestigationGraphState)

    builder.add_node(
        "hypothesis_generation", make_hypothesis_generation_node(generator=generator)
    )
    builder.add_node("hypothesis_validation", make_hypothesis_validation_node())
    builder.add_node("hypothesis_critic", make_hypothesis_critic_node(critic=critic))
    builder.add_node("report_review_gate", make_report_review_gate_node())
    builder.add_node("report_ready_marker", make_report_ready_marker_node())

    builder.add_edge(START, "hypothesis_generation")
    builder.add_edge("hypothesis_generation", "hypothesis_validation")
    builder.add_edge("hypothesis_validation", "hypothesis_critic")
    builder.add_edge("hypothesis_critic", "report_review_gate")
    builder.add_edge("report_review_gate", "report_ready_marker")
    builder.add_edge("report_ready_marker", END)
    return builder.compile(checkpointer=checkpointer)

from collections.abc import Callable
from typing import Any, cast

from langgraph.constants import START, END
from langgraph.graph.state import CompiledStateGraph, StateGraph

from telemetry_agents.domain.models import HumanReviewStatus
from telemetry_agents.graph.human_review_assessment import (
    make_human_review_assessment_node,
)
from telemetry_agents.graph.hypothesis_critic import make_hypothesis_critic_node
from telemetry_agents.graph.hypothesis_generation import make_hypothesis_generation_node
from telemetry_agents.graph.hypothesis_validation import make_hypothesis_validation_node
from telemetry_agents.graph.investigation_state import InvestigationGraphState
from telemetry_agents.graph.human_review_not_required_marker import (
    make_human_review_not_required_marker_node,
)
from telemetry_agents.graph.report_ready_marker import make_report_ready_marker_node
from telemetry_agents.graph.report_rejected_marker import (
    make_report_rejected_marker_node,
)
from telemetry_agents.graph.report_review_gate import make_report_review_gate_node
from telemetry_agents.investigation.hypothesis_critic import HypothesisCritic
from telemetry_agents.investigation.hypothesis_generation import HypothesisGenerator


def _node(
    action: Callable[[InvestigationGraphState], InvestigationGraphState],
) -> Any:
    return cast(Any, action)


def build_investigation_workflow(
    *,
    generator: HypothesisGenerator,
    critic: HypothesisCritic,
    checkpointer: Any | None = None,
) -> CompiledStateGraph[Any, None, Any, Any]:
    builder = StateGraph(InvestigationGraphState)

    builder.add_node(
        "hypothesis_generation",
        _node(make_hypothesis_generation_node(generator=generator)),
    )
    builder.add_node("hypothesis_validation", _node(make_hypothesis_validation_node()))
    builder.add_node(
        "hypothesis_critic",
        _node(make_hypothesis_critic_node(critic=critic)),
    )
    builder.add_node(
        "human_review_assessment",
        _node(make_human_review_assessment_node()),
    )
    builder.add_node(
        "human_review_not_required_marker",
        _node(make_human_review_not_required_marker_node()),
    )
    builder.add_node("report_review_gate", _node(make_report_review_gate_node()))
    builder.add_node("report_ready_marker", _node(make_report_ready_marker_node()))
    builder.add_node("report_rejected_marker", _node(make_report_rejected_marker_node()))

    builder.add_edge(START, "hypothesis_generation")
    builder.add_edge("hypothesis_generation", "hypothesis_validation")
    builder.add_edge("hypothesis_validation", "hypothesis_critic")
    builder.add_edge("hypothesis_critic", "human_review_assessment")
    builder.add_conditional_edges(
        "human_review_assessment",
        _requires_human_review_route,
        {True: "report_review_gate", False: "human_review_not_required_marker"},
    )
    builder.add_edge("human_review_not_required_marker", "report_ready_marker")
    builder.add_conditional_edges(
        "report_review_gate",
        _route_on_review_status,
    )
    builder.add_edge("report_ready_marker", END)
    builder.add_edge("report_rejected_marker", END)
    return builder.compile(checkpointer=checkpointer)


def _requires_human_review_route(state: InvestigationGraphState) -> bool:
    human_review_assessment = state.get("human_review_assessment")
    if human_review_assessment is None:
        raise ValueError(
            "human_review_assessment is required before deciding if flow should go to report_review_gate or report_ready_marker"
        )

    return human_review_assessment.human_review_required


def _route_on_review_status(state: InvestigationGraphState) -> str:
    human_review_status = state.get("human_review_status")
    if human_review_status is None:
        raise ValueError("human_review_status before marking report as ready")

    if human_review_status == HumanReviewStatus.NOT_REQUIRED:
        raise ValueError("human_review_status with status NOT_REQUIRED is not expected")

    if human_review_status == HumanReviewStatus.APPROVED:
        return "report_ready_marker"
    else:
        return "report_rejected_marker"

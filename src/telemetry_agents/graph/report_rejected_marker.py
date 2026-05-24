from collections.abc import Callable

from telemetry_agents.graph.investigation_state import InvestigationGraphState


def make_report_rejected_marker_node() -> Callable[
    [InvestigationGraphState], InvestigationGraphState
]:
    def node(state: InvestigationGraphState) -> InvestigationGraphState:
        return {"report_ready": False}

    return node

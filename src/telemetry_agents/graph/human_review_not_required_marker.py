from collections.abc import Callable

from telemetry_agents.domain.models import HumanReviewStatus
from telemetry_agents.graph.investigation_state import InvestigationGraphState


def make_human_review_not_required_marker_node() -> Callable[
    [InvestigationGraphState], InvestigationGraphState
]:
    def node(state: InvestigationGraphState) -> InvestigationGraphState:
        return {"human_review_status": HumanReviewStatus.NOT_REQUIRED}

    return node

from collections.abc import Callable
from langgraph.types import interrupt

from telemetry_agents.domain.models import HumanReviewStatus
from telemetry_agents.graph.investigation_state import InvestigationGraphState


def make_report_review_gate_node() -> Callable[
    [InvestigationGraphState], InvestigationGraphState
]:
    def node(state: InvestigationGraphState) -> InvestigationGraphState:
        validation_result = state.get("validation_result")
        if validation_result is None:
            raise ValueError("validation_result is required before report review")

        critique_findings = state.get("critique_findings")
        if critique_findings is None:
            raise ValueError("critique_findings are required before report review")

        user_feedback = interrupt(
            {
                "reason": "report_review_required",
                "accepted_hypothesis_count": len(validation_result.accepted_hypotheses),
                "critique_finding_count": len(critique_findings),
            }
        )

        user_approved = user_feedback.get("approved")
        if user_approved is None:
            raise ValueError("approved field is required in user feedback")
        human_review_status = (
            HumanReviewStatus.APPROVED if user_approved else HumanReviewStatus.REJECTED
        )
        return {
            "human_review_status": human_review_status,
        }

    return node

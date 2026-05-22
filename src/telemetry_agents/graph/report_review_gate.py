from collections.abc import Callable
from langgraph.types import interrupt
from telemetry_agents.graph.investigation_state import InvestigationGraphState


def make_report_review_gate_node() -> Callable[
    [InvestigationGraphState], InvestigationGraphState
]:
    def node(state: InvestigationGraphState) -> InvestigationGraphState:
        validation_result = state.get("validation_result")
        if validation_result is None:
            raise ValueError(
                "validation_result is required before report review"
            )

        critique_findings = state.get("critique_findings")
        if critique_findings is None:
            raise ValueError(
                "critique_findings are required before report review"
            )

        approved = interrupt(
            {
                "reason": "report_review_required",
                "accepted_hypothesis_count": len(validation_result.accepted_hypotheses),
                "critique_finding_count": len(critique_findings),
            }
        )

        return {"report_review_decision": approved}

    return node

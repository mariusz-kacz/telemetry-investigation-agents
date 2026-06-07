from typing import Callable

from telemetry_agents.graph.investigation_state import InvestigationGraphState
from telemetry_agents.graph.observability import graph_correlation_fields
from telemetry_agents.investigation.hypothesis_review import (
    HypothesisReviewRequest,
    review_hypotheses,
)
from telemetry_agents.domain import HypothesisReviewStatus
from telemetry_agents.shared.observability import (
    EVENT_HYPOTHESIS_REVIEW_COMPLETED,
    emit_event,
)


def make_hypothesis_review_node() -> Callable[
    [InvestigationGraphState], InvestigationGraphState
]:
    def node(state: InvestigationGraphState) -> InvestigationGraphState:
        validation_result = state.get("validation_result")
        if validation_result is None:
            raise ValueError("validation_result is required before hypothesis review")

        critique_findings = state.get("critique_findings")
        if critique_findings is None:
            raise ValueError(
                "critique_findings is required before hypothesis validation"
            )

        request = HypothesisReviewRequest(
            validated_hypotheses=validation_result.validated_hypotheses,
            critique_findings=critique_findings,
        )

        review_result = review_hypotheses(request)
        reviewed_hypotheses = review_result.reviewed_hypotheses

        emit_event(
            EVENT_HYPOTHESIS_REVIEW_COMPLETED,
            **graph_correlation_fields(state),
            accepted_count=sum(
                item.status is HypothesisReviewStatus.ACCEPTED
                for item in reviewed_hypotheses
            ),
            disputed_count=sum(
                item.status is HypothesisReviewStatus.DISPUTED
                for item in reviewed_hypotheses
            ),
            blocked_count=sum(
                item.status is HypothesisReviewStatus.BLOCKED
                for item in reviewed_hypotheses
            ),
            critic_finding_count=len(critique_findings),
        )

        return {"review_result": review_result}

    return node

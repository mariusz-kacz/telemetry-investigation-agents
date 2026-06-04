from typing import Callable

from telemetry_agents.graph.investigation_state import InvestigationGraphState
from telemetry_agents.investigation.hypothesis_review import (
    HypothesisReviewRequest,
    review_hypotheses,
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

        return {"review_result": review_result}

    return node

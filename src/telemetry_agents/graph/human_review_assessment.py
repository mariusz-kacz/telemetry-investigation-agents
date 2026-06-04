from typing import Callable

from telemetry_agents.graph.investigation_state import InvestigationGraphState
from telemetry_agents.investigation.human_review_assessment import (
    assess_human_review_requirement,
    HumanReviewAssessmentRequest,
)


def make_human_review_assessment_node() -> Callable[
    [InvestigationGraphState], InvestigationGraphState
]:
    def node(state: InvestigationGraphState) -> InvestigationGraphState:
        incident = state.get("normalized_incident")
        if incident is None:
            raise ValueError(
                "normalized_incident is required before decision if human should review investigation"
            )

        collected_evidence = state.get("collected_evidence")
        if collected_evidence is None:
            raise ValueError(
                "collected_evidence is required before decision if human should review investigation"
            )

        validation_result = state.get("validation_result")
        if validation_result is None:
            raise ValueError(
                "validation_result is required before decision if human should review investigation"
            )

        review_result = state.get("review_result")
        if review_result is None:
            raise ValueError(
                "review_result is required before decision if human should review investigation"
            )

        assessment = assess_human_review_requirement(
            HumanReviewAssessmentRequest(
                warnings=state.get("warnings", []),
                evidence=collected_evidence,
                validation_result=validation_result,
                incident=incident,
                reviewed_hypotheses=review_result.reviewed_hypotheses,
            )
        )

        return {
            "human_review_assessment": assessment,
        }

    return node

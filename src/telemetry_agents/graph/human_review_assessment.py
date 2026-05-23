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

        incident = state.get("normalized_incident")
        if incident is None:
            raise ValueError(
                "normalized_incident is required before decision if human should review investigation"
            )

        critique_findings = state.get("critique_findings")
        if critique_findings is None:
            raise ValueError(
                "critique_findings is required before decision if human should review investigation"
            )

        assessment = assess_human_review_requirement(
            HumanReviewAssessmentRequest(
                evidence=collected_evidence,
                validation_result=validation_result,
                incident=incident,
                critique_findings=critique_findings,
            )
        )

        return {
            "human_review_assessment": assessment,
        }

    return node

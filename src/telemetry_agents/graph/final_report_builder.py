from collections.abc import Callable

from telemetry_agents.graph.investigation_state import InvestigationGraphState
from telemetry_agents.investigation.investigation_report_builder import (
    build_investigation_report,
)


def make_final_report_builder_node() -> Callable[
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
                "collected_evidence is required before report is generated"
            )

        review_result = state.get("review_result")
        if review_result is None:
            raise ValueError("review_result is required before report is generated")

        human_review_status = state.get("human_review_status")
        if human_review_status is None:
            raise ValueError(
                "human_review_status is required before report is generated"
            )

        investigation_report = build_investigation_report(
            incident=incident,
            collected_evidence=collected_evidence,
            reviewed_hypotheses=review_result.reviewed_hypotheses,
            human_review_status=human_review_status,
        )

        return {"final_report": investigation_report}

    return node

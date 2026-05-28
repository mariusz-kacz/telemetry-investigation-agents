from collections.abc import Callable
from dataclasses import asdict
from langgraph.types import interrupt

from telemetry_agents.domain import HumanReviewStatus
from telemetry_agents.graph.investigation_state import InvestigationGraphState
from telemetry_agents.investigation.human_review_packet import build_human_review_packet


def make_report_review_gate_node() -> Callable[
    [InvestigationGraphState], InvestigationGraphState
]:
    def node(state: InvestigationGraphState) -> InvestigationGraphState:
        normalized_incident = state.get("normalized_incident")
        if normalized_incident is None:
            raise ValueError("normalized_incident is required before report review")

        validation_result = state.get("validation_result")
        if validation_result is None:
            raise ValueError("validation_result is required before report review")

        critique_findings = state.get("critique_findings")
        if critique_findings is None:
            raise ValueError("critique_findings are required before report review")

        collected_evidence = state.get("collected_evidence")
        if collected_evidence is None:
            raise ValueError("collected_evidence are required before report review")

        human_review_assessment = state.get("human_review_assessment")
        if human_review_assessment is None:
            raise ValueError("human_review_assessment is required before report review")

        warnings = state.get("warnings")
        if warnings is None:
            raise ValueError("warnings are required before report review")

        packet = build_human_review_packet(
            incident=normalized_incident,
            warnings=warnings,
            critique_findings=critique_findings,
            validation_result=validation_result,
            assessment=human_review_assessment,
            collected_evidence=collected_evidence,
        )

        user_feedback = interrupt(asdict(packet))

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

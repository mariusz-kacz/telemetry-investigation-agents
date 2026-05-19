from collections.abc import Callable

from telemetry_agents.graph.investigation_state import InvestigationGraphState
from telemetry_agents.investigation.hypothesis_validation import (
    HypothesisValidationRequest,
    validate_hypotheses,
)


def make_hypothesis_validation_node() -> Callable[
    [InvestigationGraphState], InvestigationGraphState
]:
    def node(state: InvestigationGraphState) -> InvestigationGraphState:
        collected_evidence = state.get("collected_evidence")
        if collected_evidence is None:
            raise ValueError(
                "collected_evidence is required before hypothesis validation"
            )

        hypotheses = state.get("hypotheses")
        if hypotheses is None:
            raise ValueError("hypotheses are required before hypothesis validation")

        request = HypothesisValidationRequest(
            evidence=collected_evidence,
            hypotheses=hypotheses,
        )

        validation_result = validate_hypotheses(request)

        return {"validation_result": validation_result}

    return node

from collections.abc import Callable

from telemetry_agents.graph.investigation_state import InvestigationGraphState
from telemetry_agents.investigation.hypothesis_critic import (
    HypothesisCritic,
    HypothesisCritiqueRequest,
    critique_hypotheses,
)


def make_hypothesis_critic_node(
    critic: HypothesisCritic,
) -> Callable[[InvestigationGraphState], InvestigationGraphState]:

    def node(state: InvestigationGraphState) -> InvestigationGraphState:
        collected_evidence = state.get("collected_evidence")
        if collected_evidence is None:
            raise ValueError(
                "collected_evidence is required before hypothesis critique"
            )

        validation_result = state.get("validation_result")
        if validation_result is None:
            raise ValueError(
                "validation_result is required before hypothesis critique"
            )

        request = HypothesisCritiqueRequest(
            evidence=collected_evidence,
            validation_result=validation_result,
        )
        critique_result = critique_hypotheses(request, critic)

        return {"critique_findings": critique_result.critique_findings}

    return node

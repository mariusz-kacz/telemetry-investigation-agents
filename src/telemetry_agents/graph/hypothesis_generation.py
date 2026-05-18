from collections.abc import Callable

from telemetry_agents.graph.investigation_state import InvestigationGraphState
from telemetry_agents.investigation.hypothesis_generation import (
    HypothesisGenerator,
    HypothesisGenerationRequest,
    generate_hypotheses,
)


def make_hypothesis_generation_node(
    generator: HypothesisGenerator,
) -> Callable[[InvestigationGraphState], InvestigationGraphState]:

    def node(state: InvestigationGraphState) -> InvestigationGraphState:
        incident = state.get("normalized_incident")
        if incident is None:
            raise ValueError("normalized_incident is required before hypothesis generation")

        evidence = state.get("collected_evidence")
        if evidence is None:
            raise ValueError("collected_evidence is required before hypothesis generation")

        request = HypothesisGenerationRequest(
            incident=incident,
            evidence=evidence,
        )
        hypotheses = generate_hypotheses(request, generator)

        return {"hypotheses": hypotheses}

    return node

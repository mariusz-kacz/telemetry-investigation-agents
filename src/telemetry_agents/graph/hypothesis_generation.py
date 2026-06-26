from collections.abc import Callable

from telemetry_agents.graph.investigation_state import InvestigationGraphState
from telemetry_agents.graph.observability import graph_correlation_fields
from telemetry_agents.investigation.hypothesis_generation import (
    HypothesisGenerator,
    HypothesisGenerationRequest,
    HypothesisGeneratorUnavailableError,
    generate_hypotheses,
)
from telemetry_agents.shared.observability import (
    EVENT_HYPOTHESIS_GENERATION_FALLBACK,
    emit_event,
)


def make_hypothesis_generation_node(
    generator: HypothesisGenerator,
) -> Callable[[InvestigationGraphState], InvestigationGraphState]:

    def node(state: InvestigationGraphState) -> InvestigationGraphState:
        incident = state.get("normalized_incident")
        if incident is None:
            raise ValueError(
                "normalized_incident is required before hypothesis generation"
            )

        evidence = state.get("collected_evidence")
        if evidence is None:
            raise ValueError(
                "collected_evidence is required before hypothesis generation"
            )

        request = HypothesisGenerationRequest(
            run_id=state.get("run_id"),
            incident=incident,
            evidence=evidence,
        )
        try:
            hypotheses = generate_hypotheses(request, generator)
        except HypothesisGeneratorUnavailableError:
            emit_event(
                EVENT_HYPOTHESIS_GENERATION_FALLBACK,
                **graph_correlation_fields(state),
                reason="generator_unavailable",
                fallback="no_hypotheses_generated",
                warning_added=True,
            )
            return {
                "hypotheses": [],
                "warnings": [
                    "Hypothesis generator was unavailable; no candidate hypotheses were generated."
                ],
            }

        return {"hypotheses": hypotheses}

    return node

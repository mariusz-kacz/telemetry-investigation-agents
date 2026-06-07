from collections.abc import Callable

from telemetry_agents.graph.investigation_state import InvestigationGraphState
from telemetry_agents.graph.observability import graph_correlation_fields
from telemetry_agents.investigation.hypothesis_validation import (
    HypothesisValidationRequest,
    validate_hypotheses,
)
from telemetry_agents.shared.observability import (
    EVENT_HYPOTHESIS_VALIDATION_CONFIDENCE_ADJUSTED,
    EVENT_HYPOTHESIS_VALIDATION_REJECTED,
    emit_event,
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

        for adjustment in validation_result.confidence_adjustments:
            emit_event(
                EVENT_HYPOTHESIS_VALIDATION_CONFIDENCE_ADJUSTED,
                **graph_correlation_fields(state),
                hypothesis_id=adjustment.hypothesis_id,
                original_confidence=adjustment.original_confidence,
                adjusted_confidence=adjustment.adjusted_confidence,
                reason=adjustment.reason,
            )

        for rejected_hypothesis in validation_result.rejected_hypotheses:
            emit_event(
                EVENT_HYPOTHESIS_VALIDATION_REJECTED,
                **graph_correlation_fields(state),
                hypothesis_id=rejected_hypothesis.hypothesis.hypothesis_id,
                reason=rejected_hypothesis.reason,
            )

        return {"validation_result": validation_result}

    return node

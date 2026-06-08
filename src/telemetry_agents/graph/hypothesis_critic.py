from collections.abc import Callable
from itertools import chain

from telemetry_agents.graph.investigation_state import InvestigationGraphState
from telemetry_agents.graph.observability import graph_correlation_fields
from telemetry_agents.investigation.hypothesis_critic import (
    HypothesisCritic,
    HypothesisCritiqueRequest,
    critique_hypotheses,
    HypothesisCriticUnavailableError,
)
from telemetry_agents.shared.observability import (
    EVENT_HYPOTHESIS_CRITIC_FALLBACK,
    emit_event,
    EVENT_HYPOTHESIS_CRITIC_COMPLETED,
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
            raise ValueError("validation_result is required before hypothesis critique")

        request = HypothesisCritiqueRequest(
            **graph_correlation_fields(state),
            evidence=collected_evidence,
            validation_result=validation_result,
        )
        try:
            critique_result = critique_hypotheses(request, critic)

            findings = critique_result.critique_findings
            unique_evidence_references = set(
                chain.from_iterable(f.evidence_ids for f in findings)
            )
            emit_event(
                EVENT_HYPOTHESIS_CRITIC_COMPLETED,
                **graph_correlation_fields(state),
                finding_count=len(findings),
                finding_types=sorted({f.finding_type.value for f in findings}),
                affected_hypothesis_ids=sorted({f.hypothesis_id for f in findings}),
                evidence_reference_count=len(unique_evidence_references),
            )
        except HypothesisCriticUnavailableError:
            emit_event(
                EVENT_HYPOTHESIS_CRITIC_FALLBACK,
                **graph_correlation_fields(state),
                reason="critic_unavailable",
                fallback="semantic_review_skipped",
                warning_added=True,
            )
            return {
                "critique_findings": [],
                "warnings": [
                    "Hypothesis critic was unavailable; semantic review was skipped."
                ],
            }

        return {"critique_findings": critique_result.critique_findings}

    return node

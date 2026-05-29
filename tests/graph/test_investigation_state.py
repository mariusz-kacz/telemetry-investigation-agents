from typing import Annotated, get_args, get_origin

from telemetry_agents.domain import (
    Incident,
    InvestigationHypothesis,
    InvestigationReport,
)
from telemetry_agents.graph.investigation_state import (
    InvestigationGraphState,
    append,
)
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence


def test_graph_state_has_explicit_phase_3_fields() -> None:
    expected_fields = {
        "incident_input",
        "normalized_incident",
        "collected_evidence",
        "intermediate_findings",
        "hypotheses",
        "validation_result",
        "final_report",
        "errors",
        "warnings",
    }

    assert expected_fields <= set(InvestigationGraphState.__annotations__)


def test_graph_state_references_domain_models_without_random_dicts() -> None:
    annotations = InvestigationGraphState.__annotations__

    assert annotations["normalized_incident"] is Incident
    assert annotations["collected_evidence"] == list[RetrievedEvidence]
    assert annotations["hypotheses"] == list[InvestigationHypothesis]
    assert annotations["final_report"] is InvestigationReport
    assert annotations["errors"] == list[str]
    warnings_annotation = annotations["warnings"]
    assert get_origin(warnings_annotation) is Annotated
    assert get_args(warnings_annotation) == (list[str], append)

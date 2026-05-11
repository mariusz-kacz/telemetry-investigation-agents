from telemetry_agents.domain import (
    Incident,
    InvestigationHypothesis,
    InvestigationReport,
    TelemetryEvidence,
)
from telemetry_agents.graph.investigation_state import InvestigationGraphState


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
    assert annotations["collected_evidence"] == list[TelemetryEvidence]
    assert annotations["hypotheses"] == list[InvestigationHypothesis]
    assert annotations["final_report"] is InvestigationReport
    assert annotations["errors"] == list[str]
    assert annotations["warnings"] == list[str]

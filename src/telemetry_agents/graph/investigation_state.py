from typing import TypedDict

from telemetry_agents.domain import Incident, TelemetryEvidence, InvestigationHypothesis, InvestigationReport


class InvestigationGraphState(TypedDict, total=False):
    incident_input: str
    normalized_incident: Incident
    collected_evidence: list[TelemetryEvidence]
    intermediate_findings: list[str]
    hypotheses: list[InvestigationHypothesis]
    validation_result: str
    final_report: InvestigationReport
    errors: list[str]
    warnings: list[str]

from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel

from telemetry_agents.app.demo_cases import load_incident_file
from telemetry_agents.app.workflow_runner import (
    RunWorkflow,
    WorkflowRunRequest,
)
from telemetry_agents.domain import ReviewedHypothesis
from telemetry_agents.shared.observability import new_run_id


class DemoInvestigationResult(BaseModel):
    run_id: str
    incident_id: str
    hypotheses: list[ReviewedHypothesis]
    human_review_required: bool
    review_reasons: list[str]


RunDemoInvestigation = Callable[[str], DemoInvestigationResult]


def build_demo_investigation_service(
    *,
    run_workflow: RunWorkflow,
    demo_data_root: Path,
) -> RunDemoInvestigation:
    def run_investigation(case_id: str) -> DemoInvestigationResult:
        run_id = new_run_id()
        incident = load_incident_file(demo_data_root / case_id / "incident.json")

        result = run_workflow(
            WorkflowRunRequest(
                run_id=run_id,
                case_id=case_id,
                incident=incident,
                data_root=demo_data_root / case_id,
                auto_approve_human_review=False,
            )
        )

        return DemoInvestigationResult(
            run_id=run_id,
            incident_id=result.incident.incident_id,
            hypotheses=result.review_result.reviewed_hypotheses,
            human_review_required=result.human_review_assessment.human_review_required,
            review_reasons=result.review_reasons,
        )

    return run_investigation
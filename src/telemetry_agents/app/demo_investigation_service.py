from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from telemetry_agents.app.demo_cases import load_incident_file
from telemetry_agents.app.workflow_runner import (
    RunWorkflow,
    WorkflowRunRequest,
    ResumeWorkflow,
    WorkflowResumeRequest,
)
from telemetry_agents.domain import ReviewedHypothesis
from telemetry_agents.infrastructure.run_registry import (
    create_investigation_run,
    update_investigation_run,
    get_resumable_investigation_run,
    InvestigationRunStatus,
)
from telemetry_agents.shared.observability import new_run_id


class RunNotFound(Exception):
    pass


class DemoInvestigationResult(BaseModel):
    run_id: str
    incident_id: str
    hypotheses: list[ReviewedHypothesis]
    human_review_required: bool
    review_reasons: list[str]


RunDemoInvestigation = Callable[[str], DemoInvestigationResult]


@dataclass(frozen=True)
class DemoInvestigationService:
    run_workflow: RunWorkflow
    resume_workflow: ResumeWorkflow
    demo_data_root: Path
    run_registry_db_path: Path

    def start(self, case_id: str) -> DemoInvestigationResult:
        run_id = new_run_id()
        incident = load_incident_file(self.demo_data_root / case_id / "incident.json")

        create_investigation_run(
            db_path=self.run_registry_db_path,
            run_id=run_id,
            incident_id=incident.incident_id,
            status=InvestigationRunStatus.PENDING,
        )

        result = self.run_workflow(
            WorkflowRunRequest(
                run_id=run_id,
                case_id=case_id,
                incident=incident,
                data_root=self.demo_data_root / case_id,
                auto_approve_human_review=False,
            )
        )

        status = (
            InvestigationRunStatus.AWAITING_REVIEW
            if result.human_review_assessment.human_review_required
            else InvestigationRunStatus.COMPLETED
        )
        update_investigation_run(
            db_path=self.run_registry_db_path,
            run_id=run_id,
            incident_id=incident.incident_id,
            status=status,
        )

        return DemoInvestigationResult(
            run_id=run_id,
            incident_id=result.incident.incident_id,
            hypotheses=result.review_result.reviewed_hypotheses,
            human_review_required=result.human_review_assessment.human_review_required,
            review_reasons=result.review_reasons,
        )

    def review(self, run_id: str, approved: bool) -> DemoInvestigationResult:
        record = get_resumable_investigation_run(
            self.run_registry_db_path, run_id=run_id
        )
        if record is None:
            raise RunNotFound(f"Run {run_id} not found")

        result = self.resume_workflow(
            WorkflowResumeRequest(
                run_id=record.run_id,
                approved=approved,
            )
        )
        status = (
            InvestigationRunStatus.COMPLETED
            if approved
            else InvestigationRunStatus.REJECTED
        )
        update_investigation_run(
            db_path=self.run_registry_db_path,
            run_id=run_id,
            incident_id=result.incident.incident_id,
            status=status,
        )

        return DemoInvestigationResult(
            run_id=run_id,
            incident_id=result.incident.incident_id,
            hypotheses=result.review_result.reviewed_hypotheses,
            human_review_required=result.human_review_assessment.human_review_required,
            review_reasons=result.review_reasons,
        )


def build_demo_investigation_service(
    run_workflow: RunWorkflow,
    resume_workflow: ResumeWorkflow,
    demo_data_root: Path,
    run_registry_db_path: Path,
) -> DemoInvestigationService:
    return DemoInvestigationService(
        run_workflow=run_workflow,
        resume_workflow=resume_workflow,
        demo_data_root=demo_data_root,
        run_registry_db_path=run_registry_db_path,
    )

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command
from pydantic import BaseModel

from telemetry_agents.domain import (
    Incident,
    HypothesisValidationResult,
    HypothesisReviewResult,
    HumanReviewAssessment,
)
from telemetry_agents.graph.investigation_workflow import build_investigation_workflow
from telemetry_agents.investigation.evidence_retrieval import (
    RetrievedEvidence,
    retrieve_evidence,
    EvidenceRetrievalRequest,
)
from telemetry_agents.investigation.hypothesis_critic import HypothesisCritic
from telemetry_agents.investigation.hypothesis_generation import HypothesisGenerator
from telemetry_agents.shared.tracing import get_tracer


class WorkflowRunRequest(BaseModel):
    run_id: str
    case_id: str
    incident: Incident
    data_root: Path
    auto_approve_human_review: bool = False


class WorkflowRunResult(BaseModel):
    run_id: str
    incident: Incident
    retrieved_evidence: list[RetrievedEvidence]
    validation_result: HypothesisValidationResult
    review_result: HypothesisReviewResult
    human_review_assessment: HumanReviewAssessment
    review_reasons: list[str]
    warnings: list[str]
    report_ready: bool


class WorkflowResumeRequest(BaseModel):
    run_id: str
    approved: bool


class WorkflowStateUnavailable(Exception):
    pass


RunWorkflow = Callable[[WorkflowRunRequest], WorkflowRunResult]
ResumeWorkflow = Callable[[WorkflowResumeRequest], WorkflowRunResult]
ReadWorkflowState = Callable[[str], WorkflowRunResult]

_REQUIRED_RESTORED_STATE_KEYS = (
    "normalized_incident",
    "collected_evidence",
    "validation_result",
    "review_result",
    "human_review_assessment",
    "warnings",
)


@dataclass(frozen=True)
class WorkflowService:
    run: RunWorkflow
    resume: ResumeWorkflow
    read_state: ReadWorkflowState


def _load_evidence(
    run_id: str, incident: Incident, data_root: Path
) -> list[RetrievedEvidence]:
    return retrieve_evidence(
        request=EvidenceRetrievalRequest(
            run_id=run_id,
            trace_id=incident.retrieval.trace_id,
            incident_id=incident.incident_id,
            service=incident.service,
            data_root=str(data_root),
            start_timestamp=incident.investigation_window.start.isoformat(),
            end_timestamp=incident.investigation_window.end.isoformat(),
            query_terms=incident.retrieval.query_terms,
        )
    )


def _review_reasons(assessment: HumanReviewAssessment) -> list[str]:
    return [assessment.human_review_reason] if assessment.human_review_reason else []


def _build_workflow_runner(
    *,
    generator: HypothesisGenerator,
    critic: HypothesisCritic,
    checkpointer: BaseCheckpointSaver[Any],
) -> RunWorkflow:
    def run(request: WorkflowRunRequest) -> WorkflowRunResult:
        graph = build_investigation_workflow(
            generator=generator,
            critic=critic,
            checkpointer=checkpointer,
        )
        evidence = _load_evidence(
            run_id=request.run_id,
            incident=request.incident,
            data_root=request.data_root,
        )
        tracer = get_tracer()
        with tracer.start_as_current_span("investigation.run") as run_span:
            run_span.set_attribute("run_id", request.run_id)
            run_span.set_attribute("incident_id", request.incident.incident_id)
            run_span.set_attribute("case_id", request.case_id)
            run_span.set_attribute("workflow.operation", "start")

            config: RunnableConfig = {"configurable": {"thread_id": request.run_id}}

            result = graph.invoke(
                {
                    "normalized_incident": request.incident,
                    "collected_evidence": evidence,
                    "run_id": request.run_id,
                },
                config=config,
            )
            interrupted = result.get("__interrupt__") is not None
            run_span.set_attribute("workflow.interrupted", interrupted)

            if interrupted and request.auto_approve_human_review:
                run_span.set_attribute("human_review.auto_approved", True)
                result = graph.invoke(Command(resume={"approved": True}), config=config)
            elif interrupted:
                snapshot = graph.get_state(config)
                result = snapshot.values

            evidence = result["collected_evidence"]

            return WorkflowRunResult(
                run_id=request.run_id,
                incident=request.incident,
                retrieved_evidence=evidence,
                validation_result=result["validation_result"],
                review_result=result["review_result"],
                human_review_assessment=result["human_review_assessment"],
                review_reasons=_review_reasons(result["human_review_assessment"]),
                warnings=result["warnings"],
                report_ready=result.get("report_ready", False),
            )

    return run


def _build_resume_workflow_runner(
    *,
    generator: HypothesisGenerator,
    critic: HypothesisCritic,
    checkpointer: BaseCheckpointSaver[Any],
) -> ResumeWorkflow:
    def run(request: WorkflowResumeRequest) -> WorkflowRunResult:
        graph = build_investigation_workflow(
            generator=generator,
            critic=critic,
            checkpointer=checkpointer,
        )

        tracer = get_tracer()
        with tracer.start_as_current_span("investigation.run") as run_span:
            run_span.set_attribute("run_id", request.run_id)
            run_span.set_attribute("workflow.operation", "resume")
            run_span.set_attribute("human_review.approved", request.approved)

            config: RunnableConfig = {"configurable": {"thread_id": request.run_id}}

            result = graph.invoke(
                Command(resume={"approved": request.approved}), config=config
            )
            run_span.set_attribute(
                "incident_id", result["normalized_incident"].incident_id
            )

            return WorkflowRunResult(
                run_id=request.run_id,
                incident=result["normalized_incident"],
                retrieved_evidence=result["collected_evidence"],
                validation_result=result["validation_result"],
                review_result=result["review_result"],
                human_review_assessment=result["human_review_assessment"],
                review_reasons=_review_reasons(result["human_review_assessment"]),
                warnings=result["warnings"],
                report_ready=result["report_ready"],
            )

    return run


def _build_workflow_state_reader(
    *,
    generator: HypothesisGenerator,
    critic: HypothesisCritic,
    checkpointer: BaseCheckpointSaver[Any],
) -> ReadWorkflowState:
    def read_state(run_id: str) -> WorkflowRunResult:
        graph = build_investigation_workflow(
            generator=generator,
            critic=critic,
            checkpointer=checkpointer,
        )

        config: RunnableConfig = {"configurable": {"thread_id": run_id}}
        result = graph.get_state(config)
        missing_keys = [
            key for key in _REQUIRED_RESTORED_STATE_KEYS if key not in result.values
        ]
        if missing_keys:
            raise WorkflowStateUnavailable(
                f"Workflow state for run {run_id} is unavailable or incomplete."
            )

        return WorkflowRunResult(
            run_id=run_id,
            incident=result.values["normalized_incident"],
            retrieved_evidence=result.values["collected_evidence"],
            validation_result=result.values["validation_result"],
            review_result=result.values["review_result"],
            human_review_assessment=result.values["human_review_assessment"],
            review_reasons=_review_reasons(result.values["human_review_assessment"]),
            warnings=result.values["warnings"],
            report_ready=result.values.get("report_ready", False),
        )

    return read_state


def build_workflow_service(
    *,
    generator: HypothesisGenerator,
    critic: HypothesisCritic,
    checkpointer: BaseCheckpointSaver[Any],
) -> WorkflowService:
    return WorkflowService(
        run=_build_workflow_runner(
            generator=generator, critic=critic, checkpointer=checkpointer
        ),
        resume=_build_resume_workflow_runner(
            generator=generator, critic=critic, checkpointer=checkpointer
        ),
        read_state=_build_workflow_state_reader(
            generator=generator, critic=critic, checkpointer=checkpointer
        ),
    )

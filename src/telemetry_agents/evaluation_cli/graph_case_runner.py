from pathlib import Path
from typing import Callable

from langgraph.checkpoint.memory import InMemorySaver

from telemetry_agents.app.demo_cases import load_incident_file
from telemetry_agents.app.workflow_runner import (
    WorkflowRunRequest,
    build_workflow_service,
)

from telemetry_agents.evaluation.models import (
    EvalCase,
    EvaluationRunOutput,
)
from telemetry_agents.investigation.hypothesis_critic import HypothesisCritic
from telemetry_agents.investigation.hypothesis_generation import HypothesisGenerator
from telemetry_agents.shared.observability import new_run_id

RunEvaluationCase = Callable[[EvalCase], EvaluationRunOutput]


def build_graph_case_runner(
    generator: HypothesisGenerator, critic: HypothesisCritic, data_root: Path
) -> RunEvaluationCase:
    def run_case(case: EvalCase) -> EvaluationRunOutput:
        run_id = new_run_id()
        incident = load_incident_file(data_root / case.incident_file)
        checkpointer = InMemorySaver()
        service = build_workflow_service(
            generator=generator, critic=critic, checkpointer=checkpointer
        )

        result = service.run(
            WorkflowRunRequest(
                run_id=run_id,
                case_id=case.case_id,
                incident=incident,
                data_root=data_root / case.case_id,
                auto_approve_human_review=True,
            )
        )

        return EvaluationRunOutput(
            validation_result=result.validation_result,
            review_result=result.review_result,
            human_review_assessment=result.human_review_assessment,
            warnings=result.warnings,
            retrieved_evidence=result.retrieved_evidence,
        )

    return run_case

import json
from pathlib import Path
from typing import Callable

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from telemetry_agents.domain import Incident

from telemetry_agents.evaluation.models import (
    EvalCase,
    EvaluationRunOutput,
)
from telemetry_agents.graph.investigation_workflow import build_investigation_workflow
from telemetry_agents.investigation.evidence_retrieval import (
    RetrievedEvidence,
    retrieve_evidence,
    EvidenceRetrievalRequest,
)
from telemetry_agents.investigation.hypothesis_critic import HypothesisCritic
from telemetry_agents.investigation.hypothesis_generation import HypothesisGenerator
from telemetry_agents.shared.observability import new_run_id

RunEvaluationCase = Callable[[EvalCase], EvaluationRunOutput]


def _load_incident(incident_file: str, data_root: Path) -> Incident:
    incident_path = data_root / incident_file
    with incident_path.open(encoding="utf-8") as file:
        data = json.load(file)
    return Incident.model_validate(data)


def _load_evidence(
    run_id: str, case_id: str, incident: Incident, data_root: Path
) -> list[RetrievedEvidence]:
    data_root = data_root / case_id

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


def build_graph_case_runner(
    generator: HypothesisGenerator, critic: HypothesisCritic, data_root: Path
) -> RunEvaluationCase:
    def run_case(case: EvalCase) -> EvaluationRunOutput:
        run_id = new_run_id()
        checkpointer = InMemorySaver()
        graph = build_investigation_workflow(
            generator=generator,
            critic=critic,
            checkpointer=checkpointer,
        )
        incident = _load_incident(case.incident_file, data_root)
        evidence = _load_evidence(run_id, case.case_id, incident, data_root)
        config: RunnableConfig = {"configurable": {"thread_id": incident.incident_id}}

        result = graph.invoke(
            {
                "normalized_incident": incident,
                "collected_evidence": evidence,
                "run_id": run_id,
            },
            config=config,
        )

        if result.get("__interrupt__") is not None:
            result = graph.invoke(Command(resume={"approved": True}), config=config)

        return EvaluationRunOutput(
            validation_result=result["validation_result"],
            review_result=result["review_result"],
            human_review_assessment=result["human_review_assessment"],
            warnings=result["warnings"],
            retrieved_evidence=evidence,
        )

    return run_case

import json
import os

from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from telemetry_agents.domain import Incident
from telemetry_agents.evaluation import (
    EvalCase,
    evaluate_case_output,
    GuardedUnsupportedClaimReviewer,
    EvaluationRunOutput,
)
from telemetry_agents.graph.investigation_workflow import build_investigation_workflow
from telemetry_agents.infrastructure.azure_openai_client import (
    create_azure_openai_client,
)
from telemetry_agents.infrastructure.azure_openai_hypothesis_critic import (
    AzureOpenAIHypothesisCritic,
)
from telemetry_agents.infrastructure.azure_openai_hypothesis_generator import (
    AzureOpenAIHypothesisGenerator,
)
from telemetry_agents.infrastructure.azure_openai_unsupported_claim_adapter import (
    AzureOpenAIUnsupportedClaimAdapter,
)
from telemetry_agents.investigation.evidence_retrieval import (
    retrieve_evidence,
    EvidenceRetrievalRequest,
    RetrievedEvidence,
)
from telemetry_agents.shared.paths import EVAL_DATA_DIR


def _load_eval_cases() -> list[EvalCase]:
    eval_cases_dir = EVAL_DATA_DIR / "cases"
    eval_cases: list[EvalCase] = []
    for eval_case_file in eval_cases_dir.glob("*.json"):
        with eval_case_file.open(encoding="utf-8") as file:
            data = json.load(file)
        eval_cases.append(EvalCase.model_validate(data))
    return eval_cases


def _load_incident(incident_file: str) -> Incident:
    incident_path = EVAL_DATA_DIR / incident_file
    with incident_path.open(encoding="utf-8") as file:
        data = json.load(file)
    return Incident.model_validate(data)


def _load_evidence(case_id: str, incident: Incident) -> list[RetrievedEvidence]:
    data_root = EVAL_DATA_DIR / case_id
    service = "checkout-api"

    return retrieve_evidence(
        request=EvidenceRetrievalRequest(
            trace_id=incident.retrieval.trace_id,
            incident_id=incident.incident_id,
            service=service,
            data_root=str(data_root),
            start_timestamp=incident.investigation_window.start.isoformat(),
            end_timestamp=incident.investigation_window.end.isoformat(),
            query_terms=incident.retrieval.query_terms,
        )
    )


def run_evaluation() -> None:
    eval_cases = _load_eval_cases()
    for eval_case in eval_cases[1:]:
        incident = _load_incident(eval_case.incident_file)
        evidence = _load_evidence(eval_case.case_id, incident)

        load_dotenv()

        endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
        deployment_name = os.environ["AZURE_OPENAI_HYPOTHESIS_DEPLOYMENT_NAME"]

        generator_client = create_azure_openai_client(
            endpoint=endpoint,
        )
        generator = AzureOpenAIHypothesisGenerator(
            client=generator_client,
            deployment_name=deployment_name,
        )

        critic_client = create_azure_openai_client(endpoint=endpoint)
        critic = AzureOpenAIHypothesisCritic(
            client=critic_client,
            deployment_name=deployment_name,
        )

        checkpointer = InMemorySaver()

        reviewer_client = create_azure_openai_client(
            endpoint=endpoint,
        )
        adapter = AzureOpenAIUnsupportedClaimAdapter(
            client=reviewer_client,
            deployment_name=deployment_name,
        )

        reviewer = GuardedUnsupportedClaimReviewer(
            adapter=adapter,
        )

        graph = build_investigation_workflow(
            generator=generator,
            critic=critic,
            checkpointer=checkpointer,
        )

        config: RunnableConfig = {"configurable": {"thread_id": "run-001"}}

        result = graph.invoke(
            {
                "normalized_incident": incident,
                "collected_evidence": evidence,
            },
            config=config,
        )

        if result.get("__interrupt__") is not None:
            result = graph.invoke(Command(resume={"approved": True}), config=config)

        output = EvaluationRunOutput(
            validation_result=result["validation_result"],
            review_result=result["review_result"],
            human_review_assessment=result["human_review_assessment"],
            warnings=result["warnings"],
            retrieved_evidence=evidence,
        )

        eval_result = evaluate_case_output(
            case=eval_case, output=output, reviewer=reviewer
        )
        print(f"Eval case {eval_case.case_id}, eval result: {eval_result.passed}")


if __name__ == "__main__":
    run_evaluation()

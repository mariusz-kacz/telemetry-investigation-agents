from openai import OpenAI, APIConnectionError, APITimeoutError, RateLimitError
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel

from telemetry_agents.domain import InvestigationHypothesis
from telemetry_agents.investigation.hypothesis_generation import (
    HypothesisGenerationRequest,
    HypothesisGeneratorUnavailableError,
)
from telemetry_agents.shared.observability import (
    observe_llm_call,
)


class InvestigationHypothesisResponse(BaseModel):
    hypotheses: list[InvestigationHypothesis]


class AzureOpenAIHypothesisGenerator:
    def __init__(self, *, client: OpenAI, deployment_name: str) -> None:
        self.client = client
        self.deployment_name = deployment_name

    def generate(
        self,
        request: HypothesisGenerationRequest,
    ) -> list[InvestigationHypothesis]:
        with observe_llm_call(
            run_id=request.run_id,
            incident_id=request.incident.incident_id,
            provider="azure_openai",
            operation="hypothesis_generation",
            deployment_name=self.deployment_name,
            output_schema=InvestigationHypothesisResponse.__name__,
        ) as observation:
            try:
                completion = self.client.beta.chat.completions.parse(
                    model=self.deployment_name,
                    messages=[
                        ChatCompletionSystemMessageParam(
                            content=(
                                "Generate zero or more candidate investigation hypotheses from only the "
                                "provided incident and evidence. Reference only evidence IDs present in "
                                "the supplied context. State uncertainty when evidence is insufficient. "
                                "For every hypothesis with confidence below 0.8, uncertainty must be a "
                                "non-empty string. Do not use null, empty string, or whitespace for "
                                "uncertainty in low-confidence hypotheses. "
                                "Assign exactly one coarse category to each hypothesis using the structured "
                                "output schema. Treat the category as a proposed classification, not a "
                                "validated conclusion. "
                                "Use DATABASE_FAILURE when the failed component is a database or datastore "
                                "path and the evidence includes database-specific operations or metrics, such "
                                "as orders-db, INSERT/SELECT/UPDATE operations, query latency, query timeout "
                                "rate, locks, connections, or storage I/O. Do not classify these as "
                                "DOWNSTREAM_DEPENDENCY_FAILURE just because the incident service is waiting "
                                "on the database. Use DOWNSTREAM_DEPENDENCY_FAILURE for non-database external "
                                "services or APIs. "
                                "Do not hypothesize configuration changes, timeout or retry policy problems, "
                                "feature flags, deployments, or code behavior unless the supplied evidence "
                                "includes configuration, deployment, code, change-log, or explicit log evidence "
                                "for that mechanism. It is acceptable to say a request exceeded a client "
                                "timeout when logs or traces show that. It is not acceptable to say the timeout "
                                "configuration was too aggressive or changed without config or change evidence. "
                                "If evidence supports multiple materially different root-cause directions and "
                                "no single cause clearly dominates, generate an UNCERTAIN_ROOT_CAUSE hypothesis. "
                                "State the competing interpretations and cite evidence for each. Do not force "
                                "a single concrete category when telemetry is mixed across database, downstream "
                                "service, application, or metric-anomaly signals. When this conflicting-evidence "
                                "rule applies, generate exactly one UNCERTAIN_ROOT_CAUSE hypothesis and do not "
                                "generate competing concrete causal hypotheses. "
                                "If the evidence shows symptoms, correlation, or elevated metrics but does not "
                                "directly support a root-cause mechanism, generate an INSUFFICIENT_EVIDENCE "
                                "hypothesis instead of a concrete causal category. Do not claim that latency, "
                                "timeout rate, or error logs caused the incident unless the supplied evidence "
                                "shows the causal path. When this insufficient-evidence rule applies, generate "
                                "exactly one INSUFFICIENT_EVIDENCE hypothesis and do not generate competing "
                                "concrete causal hypotheses or UNCERTAIN_ROOT_CAUSE alternatives. The statement "
                                "should say what is observed and what evidence is missing, not list speculative "
                                "root causes. "
                                "Do not present candidates as validated conclusions."
                            ),
                            role="system",
                        ),
                        ChatCompletionUserMessageParam(
                            content=request.model_dump_json(indent=2), role="user"
                        ),
                    ],
                    response_format=InvestigationHypothesisResponse,
                )
            except (APIConnectionError, APITimeoutError, RateLimitError) as exc:
                observation.fail(exc)
                raise HypothesisGeneratorUnavailableError(str(exc)) from exc

            event = completion.choices[0].message.parsed
            if event is None:
                raise ValueError("Invalid empty response from OpenAI.")

            observation.complete(hypothesis_count=len(event.hypotheses))
            return event.hypotheses

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel

from telemetry_agents.domain import InvestigationHypothesis
from telemetry_agents.investigation.hypothesis_generation import (
    HypothesisGenerationRequest,
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
        completion = self.client.beta.chat.completions.parse(
            model=self.deployment_name,
            messages=[
                ChatCompletionSystemMessageParam(
                    content=(
                        "Generate zero or more candidate investigation hypotheses from only the "
                        "provided incident and evidence. Reference only evidence IDs present in "
                        "the supplied context. State uncertainty when evidence is insufficient. "
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

        event = completion.choices[0].message.parsed
        if event is None:
            raise ValueError("Invalid empty response from OpenAI.")

        return event.hypotheses

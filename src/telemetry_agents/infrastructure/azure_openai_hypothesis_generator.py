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

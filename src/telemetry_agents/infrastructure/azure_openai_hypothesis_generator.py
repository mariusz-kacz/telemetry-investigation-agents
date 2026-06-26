from openai import OpenAI, APIConnectionError, APITimeoutError, RateLimitError
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel

from telemetry_agents.domain import InvestigationHypothesis
from telemetry_agents.infrastructure.prompt_loader import load_prompt
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
                prompt = load_prompt("hypothesis_generator.md")
                completion = self.client.beta.chat.completions.parse(
                    model=self.deployment_name,
                    messages=[
                        ChatCompletionSystemMessageParam(
                            content=prompt,
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

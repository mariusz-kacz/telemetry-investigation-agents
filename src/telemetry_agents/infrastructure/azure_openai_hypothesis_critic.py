from openai import OpenAI, APIConnectionError, APITimeoutError, RateLimitError
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from telemetry_agents.domain import HypothesisCritiqueResult
from telemetry_agents.infrastructure.prompt_loader import load_prompt
from telemetry_agents.investigation.hypothesis_critic import (
    HypothesisCritiqueRequest,
    HypothesisCriticUnavailableError,
)
from telemetry_agents.shared.observability import observe_llm_call


class AzureOpenAIHypothesisCritic:
    def __init__(self, *, client: OpenAI, deployment_name: str) -> None:
        self.client = client
        self.deployment_name = deployment_name

    def critique(
        self,
        request: HypothesisCritiqueRequest,
    ) -> HypothesisCritiqueResult:
        with observe_llm_call(
            run_id=request.run_id,
            incident_id=request.incident_id,
            provider="azure_openai",
            operation="hypothesis_critic",
            deployment_name=self.deployment_name,
            output_schema=HypothesisCritiqueResult.__name__,
        ) as observation:
            try:
                prompt = load_prompt("hypothesis_critic.md")
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
                    response_format=HypothesisCritiqueResult,
                )
            except (APIConnectionError, APITimeoutError, RateLimitError) as exc:
                observation.fail(exc)
                raise HypothesisCriticUnavailableError(str(exc)) from exc

            event = completion.choices[0].message.parsed
            if event is None:
                raise ValueError("Invalid empty response from OpenAI.")

            observation.complete(
                finding_count=len(event.critique_findings),
                finding_types=sorted(
                    {finding.finding_type.value for finding in event.critique_findings}
                ),
            )
            return event

from openai import OpenAI, APIConnectionError, APITimeoutError, RateLimitError
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from telemetry_agents.domain import HypothesisCritiqueResult
from telemetry_agents.investigation.hypothesis_critic import (
    HypothesisCritiqueRequest,
    HypothesisCriticUnavailableError,
)


class AzureOpenAIHypothesisCritic:
    def __init__(self, *, client: OpenAI, deployment_name: str) -> None:
        self.client = client
        self.deployment_name = deployment_name

    def critique(
        self,
        request: HypothesisCritiqueRequest,
    ) -> HypothesisCritiqueResult:
        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.deployment_name,
                messages=[
                    ChatCompletionSystemMessageParam(
                        content=(
                            "Review accepted investigation hypotheses for semantic problems only. "
                            "Do not generate new hypotheses. Do not rewrite hypotheses. "
                            "Review whether each hypothesis category is semantically consistent "
                            "with its statement and cited evidence. Report category inconsistencies "
                            "using the existing critique finding types. "
                            "Return critique findings only when the supplied evidence suggests a "
                            "contradiction, unsupported causal leap, alternative interpretation, or "
                            "overstated confidence. Reference only hypothesis IDs from the accepted "
                            "hypotheses in the validation result. Reference only evidence IDs present "
                            "in the supplied evidence context. Do not cite missing evidence as support "
                            "for a critique finding. If there are no semantic concerns, return an empty "
                            "critique_findings list."
                        ),
                        role="system",
                    ),
                    ChatCompletionUserMessageParam(
                        content=request.model_dump_json(indent=2), role="user"
                    ),
                ],
                response_format=HypothesisCritiqueResult,
            )
        except (APIConnectionError, APITimeoutError, RateLimitError) as exc:
            raise HypothesisCriticUnavailableError(str(exc)) from exc

        event = completion.choices[0].message.parsed
        if event is None:
            raise ValueError("Invalid empty response from OpenAI.")

        return event

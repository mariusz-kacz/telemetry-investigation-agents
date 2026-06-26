from openai import OpenAI, APIConnectionError, APITimeoutError, RateLimitError
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from telemetry_agents.evaluation.unsupported_claim_review import (
    UnsupportedClaimReviewRequest,
    UnsupportedClaimReviewResult,
    UnsupportedClaimReviewerUnavailableError,
)
from telemetry_agents.infrastructure.prompt_loader import load_prompt


class AzureOpenAIUnsupportedClaimAdapter:
    def __init__(self, *, client: OpenAI, deployment_name: str) -> None:
        self.client = client
        self.deployment_name = deployment_name

    def review(
        self,
        request: UnsupportedClaimReviewRequest,
    ) -> UnsupportedClaimReviewResult:
        """Review validated hypotheses without changing workflow state."""
        try:
            prompt = load_prompt("unsupported_claim_reviewer.md")
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
                response_format=UnsupportedClaimReviewResult,
            )
        except (APIConnectionError, APITimeoutError, RateLimitError) as exc:
            raise UnsupportedClaimReviewerUnavailableError(str(exc)) from exc

        event = completion.choices[0].message.parsed
        if event is None:
            raise ValueError("Invalid empty response from OpenAI.")

        return event

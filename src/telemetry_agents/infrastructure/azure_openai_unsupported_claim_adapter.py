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


class AzureOpenAIUnsupportedClaimAdapter:
    def __init__(self, *, client: OpenAI, deployment_name: str) -> None:
        self.client = client
        self.deployment_name = deployment_name

    def review(
        self,
        request: UnsupportedClaimReviewRequest,
    ) -> UnsupportedClaimReviewResult:
        """Review accepted hypotheses without changing workflow state."""
        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.deployment_name,
                messages=[
                    ChatCompletionSystemMessageParam(
                        content=(
                            "Review accepted investigation hypotheses for unsupported causal claims "
                            "only. Report findings only for the supplied accepted hypotheses. "
                            "Reference only hypothesis IDs from the accepted hypotheses and only "
                            "evidence IDs from the supplied evidence context. Do not use missing "
                            "evidence as support. Do not change workflow state. If the accepted "
                            "hypotheses contain no unsupported causal claims, return an empty "
                            "findings list."
                        ),
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

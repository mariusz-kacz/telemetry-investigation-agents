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
from telemetry_agents.shared.observability import observe_llm_call


class AzureOpenAIUnsupportedClaimAdapter:
    def __init__(self, *, client: OpenAI, deployment_name: str) -> None:
        self.client = client
        self.deployment_name = deployment_name

    def review(
        self,
        request: UnsupportedClaimReviewRequest,
    ) -> UnsupportedClaimReviewResult:
        """Review validated hypotheses without changing workflow state."""
        with observe_llm_call(
            run_id=request.run_id,
            case_id=request.case_id,
            provider="azure_openai",
            operation="unsupported_claim_review",
            deployment_name=self.deployment_name,
            output_schema=UnsupportedClaimReviewResult.__name__,
        ) as observation:
            try:
                completion = self.client.beta.chat.completions.parse(
                    model=self.deployment_name,
                    messages=[
                        ChatCompletionSystemMessageParam(
                            content=(
                                "Review validated investigation hypotheses for unsupported causal claims "
                                "only. Report findings only for the supplied validated hypotheses. "
                                "Reference only hypothesis IDs from the validated hypotheses and only "
                                "evidence IDs from the supplied evidence context. Do not use missing "
                                "evidence as support. Copy hypothesis IDs and evidence IDs exactly as "
                                "supplied; do not rename, normalize, reformat, translate, or change "
                                "hyphens and underscores in IDs. Do not change workflow state. If the accepted "
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
                observation.fail(exc)
                raise UnsupportedClaimReviewerUnavailableError(str(exc)) from exc

            event = completion.choices[0].message.parsed
            if event is None:
                raise ValueError("Invalid empty response from OpenAI.")

            observation.complete(finding_count=len(event.findings))
            return event

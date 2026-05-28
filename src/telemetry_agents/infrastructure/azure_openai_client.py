from azure.identity import get_bearer_token_provider, DefaultAzureCredential
from openai import OpenAI


def create_azure_openai_client(*, endpoint: str) -> OpenAI:
    """Azure OpenAI implementation boundary for OpenAI client.

    Authentication for this adapter must use Microsoft Entra ID through
    DefaultAzureCredential. API-key support is intentionally out of scope.
    """
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://ai.azure.com/.default",
    )
    return OpenAI(base_url=endpoint, api_key=token_provider)

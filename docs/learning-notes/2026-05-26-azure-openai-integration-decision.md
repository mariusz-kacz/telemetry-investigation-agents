# Session: Azure OpenAI integration decision

## Goal

Decide whether to connect a real model provider before starting the evaluation framework.

## What I built

The learning journey now includes a bounded Phase 13 for Azure OpenAI adapter integration and graph-level live smoke before Phase 14 evaluations. I selected Microsoft Entra ID authentication through `DefaultAzureCredential` as the only initial credential path.

I added concrete Azure OpenAI adapters for hypothesis generation and hypothesis critique behind the existing `HypothesisGenerator` and `HypothesisCritic` protocols. The adapters use structured output parsing into the existing Pydantic contracts instead of returning untyped provider JSON.

## LangGraph concept learned

LangGraph can own orchestration while a cloud model provider remains an injected implementation of an existing application boundary. A real LLM integration does not require moving workflow control, deterministic validation, or human-review routing into a hosted agent platform.

## Mapping to .NET/C# thinking

The existing `HypothesisGenerator` and `HypothesisCritic` protocols are sufficient dependency boundaries for concrete Azure OpenAI adapters. The next step should not add a broad provider service hierarchy or duplicate orchestration layer merely because an enterprise cloud platform is involved.

## What confused me

Using Azure OpenAI is not automatically an architecture improvement. It adds portfolio value only when its enterprise concerns are explicit: identity, RBAC, deployment configuration, provider failure behavior, and bounded model responsibilities.

The deployment used for live smoke validation was `hypothesis-model`, which supports structured outputs.

## Tradeoffs noticed

Azure OpenAI requires more setup than direct OpenAI API integration, particularly for deployment availability and Microsoft Entra ID authentication. It is accepted here because Microsoft-oriented enterprise AI positioning is a stated project objective.

The provider must remain behind current protocols. Foundry-hosted agent orchestration is deliberately excluded because LangGraph already owns the workflow in this project.

Microsoft Entra ID is less convenient than a local API key for the first live invocation, because local identity and RBAC must be configured correctly. That complexity is accepted because identity-based access is the enterprise boundary this portfolio project is intended to demonstrate. API-key fallback is deliberately deferred.

Adapter-level live smoke tests prove provider connectivity and structured-output compatibility. A graph-level live smoke test now couples the compiled graph nodes with the Azure generator and critic adapters in a single execution.

## Production concerns

- Use Microsoft Entra ID through `DefaultAzureCredential`; do not store or support API keys in the initial adapter.
- Keep live model calls opt-in and out of ordinary unit tests.
- Require typed structured outputs and retain deterministic evidence-reference validation.
- Treat quota, region, model deployment, and provider unavailability as infrastructure concerns.
- Do not claim model quality from a single live smoke run; that is the purpose of Phase 14 evaluations.
- The critic adapter translates temporary provider availability failures into the existing safe fallback path; configuration or schema problems should still fail loudly.
- Live adapter success proves provider connectivity and schema compatibility, not investigation quality.

## Tests/evals added

- Mocked Azure OpenAI generator tests cover structured response parsing, prompt/request wiring, empty provider response, and provider connection failure propagation.
- Mocked Azure OpenAI critic tests cover structured response parsing, prompt/request wiring, valid empty critique results, empty provider response, and provider availability translation.
- Opt-in live smoke tests exist for both generator and critic adapters using synthetic evidence and the `hypothesis-model` deployment.
- An opt-in graph-level live smoke test executed successfully with the Azure generator and critic adapters wired into the compiled graph. It exercised generation, validation, critic review, human-review routing, interrupt/resume, and report-ready marking.
- Normal unit tests remain credential-free.

## Next step

Begin Phase 14 by defining evaluation cases that inspect evidence-reference quality, unsupported claims, escalation behavior, and model-backed output quality. Do not tune prompts before the scoring loop exists.

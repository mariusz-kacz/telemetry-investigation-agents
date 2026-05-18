# Session: Agentic hypothesis generation

## Goal

Introduce LLM-assisted hypothesis generation without letting the LLM become the source of truth.

## What I built

Added a `HypothesisGenerator` protocol, a `HypothesisGenerationRequest`, deterministic hypothesis guardrails, and a thin LangGraph hypothesis-generation node.

The generator proposes `InvestigationHypothesis` objects. Deterministic code then verifies cited evidence IDs, rejects missing evidence as support, caps confidence based on evidence strength, and ensures low-confidence hypotheses carry uncertainty.

## LangGraph concept learned

A LangGraph node should be a workflow adapter, not the place where business rules accumulate. The hypothesis node reads graph state, builds an application request, calls `generate_hypotheses`, and returns a state update with `hypotheses`.

## Mapping to .NET/C# thinking

`HypothesisGenerator` is similar to an interface, but Python uses a lightweight `Protocol`: any object with a compatible `generate` method satisfies the contract. The real provider adapter belongs in infrastructure, while investigation logic stays testable and provider-independent.

## What confused me

Weak evidence and missing evidence require different behavior. Weak evidence can support a low-confidence hypothesis with uncertainty. Missing or unknown evidence cannot support a hypothesis and should be rejected.

## Tradeoffs noticed

The confidence cap is intentionally simple for this phase. It is enough to prove the boundary: the LLM can propose confidence, but deterministic code limits confidence based on evidence quality. More precise scoring belongs later with validation and evals.

## Production concerns

LLM output must be treated as untrusted. A production system cannot rely on prompt instructions alone for citation correctness, confidence, or uncertainty handling. Those constraints need deterministic checks and tests.

## Tests/evals added

Unit tests cover unknown evidence references, mixed valid and hallucinated evidence references, missing evidence support, confidence caps for weak and medium evidence, strong evidence preserving high confidence, non-mutation of generator-owned hypotheses, and LangGraph node state translation.

## Next step

Move to the critic / evidence validator phase after the Phase 8 checkpoint is approved and the progress board is updated.

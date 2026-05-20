# Session: Agentic hypothesis generation

## Goal

Introduce LLM-assisted hypothesis generation without letting the LLM become the source of truth.

## What I built

Added a `HypothesisGenerator` protocol, a `HypothesisGenerationRequest`, and a thin LangGraph hypothesis-generation node.

The generator proposes `InvestigationHypothesis` objects. Evidence-reference policy and confidence policy now belong to the deterministic validator, so generation stays focused on producing typed candidate hypotheses from bounded context.

## LangGraph concept learned

A LangGraph node should be a workflow adapter, not the place where business rules accumulate. The hypothesis node reads graph state, builds an application request, calls `generate_hypotheses`, and returns a state update with `hypotheses`.

## Mapping to .NET/C# thinking

`HypothesisGenerator` is similar to an interface, but Python uses a lightweight `Protocol`: any object with a compatible `generate` method satisfies the contract. The real provider adapter belongs in infrastructure, while investigation logic stays testable and provider-independent.

## What confused me

Weak evidence and missing evidence require different behavior, but generation should not make that policy decision. The validator decides whether weak evidence can support a low-confidence hypothesis and whether missing or unknown evidence should reject a candidate.

## Tradeoffs noticed

The generator/validator split is intentionally simple. The LLM can propose candidates, but deterministic validation decides which candidates are evidence-usable and how much confidence they can carry.

## Production concerns

LLM output must be treated as untrusted. A production system cannot rely on prompt instructions alone for citation correctness, confidence, or uncertainty handling. Those constraints need deterministic validation and tests.

## Tests/evals added

Unit tests cover generator candidate pass-through, empty candidate lists, and LangGraph node state translation. Evidence-reference checks and confidence caps are covered by validator tests.

## Next step

Move to the critic / evidence validator phase after the Phase 8 checkpoint is approved and the progress board is updated.

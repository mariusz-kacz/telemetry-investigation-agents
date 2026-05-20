# Session: Critic / evidence validator

## Goal

Add a deterministic validation step after hypothesis generation so generated hypotheses are reviewed against retrieved evidence before they can be used downstream.

## What I built

Added a structured `HypothesisValidationResult` with accepted hypotheses, rejected hypotheses, confidence adjustments, and a placeholder for contradictions.

Added `validate_hypotheses()` as the deterministic validation boundary. It rejects hypotheses with no supporting evidence IDs, unknown evidence IDs, or missing evidence used as support. It accepts weak and medium evidence when plausible, but caps overconfident hypotheses and records confidence adjustment reasons.

Added a LangGraph hypothesis validation node that requires `collected_evidence` and `hypotheses`, then writes `validation_result` back to graph state.

## LangGraph concept learned

A validation node should be a review step in the workflow, not just a helper function. It consumes prior graph state, produces a structured state update, and creates an audit trail that later report generation, human review, evals, and observability can inspect.

## Mapping to .NET/C# thinking

This resembles a validation/application-service boundary, but the Python design stays lighter: plain functions, Pydantic models, and small graph node wrappers instead of a large validator class hierarchy.

The important boundary is behavioral, not inheritance-based: generation produces typed candidate hypotheses, while validation decides whether they survive evidence-based review.

## What confused me

The main confusion was where confidence adjustment belongs. It started in hypothesis generation, but it fits validation better because confidence depends on evidence strength, not merely whether the LLM output is structurally valid.

Another design question was contradiction detection. General contradiction detection is semantic and broad, so it is deferred to a later LLM critic rather than hardcoded into fragile deterministic rules.

## Tradeoffs noticed

The validation boundary owns evidence policy:

- generation produces typed candidates,
- validation acts as the trust and audit boundary.

The deterministic validator is intentionally narrow. It handles reference integrity, missing support, missing evidence, confidence policy, and audit reasons. It does not claim to understand every possible semantic contradiction.

## Production concerns

Validation results need to be structured because later production concerns depend on them:

- human reviewers need to see why confidence changed,
- reports need cited reasoning,
- evals need to detect unsupported claims,
- observability needs inspectable validation events.

An LLM critic can later enrich `HypothesisValidationResult`, but its cited IDs and reasons must still be validated deterministically.

## Tests/evals added

Unit tests cover:

- rejecting hypotheses without supporting evidence,
- rejecting unknown evidence IDs,
- rejecting missing evidence used as support,
- downgrading weak and medium evidence overconfidence,
- preserving confidence when strong evidence supports it,
- preserving original hypothesis objects when adjusted copies are returned,
- allowing an empty hypothesis list,
- graph node state preconditions and output.

## Next step

Move to the LLM critic for semantic review after the Phase 9 checkpoint is accepted and the progress board is updated.

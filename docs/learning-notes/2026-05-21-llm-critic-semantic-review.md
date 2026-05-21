# Session: LLM critic semantic review

## Goal

Add a separate LLM critic step after deterministic hypothesis validation, so semantic issues can be reviewed without weakening the deterministic evidence boundary.

## What I built

Added a `HypothesisCritic` protocol and `HypothesisCritiqueRequest` boundary for an LLM-backed critic adapter.

Added `critique_hypotheses()` to call the critic and validate critic output against known accepted hypothesis IDs and known retrieved evidence IDs.

Added a separate LangGraph critic node that reads `collected_evidence` and `validation_result`, writes `critique_findings`, and records a warning when the critic adapter is unavailable.

Added a warning reducer to graph state so warning updates can accumulate instead of overwriting each other.

## LangGraph concept learned

A graph node can represent a risk-control review step, not only a data transformation. The critic node consumes trusted validation state, calls an unreliable LLM-backed adapter, and returns a bounded state update.

The graph owns fallback orchestration. The critic adapter reports a known unavailability failure, while deterministic guardrails still reject unsafe critic output.

## Mapping to .NET/C# thinking

The critic adapter resembles an interface boundary, but the Python design stays lightweight with a `Protocol`, small request/result models, and plain functions.

The important distinction is responsibility, not class layering:

- validator: deterministic evidence and confidence policy,
- critic: semantic risk review,
- graph node: workflow fallback and state update.

## What confused me

The main confusion was where to catch failures. Catching every exception inside the application function would hide adapter bugs and unsafe critic behavior. The better boundary is for concrete adapters to raise `HypothesisCriticUnavailableError`, and for the graph node to catch only that known fallback case.

Another design question was whether the critic should review rejected hypotheses. For this checkpoint it reviews accepted hypotheses only, because those are the hypotheses downstream nodes may trust.

## Tradeoffs noticed

Keeping critique findings separate from `HypothesisValidationResult` makes the validator/critic boundary explicit. Merging them could simplify downstream report generation, but it would blur deterministic validation with probabilistic critique.

The critic can identify contradictions, unsupported causal leaps, alternative interpretations, and overstated confidence, but it cannot increase confidence or directly mutate validated hypotheses.

## Production concerns

LLM critique is useful but unreliable. It must be constrained by structured output, known IDs, citation requirements, and fallback behavior.

If the critic is unavailable, the investigation can continue with a warning because deterministic validation has already protected reference integrity. If the critic cites unknown IDs or missing evidence, that is unsafe output and should fail loudly rather than be treated as ordinary unavailability.

## Tests/evals added

Tests cover:

- structured critic findings from a fake adapter,
- empty critic findings,
- rejecting unknown hypothesis IDs,
- rejecting unknown evidence IDs,
- rejecting missing evidence as critique support,
- critic node state preconditions,
- critic node writing critique findings,
- critic unavailable fallback warning,
- graph warning reducer annotation.

## Next step

Move to persistence, checkpointing, and interrupts. Do not add human review yet.

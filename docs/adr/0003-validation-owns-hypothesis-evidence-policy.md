# ADR 0003: Validation Owns Hypothesis Evidence Policy

## Status

Accepted

## Context

Phase 8 introduced bounded LLM-assisted hypothesis generation. The original generator helper rejected missing support, unknown evidence IDs, and missing evidence references before returning hypotheses.

Phase 9 then introduced a deterministic validator that performed the same evidence-reference checks and also capped confidence based on evidence strength. This made validation partly duplicative and weakened its role as the workflow trust boundary.

The core design question was whether the generator should police its own LLM output or whether generated hypotheses should enter graph state as untrusted candidates.

## Decision

Hypothesis generation produces typed candidate `InvestigationHypothesis` objects from bounded incident and evidence context.

Hypothesis validation owns evidence policy:

- every validated hypothesis must cite supporting evidence;
- cited evidence IDs must exist;
- missing evidence cannot be used as support;
- confidence is capped according to evidence strength;
- rejections and confidence changes are recorded in `HypothesisValidationResult`.

Raw generated `hypotheses` are untrusted candidate state. Downstream nodes should consume `validation_result` when they need evidence-reviewed hypotheses.

## Consequences

Positive consequences:

- The generator boundary is smaller and easier to test.
- Validation has a clear responsibility in the workflow.
- Evidence-policy decisions produce structured audit data instead of exceptions from generation.
- The LLM critic phase can build on `HypothesisValidationResult` rather than raw generated candidates.

Tradeoffs:

- Invalid candidate hypotheses may temporarily exist in graph state before validation runs.
- Graph wiring and future nodes must preserve the invariant that raw `hypotheses` are not trusted downstream.
- The graph state name `hypotheses` may become ambiguous; `candidate_hypotheses` may be clearer later.

## Alternatives considered

### Keep evidence checks in generation and validation

Rejected. The duplication made validation look ceremonial and produced two different failure styles: generation raised exceptions while validation returned structured audit results.

### Move all evidence policy into generation

Rejected. The generator should not judge its own LLM output. Evidence policy belongs at a deterministic trust boundary that downstream nodes can inspect.

### Add a separate confidence policy layer

Rejected for now. A separate service or class hierarchy would be premature. The current policy is small enough to live inside `hypothesis_validation.py`.

## Why this matters for Telemetry Investigation Agents

The project needs a clear answer to where hallucination control happens. This decision makes the answer explicit: generation proposes candidates, validation decides whether those candidates are evidence-usable, and later workflow steps trust the validation result rather than raw LLM output.

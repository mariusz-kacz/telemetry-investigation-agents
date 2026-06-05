# ADR 0007: Evaluation Before Prompt Optimization

## Status

Accepted

## Context

The investigation workflow uses LLMs for hypothesis generation, semantic critique,
and unsupported-claim review. Prompt changes can improve one case while silently
regressing another because the model output is probabilistic and sensitive to
wording.

Phase 14 introduced golden evaluation cases, deterministic scorecard dimensions,
and a separate semantic unsupported-claim reviewer. The evaluation framework now
checks evidence-source coverage, expected category, human-review behavior,
citation correctness, and unsupported causal claims.

## Decision

Prompt optimization must happen only after evaluation cases and scoring are in
place.

Prompt changes should be judged against the batch evaluation command:

```powershell
uv run telemetry-evals
```

Evaluation scoring should inspect accepted reviewed hypotheses for category and
unsupported-claim checks. Blocked or disputed hypotheses are not auto-usable
workflow conclusions, so they should not make a category pass and should not be
reviewed again for unsupported claims.

## Consequences

- Prompt changes have an objective regression check.
- The project can distinguish retrieval failures, category failures,
  human-review failures, citation failures, and semantic unsupported-claim
  failures.
- Evaluation remains separate from graph execution. The evaluator measures the
  workflow output; it does not influence graph state.
- Passing evals do not prove production correctness, but they provide a stable
  baseline for prompt and policy iteration.

## Alternatives Considered

Optimizing prompts first was rejected because it encourages tuning by anecdote
from one run and makes regressions hard to see.

Using only manual inspection was rejected because it is too subjective and does
not scale once multiple golden cases exist.

Using a single aggregate score was deferred because the MVP needs diagnostic
clarity more than weighted scoring.

## Why This Matters for Telemetry Investigation Agents

The system is designed to produce evidence-backed incident hypotheses, not just
plausible narratives. Evaluation before prompt optimization keeps the workflow
honest: prompt edits must preserve citation discipline, human-review behavior,
accepted-hypothesis category accuracy, and unsupported-claim guardrails.

# ADR 0005: Hypothesis Category Is Structured LLM-Proposed State

## Status

Accepted

## Context

Phase 14 introduced evaluation scoring for expected hypothesis categories.

The first implementation attempted to infer categories from hypothesis
statements using deterministic keyword matching. This produced false positives.
For example, a downstream service timeout could be incorrectly classified as a
database timeout because both statements contain the word `timeout`.

Deterministic code can validate evidence references, missing-evidence policy,
and confidence caps. It cannot reliably prove the semantic category of a
free-form hypothesis statement.

The project needs categories for evaluation, reporting, and human review without
pretending that keyword matching is semantic validation.

## Decision

Add a required `HypothesisCategory` field to `InvestigationHypothesis`.

The category taxonomy is intentionally coarse:

```text
database_failure
authentication_failure
downstream_dependency_failure
resource_saturation
network_failure
configuration_error
application_error
metric_anomaly
other
insufficient_evidence
```

The LLM-backed hypothesis generator proposes exactly one category for each
candidate hypothesis through structured output.

The category is not treated as a validated conclusion:

- Pydantic constrains category values to the known enum.
- Deterministic validation continues to own evidence-reference integrity and
  confidence policy.
- The LLM critic reviews whether a category is semantically consistent with the
  hypothesis statement and cited evidence.
- Evaluation compares the structured category against the expected scenario
  category.
- Human-review packets expose the proposed category beside the hypothesis.

## Consequences

Positive consequences:

- Evaluation no longer reverse-engineers categories from free-form prose.
- Category scoring is deterministic and auditable.
- Provider output cannot introduce arbitrary category strings.
- Reviewers can inspect the proposed category with the supporting evidence.
- The taxonomy stays stable while hypothesis statements preserve detail.

Tradeoffs:

- Category correctness remains probabilistic because the LLM proposes it.
- Existing hypothesis fixtures and provider prompts must include the category.
- The critic prompt must review category consistency.
- The taxonomy may need to expand when new scenarios do not fit cleanly.
- `other` and `insufficient_evidence` must remain valid outputs to avoid forced
  misclassification.

## Alternatives considered

### Infer categories from hypothesis text with keywords

Rejected. Keyword matching is useful for lightweight search but too brittle for
semantic correctness scoring. It produced false positives for generic timeout
language.

### Use a separate eval-only category classifier

Deferred. A separate classifier could be useful for independent evaluation, but
it would add another probabilistic component before the basic evaluation loop is
complete.

### Omit categories and evaluate free-form statements only

Rejected. Free-form-only evaluation makes regression scoring brittle and harder
to audit.

### Add fine-grained root-cause categories

Rejected for now. Categories such as `database_timeout` and
`database_pool_exhaustion` would overfit early synthetic cases. The enum should
stay coarse until representative evaluation data justifies expansion.

## Why this matters for Telemetry Investigation Agents

The project needs a defensible boundary between deterministic guarantees and
LLM reasoning. Structured categories improve auditability without overstating
what deterministic code can prove. The generator proposes, validation enforces
structural policy, the critic reviews semantic quality, and evaluation measures
scenario-level behavior.

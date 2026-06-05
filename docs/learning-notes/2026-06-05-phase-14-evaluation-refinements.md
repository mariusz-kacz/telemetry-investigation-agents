# Session: Phase 14 evaluation refinements

## Context

Phase 14 eval runs exposed that tests must measure the workflow's usable
post-review conclusions, not every intermediate hypothesis that survived
validation.

## Agreed Changes

- `EvaluationRunOutput` represents a post-review workflow result, so
  `validation_result`, `review_result`, and `human_review_assessment` are
  required.
- Expected-category scoring considers accepted reviewed hypotheses only.
- Unsupported-claim scoring considers accepted reviewed hypotheses only.
- Raw critique findings do not directly trigger human review. Critique findings
  are converted into deterministic hypothesis review statuses first.
- Low confidence across all validated hypotheses is not a human-review trigger.
  Review routing uses `ReviewedHypothesis` status and dominance policy.
- The generator prompt must prefer `DATABASE_FAILURE` for database/datastore
  operations and DB-specific metrics, instead of generic
  `DOWNSTREAM_DEPENDENCY_FAILURE`.
- Timeout/retry/configuration/deployment/code-causality claims require direct
  evidence for that mechanism.
- Mixed evidence with no dominant cause should produce `UNCERTAIN_ROOT_CAUSE`.
- The critic should treat supported competing explanations as
  `ALTERNATIVE_INTERPRETATION`, not as unsupported causal leaps.
- Retrieval should include incident-window `WARN`/`ERROR`/`CRITICAL` logs for
  the incident service through a `SEVERITY` match reason.
- Telemetry readers should tolerate UTF-8 BOM-prefixed files with `utf-8-sig`.

## Design Rationale

The workflow should not depend on perfect incident wording or on an LLM rescuing
an incomplete evidence package. Query terms are weak seeds. Severity is a
deterministic telemetry signal and can preserve competing causal evidence before
the generator or critic reason over it.

Evaluation should not pass because a blocked or disputed hypothesis happens to
match the expected category. It should pass only when the workflow's accepted
conclusions match the expected behavior.

## Remaining Policy Gap

Accepted `UNCERTAIN_ROOT_CAUSE` should trigger human review, just like accepted
`INSUFFICIENT_EVIDENCE`. This is a deterministic routing rule, not a prompt
quality issue.

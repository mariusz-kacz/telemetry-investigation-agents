# Session: Human-in-the-loop review

## Goal

Learn how human review becomes an explicit, risk-based LangGraph workflow
transition rather than an unconditional pause or a UI concern.

## What I built

- A deterministic human-review assessment policy outside the graph layer.
- Typed human-review assessment and status models.
- An `IncidentImpact` classification used as an escalation trigger.
- Conditional routing that bypasses review for safe investigations and
  interrupts execution when review is required.
- Explicit approved, rejected, and not-required review outcomes.
- A report-ready path that is reached only after approval or when review was
  not required.
- Tests for assessment triggers, model invariants, impact escalation, and
  interrupt/resume behavior.

## LangGraph concept learned

An interrupt is only the pause mechanism. The decision to interrupt belongs to
deterministic workflow policy, and LangGraph conditional edges route from that
policy result.

The review flow separates three concerns:

- assessment: determine whether human review is required;
- gate: interrupt and resume with a human response;
- outcome routing: continue after approval or terminate explicitly after
  rejection.

## Mapping to .NET/C# thinking

This resembles a durable workflow transition more than controller-driven
approval handling. The state contains the review assessment and outcome, while
the graph controls which transition executes next.

The Python design uses small functions, typed Pydantic models, and conditional
edges rather than introducing a review service hierarchy or workflow-command
framework.

## What confused me

The first interrupt gate always required review, which was enough to learn
checkpoint resume behavior but not enough for a real risk-control policy.

It was also important to distinguish report readiness from review status:
`NOT_REQUIRED` does not mean the report is skipped, and `REJECTED` must not
silently become report-ready.

## Tradeoffs noticed

Assessment policy belongs outside graph orchestration because confidence,
evidence quality, critic findings, and incident impact are investigation
policy. The graph should route using the assessment result rather than contain
the policy itself.

Approval and rejection form a coherent first human-review slice. Additional
human actions would introduce materially larger workflow behavior.

Deferred: request-more-evidence routing requires an investigation re-entry loop
and bounded iteration policy. Edit-final-recommendation routing requires a
typed final report/recommendation artifact and audit semantics. Phase 12
demonstrates risk-based approval/rejection human-in-the-loop control only.

## Production concerns

- Escalation reasons must remain auditable and deterministic.
- A high-impact incident can require review even when confidence is high.
- A rejected candidate hypothesis does not by itself require human review when
  a trustworthy accepted hypothesis remains.
- Human-review outcomes must not be represented by loosely typed dictionaries.
- Resume payloads eventually need a typed boundary if reviewer actions grow.

## Tests/evals added

- Human-review assessment trigger tests for confidence, evidence quality,
  critic findings, and incident impact.
- Domain model tests for review-assessment invariants and evidence-reference
  uniqueness.
- Workflow interrupt/resume tests for human review.

## Next step

Complete Phase 12 verification by testing all graph-level routing outcomes,
then review the checkpoint understanding questions before marking the phase
done.

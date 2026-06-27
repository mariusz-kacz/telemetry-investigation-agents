# ADR 0008: Keep semantic evaluation separate from workflow critique

## Status

Proposed

## Context

The investigation workflow already has a semantic critic. That critic runs inside
the LangGraph workflow after deterministic evidence validation. It reviews
validated hypotheses for issues such as contradictions, unsupported causal
leaps, alternative interpretations, and overstated confidence. Its findings are
then mapped by deterministic policy into reviewed hypothesis statuses.

Evaluation has a different job. It should measure whether unsupported causal or
configuration claims still made it through the workflow controls and appeared in
accepted reviewed hypotheses.

If evaluation reused the workflow critic directly, the system would partly grade
itself with the same runtime control that failed to catch the issue. That would
weaken the eval signal and make regressions harder to trust.

## Decision

Keep the evaluation unsupported-claim reviewer separate from the workflow
critic.

The workflow critic:

- runs inside graph execution;
- contributes structured critique findings to graph state;
- participates in deterministic review status policy;
- can affect human-review routing through reviewed hypothesis status.

The unsupported-claim reviewer:

- runs after workflow execution as part of evaluation;
- inspects accepted reviewed hypotheses only;
- scores whether unsupported semantic claims passed the workflow controls;
- must not mutate graph state;
- must not affect workflow routing or human-review decisions.

The evaluator may use similar evidence-boundary rules and prompt guardrails, but
it remains a separate protocol and adapter from the runtime critic.

## Consequences

Evaluation remains an external check on workflow behavior instead of another
runtime policy node.

The scorecard can detect cases where structural validation passed but a semantic
claim was still unsupported by the cited evidence.

The project has two related LLM-assisted review paths, which adds some
conceptual overhead. The distinction must be documented clearly:

- runtime critique controls the investigation workflow;
- post-run semantic evaluation measures whether those controls were sufficient.

## Alternatives considered

One alternative was to reuse the workflow critic inside the evaluator. That
would reduce code and prompt surface area, but it would make the evaluator less
independent from the runtime mechanism being assessed.

Another alternative was to rely only on deterministic citation validation. That
was rejected because valid evidence IDs do not prove that the hypothesis
statement is semantically supported by the cited evidence.

Another alternative was to put unsupported-claim scoring into the graph itself.
That was rejected because evaluation should not become part of normal workflow
routing. Runtime risk control belongs to validation, critique, review policy,
and human review; evaluation measures the result after those controls run.

## Why this matters for Telemetry Investigation Agents

The portfolio claim is not merely that reports contain citations. The stronger
claim is that conclusions are evidence-backed and that unsupported causal claims
are controlled.

The unsupported-claim reviewer gives the evaluation suite a semantic regression
signal for that claim. Keeping it separate from the workflow critic makes the
signal more credible: it checks whether unsupported claims escaped the runtime
controls instead of reusing those controls as the judge.

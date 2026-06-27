# Evaluation Cases

This page contains scenario notes for the current eval/demo cases. For the
scorecard, commands, and provider setup, see [../evaluation.md](../evaluation.md).

## Purpose

The suite verifies whether the workflow can:

- identify clear root causes when evidence is strong;
- correlate evidence across logs, traces, and metrics;
- handle cross-service and dependency failures;
- reduce certainty when evidence conflicts;
- require human review when uncertainty is high;
- return insufficient evidence instead of inventing unsupported causes.

The cases are capability-driven, not just telemetry-pattern-driven. Each case
exists to exercise behavior that matters for evidence-backed incident analysis.

## Case Summary

| Case | Scenario | Expected Category | Human Review | Capability Tested |
|---|---|---|---:|---|
| `checkout-database-timeout` | Checkout failures with consistent database timeout evidence across logs, traces, and metrics. | `database_failure` | No | Clear root-cause identification from consistent evidence. |
| `downstream-dependency-latency` | Checkout latency caused by a downstream shipping-rate dependency while local checkout work remains healthy. | `downstream_dependency_failure` | No | Cross-service evidence correlation. |
| `conflicting-evidence` | Logs, metrics, and traces support competing explanations. | `uncertain_root_cause` | Yes | Confidence calibration and human-review escalation. |
| `insufficient-evidence` | Sparse telemetry confirms symptoms but does not provide enough causal evidence. | `insufficient_evidence` | Yes | Refusal to hallucinate unsupported root causes. |

## Cases

### checkout-database-timeout

This is the strong evidence case. Logs show database timeout symptoms during
checkout processing. Traces show checkout processing dominated by database
spans, and metrics show database-related degradation in the same window.

The expected result is a high-confidence database failure hypothesis. Human
review should not be required because the evidence is consistent across
telemetry sources.

### downstream-dependency-latency

This case validates downstream dependency reasoning. Checkout's local work is
not the main bottleneck, but traces show time spent waiting on
`shipping-rate-service`. Metrics support a dependency latency or timeout trend.

The expected result is a high-confidence downstream dependency hypothesis.
Human review should not be required because the causal path is supported.

### conflicting-evidence

This case checks whether the workflow avoids overstating certainty. Telemetry
supports multiple plausible directions, so no single explanation clearly
dominates.

The expected result is low certainty with human review required. The system
should surface the conflict instead of forcing a neat root cause.

### insufficient-evidence

This case checks weak-evidence behavior. Telemetry confirms checkout symptoms,
but does not provide enough direct evidence to support a concrete cause.

The expected result is human review and an insufficient-evidence outcome. The
system should state what is missing rather than invent a root cause.
# Evaluation Cases

## Purpose

This is a compact MVP evaluation suite for an evidence-based telemetry investigation agent.

The suite verifies whether the system can:

- identify clear root causes when evidence is strong
- correlate evidence across logs, traces, and metrics
- handle cross-service and dependency failures
- reduce confidence when evidence conflicts
- require human review when uncertainty is high
- return insufficient evidence instead of hallucinating

The cases are capability-driven, not just telemetry-pattern-driven. Each case exists to exercise a specific investigation behavior that matters for evidence-backed incident analysis.

## Case Summary

| Case | Scenario | Expected Category | Expected Confidence | Human Review | Capability Tested |
|---|---|---|---|---|---|
| `checkout-database-timeout` | Checkout failures with consistent database timeout evidence across logs, traces, and metrics. | Database degradation / timeout | High | No | Clear root-cause identification from consistent evidence. |
| `downstream-dependency-latency` | Checkout latency caused by waiting on a downstream shipping-rate dependency while local checkout work remains healthy. | Downstream dependency latency | High | No | Cross-service evidence correlation. |
| `conflicting-evidence` | Logs suggest database degradation, metrics suggest shipping-rate-service degradation, and traces do not clearly resolve the conflict. | Conflicting or uncertain cause | Low | Yes | Confidence calibration and human-review escalation. |
| `insufficient-evidence` | Sparse telemetry confirms checkout failures but does not provide enough causal evidence. | Insufficient evidence | Low | Yes | Refusal to hallucinate unsupported root causes. |

## Cases

### checkout-database-timeout

This is the strong evidence case. Logs show `orders-db` latency and timeout symptoms during checkout processing. Traces show checkout processing dominated by database spans, and metrics show database latency and timeout rate increasing in the same window.

The expected result is a high-confidence database timeout hypothesis. Human review should not be required because the evidence is consistent across telemetry sources.

Capability tested:

```text
Clear root-cause identification from consistent evidence.
```

### downstream-dependency-latency

This case validates downstream dependency reasoning. The checkout API's local work remains healthy, but traces show time spent waiting on `shipping-rate-service`. Metrics support a dependency latency or timeout trend rather than a local checkout bottleneck.

The expected result is a high-confidence downstream dependency latency hypothesis. Human review should not be required because the causal path is supported across traces and metrics.

Capability tested:

```text
Cross-service evidence correlation.
```

### conflicting-evidence

This case checks whether the system can avoid overstating certainty. Logs lean toward database degradation, while metrics lean toward `shipping-rate-service` degradation. Traces are mixed or incomplete, so no single explanation clearly dominates.

The expected result is low confidence with human review required. The system should surface the conflict instead of forcing a neat root cause.

Capability tested:

```text
Confidence calibration and human-review escalation.
```

### insufficient-evidence

This case checks weak-evidence behavior. Telemetry is sparse and generic: logs confirm checkout failures but do not explain why, traces are missing or incomplete, and metrics show weak abnormality without a clear causal signal.

The expected result is low confidence with human review required. The system should return insufficient evidence rather than inventing an unsupported root cause.

Capability tested:

```text
Refusal to hallucinate unsupported root causes.
```

## Design Principles

- Runtime incident input must not contain the known root cause.
- Query terms represent weak initial retrieval signals, not the answer.
- Retrieval should preserve incident-window `WARN`/`ERROR`/`CRITICAL` logs even
  when they do not match the initial query terms, so competing causal evidence is
  not hidden by incomplete incident wording.
- Trace IDs should preferably be discovered from retrieved logs rather than hardcoded in incident input.
- Logs should describe symptoms, not conclusions.
- Traces should provide timing and causality.
- Metrics should support trends, not encode answers.
- Cases should be deterministic and easy to explain.
- Evaluation should focus on evidence quality, confidence, and human-review behavior rather than exact prose matching.

# Evaluation

## Purpose

The evaluation layer exists to make the workflow measurable before prompt or
policy tuning. It checks whether the system produces evidence-bound, reviewable
outputs for a small set of synthetic incidents.

The evals do not prove production correctness. They provide a regression suite
for the implemented workflow: retrieval, structured hypotheses, validation,
review routing, citations, and unsupported-claim controls.

## Evaluation Cases

The four eval/demo cases live under `eval_data/`.

| Case | Expected category | Expected review | Behavior verified |
|---|---|---:|---|
| `checkout-database-timeout` | `database_failure` | No | The workflow can identify a clear database failure when logs, traces, and metrics agree. |
| `downstream-dependency-latency` | `downstream_dependency_failure` | No | The workflow can reason across a downstream dependency path. |
| `conflicting-evidence` | `uncertain_root_cause` | Yes | The workflow should avoid forcing a single cause when evidence supports competing explanations. |
| `insufficient-evidence` | `insufficient_evidence` | Yes | The workflow should refuse unsupported concrete root-cause claims. |

Runtime incident files do not contain the known root cause. They provide incident
metadata, a service, an investigation window, and retrieval hints.

## Scorecard Dimensions

Each case is scored across five dimensions:

- expected evidence-source coverage;
- expected accepted hypothesis category;
- expected human-review behavior;
- citation correctness;
- unsupported causal claims.

Category and unsupported-claim checks inspect accepted reviewed hypotheses only.
Blocked or disputed hypotheses are not considered auto-usable workflow
conclusions.

## Behavior Verified By Each Case

`checkout-database-timeout`

Logs show database timeout symptoms, traces show checkout work dominated by
database spans, and metrics show database-related degradation. The expected
result is an accepted `database_failure` hypothesis without human review.

`downstream-dependency-latency`

Checkout work is affected by a downstream shipping-rate service path. The
expected result is an accepted `downstream_dependency_failure` hypothesis without
human review.

`conflicting-evidence`

Telemetry supports more than one plausible explanation. The expected result is
an `uncertain_root_cause` outcome and human review. A forced confident concrete
cause would be a failure.

`insufficient-evidence`

Telemetry confirms symptoms but lacks enough causal evidence. The expected
result is `insufficient_evidence` and human review. A concrete root-cause claim
would be a failure unless directly supported by cited evidence.

## Running Evals

The default offline check is the test suite:

```powershell
uv run pytest
```

The batch eval CLI uses live provider calls for hypothesis generation, semantic
critique, and unsupported-claim review:

```powershell
uv run telemetry-evals --provider azure
```

The default console output is the compact scorecard. To debug the workflow with
structured JSON observability events, opt in explicitly:

```powershell
uv run telemetry-evals --provider azure --show-telemetry
```

Provider-backed evaluation requires:

- configured `.env`;
- Azure OpenAI endpoint;
- hypothesis deployment name;
- evaluation deployment name;
- local identity that works with `DefaultAzureCredential`.

The Azure adapter uses Microsoft Entra ID. API-key authentication is
intentionally out of scope for this project.

Relevant environment variables:

```text
TELEMETRY_AGENTS_AZURE_OPENAI_ENDPOINT
TELEMETRY_AGENTS_AZURE_OPENAI_HYPOTHESIS_DEPLOYMENT_NAME
TELEMETRY_AGENTS_AZURE_OPENAI_EVALUATION_DEPLOYMENT_NAME
TELEMETRY_AGENTS_EVAL_DATA_ROOT
TELEMETRY_AGENTS_TRACING_ENABLED
```

## Output

The CLI prints a compact pass/fail report:

```text
Evaluation summary: 4/4 passed

[PASS] checkout-database-timeout
  evidence sources: PASS
  category: PASS
  human review: PASS
  citation correctness: PASS
  unsupported claims: PASS
```

When a dimension fails, the report prints diagnostic details such as missing
evidence sources, expected vs actual category, human review mismatch, unknown
evidence references, missing-evidence references, or unsupported claims.

The latest captured Azure eval result is stored in
[2026-06-26-azure-eval-report.md](evaluation/2026-06-26-azure-eval-report.md).

## What Failure Means

Evidence-source failure means deterministic retrieval did not collect an
expected telemetry source.

Category failure means the accepted reviewed hypothesis did not match the
expected category.

Human-review failure means the risk policy escalated when it should not have, or
failed to escalate when it should have.

Citation failure means a validated hypothesis had no citations, unknown evidence
references, or references to missing evidence.

Unsupported-claim failure means an accepted reviewed hypothesis made a causal
claim that the evaluation reviewer could not connect to cited evidence.

## Why Evals Matter

LLM prompts are sensitive to small changes. Without evals, tuning one case can
quietly break citation discipline, category behavior, or review routing in
another case.

This project uses evals as a quality gate for AI workflow behavior, not as a
claim that the system is production-ready.

## Current Limits

- Only four synthetic cases are included.
- The semantic unsupported-claim check uses a provider-backed reviewer.
- There is no statistical benchmark or multi-judge aggregation.
- The eval data is intentionally small so each case and score can be inspected
  manually.

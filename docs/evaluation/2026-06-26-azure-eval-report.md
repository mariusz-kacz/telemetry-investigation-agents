# Azure Evaluation Report - 2026-06-26

## Command

```powershell
uv run telemetry-evals --provider azure
```

## Environment

- Provider: Azure OpenAI.
- Hypothesis generator: configured by `TELEMETRY_AGENTS_AZURE_OPENAI_HYPOTHESIS_DEPLOYMENT_NAME`.
- Critic/reviewer: configured by `TELEMETRY_AGENTS_AZURE_OPENAI_EVALUATION_DEPLOYMENT_NAME`.
- Eval data root: `eval_data`.
- Cases: 4 synthetic golden cases.

## Result

```text
Evaluation summary: 4/4 passed

[PASS] checkout-database-timeout
  evidence sources: PASS
  category: PASS
  human review: PASS
  citation correctness: PASS
  unsupported claims: PASS

[PASS] conflicting-evidence
  evidence sources: PASS
  category: PASS
  human review: PASS
  citation correctness: PASS
  unsupported claims: PASS

[PASS] downstream-dependency-latency
  evidence sources: PASS
  category: PASS
  human review: PASS
  citation correctness: PASS
  unsupported claims: PASS

[PASS] insufficient-evidence
  evidence sources: PASS
  category: PASS
  human review: PASS
  citation correctness: PASS
  unsupported claims: PASS
```

## Interpretation

All current synthetic golden cases passed across evidence retrieval,
accepted-category selection, human-review routing, citation correctness, and
unsupported-claim review.

## Caveats

- This is a small synthetic eval suite, not a production benchmark.
- The run uses live model calls, so output can vary across model versions and
  deployments.
- Passing evals do not prove root-cause correctness outside these scenarios.
- No holdout eval set exists yet.

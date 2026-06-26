# Sample Investigation Report - Checkout Database Timeout

## Scenario

- Case: `checkout-database-timeout`
- Incident: `inc-checkout-db-timeout-001`
- Service: `checkout-api`
- Impact: medium
- Human review status: not required

## Final Report

The `orders-db` path experienced elevated query latency and intermittent
timeouts during the incident window. This caused `checkout-api` order-insert
operations to fail or time out, resulting in failed checkout requests.

## Selected Hypothesis

- Hypothesis ID: `hyp-1`
- Category: database failure
- Confidence: 90%

## Supporting Evidence

| Evidence ID | Source | Summary |
|---|---|---|
| `trace-checkout-api-9` | Trace | `INSERT orders` attempt 1 ended with `error` in 1230 ms. |
| `trace-checkout-api-10` | Trace | `INSERT orders` attempt 2 ended with `timeout` in 1250 ms. |
| `log-checkout-api-11` | Log | Checkout request aborted after timeout waiting for `orders-db`. |
| `log-checkout-api-10` | Log | Request timed out while waiting for `orders-db`. |
| `metric-checkout-api-6` | Metric | `orders_db_query_p95_latency_ms` was 920 ms at 09:56 UTC. |
| `metric-checkout-api-10` | Metric | `orders_db_query_p95_latency_ms` was 1850 ms at 10:00 UTC. |
| `metric-checkout-api-14` | Metric | `orders_db_query_p95_latency_ms` was 2480 ms at 10:04 UTC. |
| `metric-checkout-api-7` | Metric | `orders_db_timeout_rate_percent` was 1.2% at 09:56 UTC. |
| `metric-checkout-api-11` | Metric | `orders_db_timeout_rate_percent` was 5.8% at 10:00 UTC. |
| `metric-checkout-api-15` | Metric | `orders_db_timeout_rate_percent` was 11.6% at 10:04 UTC. |

## Interpretation

The strongest evidence is the combination of failed database write spans,
checkout timeout logs, and rising database-specific latency and timeout metrics.
Together, these support a database-path failure rather than a generic downstream
dependency issue.
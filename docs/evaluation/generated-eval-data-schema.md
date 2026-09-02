# Generated Evaluation Data Schema

## Purpose

Use this specification when adding synthetic evaluation datasets. Each dataset
must be isolated by case and compatible with the deterministic telemetry parsers
and `LocalFileTelemetryReader`.

Do not include evaluation-only labels in runtime incident input. In particular,
do not put the known root cause in `incident.json`.

## Directory Layout

```text
eval_data/
    cases/
        <case-id>.json
    <case-id>/
        incident.json
        logs/
            <service>.log
        traces/
            <service>.jsonl
        metrics/
            <service>.jsonl
```

Telemetry files may be omitted intentionally when a source is unavailable. The
retrieval layer represents an omitted file as missing evidence.

Use the same primary `<service>` value in `incident.json`, telemetry filenames,
logs, and metrics. Trace records may identify downstream services when they
share a correlated trace ID.

## Runtime Incident Input

File: `eval_data/<case-id>/incident.json`

```json
{
  "incident_id": "inc-checkout-db-timeout-001",
  "title": "Checkout API latency and database timeout errors",
  "service": "checkout-api",
  "impact": "medium",
  "reported_at": "2026-05-11T10:05:00Z",
  "investigation_window": {
    "start": "2026-05-11T09:40:00Z",
    "end": "2026-05-11T10:10:00Z"
  },
  "retrieval": {
    "query_terms": ["timeout", "database"],
    "trace_id": "trace-001"
  }
}
```

Required fields:

| Field | Rule |
|---|---|
| `incident_id` | Non-empty string, unique across cases. |
| `title` | Non-empty incident description. |
| `service` | Non-empty primary service name. |
| `impact` | One of `low`, `medium`, `high`. |
| `reported_at` | ISO 8601 timestamp with timezone. |
| `investigation_window.start` | ISO 8601 timestamp with timezone. |
| `investigation_window.end` | ISO 8601 timestamp with timezone, not earlier than `start`. |
| `retrieval.query_terms` | Concrete terms expected to occur in relevant log messages. |
| `retrieval.trace_id` | Optional trace ID. Trace evidence can also be retrieved from trace IDs discovered in logs. |

## Log File

File: `eval_data/<case-id>/logs/<service>.log`

Format:

```text
<timestamp> <level> <service> trace_id=<id> <message>
```

Rules:

- Every non-empty line must contain at least five whitespace-separated tokens.
- `timestamp`, `level`, and `service` are the first three tokens.
- Every line must include non-empty `trace_id=<id>`.
- Relevant records must fall inside the investigation window.
- Query-matched log records may seed one-hop trace ID expansion.
- Incident-window `WARN`, `ERROR`, and `CRITICAL` logs may be selected by
  severity.

## Trace File

File: `eval_data/<case-id>/traces/<service>.jsonl`

Format: JSON Lines, one span per line.

```json
{"timestamp":"2026-05-11T10:01:13Z","trace_id":"trace-001","span_id":"span-001","service":"checkout-api","operation":"POST /checkout","duration_ms":2420,"status":"error"}
```

Required fields:

| Field | Rule |
|---|---|
| `timestamp` | ISO 8601 timestamp with timezone. |
| `trace_id` | Non-empty string. |
| `span_id` | Non-empty string. |
| `service` | Non-empty emitting service name. |
| `operation` | Non-empty operation name. |
| `duration_ms` | Integer greater than or equal to zero. |
| `status` | Non-empty string such as `ok` or `error`. |

## Metric File

File: `eval_data/<case-id>/metrics/<service>.jsonl`

Format: JSON Lines, one sample per line.

```json
{"timestamp":"2026-05-11T10:01:00Z","service":"checkout-api","metric_name":"p95_latency_ms","value":2400}
```

Required fields:

| Field | Rule |
|---|---|
| `timestamp` | ISO 8601 timestamp with timezone. |
| `service` | Non-empty string matching the primary service when the sample should be retrieved. |
| `metric_name` | Non-empty string. |
| `value` | JSON number, not a string or boolean. |

Relevant samples must fall inside the investigation window.

## Golden Evaluation Contract

File: `eval_data/cases/<case-id>.json`

```json
{
  "case_id": "checkout-database-timeout",
  "incident_file": "checkout-database-timeout/incident.json",
  "expected_category": "database_failure",
  "expected_evidence_sources": [
    {
      "source": "log",
      "source_file": "eval_data/checkout-database-timeout/logs/checkout-api.log"
    },
    {
      "source": "trace",
      "source_file": "eval_data/checkout-database-timeout/traces/checkout-api.jsonl"
    },
    {
      "source": "metric",
      "source_file": "eval_data/checkout-database-timeout/metrics/checkout-api.jsonl"
    }
  ],
  "expected_human_review_required": false
}
```

Rules:

- `case_id` must match the `eval_data/<case-id>/` folder name.
- `incident_file` is relative to `eval_data/`.
- `expected_category` must be a valid `HypothesisCategory`.
- `expected_evidence_sources` should contain telemetry sources genuinely needed
  to explain the scenario.
- `expected_human_review_required` describes expected workflow escalation.
- Do not store expected model prose. Evaluation checks structure, citations,
  review behavior, and unsupported claims.

## Cross-File Consistency Rules

- Use one coherent UTC timeline per case.
- Place relevant telemetry inside the investigation window.
- Use stable service names across incident input and filenames.
- Reuse trace IDs across logs and trace spans when trace correlation matters.
- Include only enough records to express the scenario.
- Include ordinary or weakly relevant records when needed to verify filtering.
- Avoid leaking known root causes into runtime incident input.

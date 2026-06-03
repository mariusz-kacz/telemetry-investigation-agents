# Generated Evaluation Data Schema

## Purpose

Use this specification when generating synthetic evaluation datasets with an
LLM. Each dataset must be isolated by case and remain compatible with the
existing deterministic telemetry parsers and `LocalFileTelemetryReader`.

Do not include evaluation-only labels in runtime incident input. In particular,
do not put the known root cause in `incident.json`.

## Directory Layout

Each generated case uses this layout:

```text
eval_data/
    <case-id>/
        incident.json
        logs/
            <service>.log
        traces/
            <service>.jsonl
        metrics/
            <service>.jsonl

evals/
    cases/
        <case-id>.json
```

Telemetry files may be omitted intentionally when a source is unavailable. The
retrieval layer represents an omitted file as missing evidence.

Use the same primary `<service>` value in `incident.json`, telemetry filenames,
logs, and metrics. Trace records may identify downstream emitting services when
they share a correlated trace ID.

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
| `reported_at` | ISO 8601 timestamp with timezone, preferably UTC `Z`. |
| `investigation_window.start` | ISO 8601 timestamp with timezone. |
| `investigation_window.end` | ISO 8601 timestamp with timezone, not earlier than `start`. |
| `retrieval.query_terms` | List of concrete terms expected to occur in relevant log messages. |
| `retrieval.trace_id` | Optional non-empty string. When omitted, trace evidence can still be retrieved from trace IDs discovered in query-matched logs. |

The future eval loader will translate these fields into the existing domain
`Incident` and `EvidenceRetrievalRequest` models. This loader does not exist yet.

## Log File

File: `eval_data/<case-id>/logs/<service>.log`

Format: one plain-text record per line.

```text
<timestamp> <level> <service> trace_id=<id> <message>
```

Example:

```text
2026-05-11T10:01:13Z ERROR checkout-api trace_id=trace-001 DatabaseTimeoutException while calling orders-db
```

Rules:

- Every non-empty line must contain at least five whitespace-separated tokens.
- `timestamp`, `level`, and `service` are the first three tokens.
- Every line must include non-empty `trace_id=<id>`.
- The remaining non-metadata tokens form the message.
- Exception names should end with `Exception` when exception extraction matters.
- Relevant records must fall inside the investigation window.
- Include a retrieval query term or matching trace ID when a record should become
  evidence.
- Query-matched log records may seed one-hop trace ID expansion. Companion logs
  sharing a discovered trace ID may become evidence even when they do not contain
  the query term.

## Trace File

File: `eval_data/<case-id>/traces/<service>.jsonl`

Format: JSON Lines. Each line is one JSON object.

```json
{"timestamp":"2026-05-11T10:01:13Z","trace_id":"trace-001","span_id":"span-001","service":"checkout-api","operation":"POST /checkout","duration_ms":2420,"status":"error"}
```

Required fields:

| Field | Rule |
|---|---|
| `timestamp` | ISO 8601 timestamp with timezone. |
| `trace_id` | Non-empty string. |
| `span_id` | Non-empty string, unique within the trace. |
| `service` | Non-empty emitting service name. A correlated trace may include the primary service and downstream dependency services. |
| `operation` | Non-empty operation name. |
| `duration_ms` | Integer greater than or equal to zero. |
| `status` | Non-empty string such as `ok` or `error`. |

Trace retrieval uses `retrieval.trace_id` when present and also uses trace IDs
discovered from query-matched log evidence.

## Metric File

File: `eval_data/<case-id>/metrics/<service>.jsonl`

Format: JSON Lines. Each line is one JSON object.

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

File: `evals/cases/<case-id>.json`

```json
{
  "case_id": "checkout-database-timeout",
  "incident_file": "eval_data/checkout-database-timeout/incident.json",
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
- `incident_file` must point to the case-scoped runtime incident input.
- `expected_category` must be a valid `HypothesisCategory` value.
- `expected_evidence_sources` must contain only telemetry sources genuinely
  required to explain the scenario.
- Each expected source path must exist unless the case intentionally tests
  missing evidence behavior.
- `expected_human_review_required` describes the expected workflow escalation.
- Do not store unsupported-claim blacklists or expected model prose. Semantic
  unsupported claims are evaluated independently by the reviewer.

## Cross-File Consistency Rules

- Use one coherent UTC timeline per case.
- Place relevant telemetry inside the investigation window.
- Use stable service names across incident input and filenames. Trace records may
  identify downstream emitting services when they share the correlated trace ID.
- Reuse `trace_id` across logs and trace spans when trace correlation matters.
- When relying on query-only retrieval, include at least one query-matched seed
  log with the trace ID that should be expanded.
- Add only enough records to express the scenario, usually three to six records
  per telemetry file.
- Include ordinary or weakly relevant records when needed to prove filtering.
- Avoid leaking the known root cause into runtime incident input.

## Insufficient-Evidence Case

Do not force this case into the current golden contract yet. A correct workflow
may return no accepted hypothesis, while the current category score expects at
least one accepted hypothesis matching `expected_category`.

Before generating this case, decide whether the golden schema should support an
explicit expectation such as:

```json
{
  "expected_outcome": "insufficient_evidence"
}
```

That schema decision belongs to the evaluation framework, not the data
generator.

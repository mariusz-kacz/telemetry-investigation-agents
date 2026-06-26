# API

## Purpose

The FastAPI layer exposes a focused portfolio demo interface. It is not a
general incident ingestion API. The API accepts predefined demo case IDs, starts
or resumes workflow runs, and returns UI-oriented response DTOs.

The API does not expose raw LangGraph state.

## Base URLs

Backend:

```text
http://127.0.0.1:8000
```

Versioned API prefix:

```text
/api/v1
```

## Endpoints

### Health

```http
GET /health
```

Response:

```json
{"status":"ok"}
```

### List Demo Cases

```http
GET /api/v1/demo-cases
```

Response:

```json
[
  "checkout-database-timeout",
  "conflicting-evidence",
  "downstream-dependency-latency",
  "insufficient-evidence"
]
```

Demo cases are discovered from `TELEMETRY_AGENTS_DATA_ROOT/cases`.

### Start Investigation

```http
POST /api/v1/investigations
```

Request:

```json
{
  "case_id": "checkout-database-timeout"
}
```

Response status:

```text
201 Created
```

The API loads the case incident, creates a run registry record, retrieves
evidence, invokes the graph, persists checkpoints, and returns the current run
state.

### List Investigation Runs

```http
GET /api/v1/investigations
```

Response:

```json
{
  "runs": [
    {
      "run_id": "run_...",
      "case_id": "checkout-database-timeout",
      "demo_provider": "fake",
      "incident_id": "inc-checkout-db-timeout-001",
      "status": "completed"
    }
  ]
}
```

Statuses are returned in lowercase from the API. Stored registry statuses are:

- `PENDING`
- `AWAITING_REVIEW`
- `COMPLETED`
- `REJECTED`

### Read Investigation

```http
GET /api/v1/investigations/{run_id}
```

Returns the latest checkpoint-backed workflow state mapped to the public
response DTO.

### Submit Human Review

```http
POST /api/v1/investigations/{run_id}/review
```

Request:

```json
{
  "approved": true
}
```

Response status:

```text
202 Accepted
```

Only runs in `awaiting_review` can be resumed through this endpoint. Approval
continues to final report construction. Rejection marks the run as rejected.

## Investigation Response Shape

Representative response:

```json
{
  "run_id": "run_...",
  "case_id": "checkout-database-timeout",
  "demo_provider": "fake",
  "status": "completed",
  "incident": {
    "id": "inc-checkout-db-timeout-001",
    "title": "Checkout API latency and database timeout errors",
    "service": "checkout-api",
    "impact": "medium"
  },
  "top_hypothesis": {
    "id": "local-hyp-database-timeout",
    "statement": "Checkout failures are most consistent with database timeout behavior observed in the retrieved log, trace, and metric evidence.",
    "category": "database_failure",
    "confidence": 0.88,
    "review_status": "accepted",
    "evidence_ids": ["log-checkout-api-12"]
  },
  "hypotheses": [],
  "evidence": [],
  "human_review_required": false,
  "review_reasons": [],
  "warnings": [],
  "report_ready": true,
  "final_report": null
}
```

Actual evidence and hypothesis arrays depend on the selected case and provider.

## Error Behavior

The API maps application failures into HTTP responses:

- missing case or data file: `400 Bad Request`;
- invalid request or workflow value error: `422 Unprocessable Entity`;
- run not found: `404 Not Found`;
- checkpoint state unavailable or incomplete: `409 Conflict`.

## Frontend Relationship

The React UI calls these endpoints through `frontend/src/api.ts`. In local dev,
Vite proxies `/api` to `http://127.0.0.1:8000`, so the frontend can use relative
API paths.

The frontend can optionally use `VITE_API_BASE_URL`, but the current local setup
does not require it.

# Telemetry Investigation Agents

Telemetry Investigation Agents is a learning-oriented portfolio project for building a production-minded LangGraph investigation workflow.

The target system will analyze synthetic enterprise telemetry such as logs, traces, metrics, and incident tickets. It will produce cited investigation reports with suspected root causes, supporting and contradicting evidence, confidence levels, explicit uncertainty, and recommended next actions.

The project is intentionally incremental. The current checkpoint includes LangGraph state, telemetry adapters, deterministic parsing and retrieval, bounded LLM-backed hypothesis generation, deterministic hypothesis validation, persistence, human review, evaluations, observability, and a small FastAPI demo boundary.

## Engineering Thesis

LangGraph should orchestrate workflow state and transitions. Deterministic parsing, validation, telemetry access, and domain behavior should remain in normal Python modules that are easy to test without an LLM.

This mirrors the useful part of enterprise layering without copying its ceremony: the graph is the orchestration layer, domain models stay framework-independent, telemetry modules own parsing and local readers, and investigation modules hold retrieval, matching, generation adapter boundaries, and deterministic validation policy.

## FastAPI Demo API

Start the local API in the default deterministic demo mode:

```powershell
uv run uvicorn telemetry_agents.api.app:app --reload
```

The default `TELEMETRY_AGENTS_DEMO_PROVIDER=fake` mode runs the real retrieval,
validation, graph, checkpointing, API, and UI path without making Azure OpenAI
calls.

To run the same demo with live Azure OpenAI calls, set:

```powershell
$env:TELEMETRY_AGENTS_DEMO_PROVIDER="azure"
uv run uvicorn telemetry_agents.api.app:app --reload
```

List available demo cases:

```powershell
curl http://127.0.0.1:8000/api/v1/demo-cases
```

Start an investigation for a predefined demo case:

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/investigations `
  -H "Content-Type: application/json" `
  -d '{"case_id":"checkout-database-timeout"}'
```

Read the latest investigation result by run ID:

```powershell
curl http://127.0.0.1:8000/api/v1/investigations/<run_id>
```

Submit a human review decision for a run that is awaiting review:

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/investigations/<run_id>/review `
  -H "Content-Type: application/json" `
  -d '{"approved":true}'
```

The API is intentionally synchronous for this checkpoint. Background execution,
polling workers, WebSockets, auth, and arbitrary incident ingestion are later
hardening concerns.

## Live Evaluation

The batch evaluation command uses live Azure OpenAI model calls and requires
Azure configuration from `.env`:

```powershell
uv run telemetry-evals --provider azure
```

Run `uv run pytest` for the default offline verification path.

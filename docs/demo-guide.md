# Demo Guide

## Goal

Use this guide to explain the project in about five minutes. The demo should
show that the project is a controlled AI workflow, not a generic chatbot over
logs.

## Recommended Setup

Start the backend:

```powershell
uv run uvicorn telemetry_agents.api.app:app --reload
```

Start the frontend:

```powershell
cd frontend
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

Use the default deterministic provider for a stable demo unless you explicitly
want to show live provider-backed behavior.

## Five-Minute Walkthrough

### 1. Open The UI

Say:

> This is a portfolio demo UI over a LangGraph investigation workflow. The UI is
> intentionally thin: it calls FastAPI DTOs and does not know about graph state.

Point out the case selector, run history, workflow stages, and empty outcome
area.

### 2. Select A Clear Case First

Start with:

```text
checkout-database-timeout
```

Say:

> I usually start with the strong-evidence case because it shows the happy path:
> deterministic retrieval finds log, trace, and metric evidence, the LLM boundary
> proposes a structured hypothesis, and deterministic validation decides whether
> the citations are usable.

Click **Run Investigation**.

### 3. Show Evidence Citations

After the run completes, show the evidence list.

Say:

> Each evidence item has an ID, source, citation, strength, and summary. The LLM
> is not asked to inspect arbitrary raw telemetry. It receives this curated,
> cited evidence context.

Emphasize that evidence IDs are the link between source telemetry and
hypotheses.

### 4. Show The Hypothesis

Show the top hypothesis and the hypothesis review panel.

Say:

> Generated hypotheses are candidate state. They only become usable after the
> validator checks evidence references, rejects unknown or missing evidence IDs,
> and caps confidence when the evidence is not strong enough.

For the strong database case, the expected result is an accepted database-related
hypothesis without human review.

### 5. Show Human Review Behavior

Run one of these next:

```text
conflicting-evidence
insufficient-evidence
```

Say:

> These cases are more important than the happy path. They demonstrate that the
> workflow can stop short of a confident answer. Human review is triggered by
> deterministic policy when evidence is weak, conflicting, disputed, blocked, or
> insufficient.

If the run is awaiting review, show the approve/reject buttons.

Say:

> The review gate uses LangGraph checkpointing and interrupt/resume. The workflow
> persists state, waits for a decision, then resumes to either finalize or reject
> the report.

### 6. Show Run History

Click a previous run.

Say:

> The run history comes from an application-owned SQLite registry. It is separate
> from LangGraph checkpoints, which store workflow state. The UI reloads past run
> outcomes through the API without rerunning the investigation.

### 7. Explain Evaluation

Say:

> The same synthetic cases are used for evaluation. The scorecard checks evidence
> source coverage, expected category, expected human-review behavior, citation
> correctness, and unsupported causal claims. That keeps prompt and policy
> changes from being judged by anecdote.

## Suggested Case Order

1. `checkout-database-timeout`
2. `conflicting-evidence`
3. `insufficient-evidence`
4. `downstream-dependency-latency`

This order shows the happy path first, then demonstrates uncertainty and review
controls.

## What To Emphasize

- LangGraph is used for stateful orchestration, branching, checkpointing, and
  human review resume.
- Deterministic code owns evidence handling and policy.
- The LLM is bounded to structured generation and semantic critique.
- Final reports cite evidence from accepted hypotheses.
- Human review is part of the workflow design, not just a UI button.
- Synthetic telemetry is a deliberate simplification for portfolio scope.

## Honest Limitations To Mention

- The telemetry is synthetic and local.
- The UI is a demo surface, not a full observability product.
- There is no real ingestion, auth, deployment, or production monitoring.
- The eval suite is intentionally small.
- The default local provider is deterministic for repeatable demos.

## Thirty-Second Resource Manager Summary

This is a Python/LangGraph portfolio project that demonstrates controlled
enterprise AI workflow engineering. It investigates synthetic telemetry incidents
using deterministic evidence retrieval and validation, bounded LLM hypothesis
generation, evidence citations, evaluation cases, traceability, and human review
gates. The emphasis is not a production monitoring product, but the engineering
patterns needed to make AI-assisted workflows auditable and safe enough for
enterprise discussion.

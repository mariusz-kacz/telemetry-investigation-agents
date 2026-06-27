# ADR 0004: Use LangGraph checkpointing for human-review resume

## Status

Proposed

## Context

Telemetry investigations can run synchronously when no human review is needed.
Checkpointing is not required merely because the workflow has multiple steps.

The need appears when the graph reaches a human-review gate. The current
workflow can pause at `report_review_gate` with a LangGraph `interrupt(...)`,
return a review packet to the API/UI, and later resume with
`Command(resume=...)`.

That pause/resume path needs durable workflow state keyed by LangGraph
`thread_id`. Without checkpointing, a process restart or a later API review
request would lose the graph position and the intermediate state needed to
continue safely.

The API/UI also need to read the latest workflow result after a run has started.
That state belongs to LangGraph checkpoints, while application-owned run
metadata, such as case ID, incident ID, provider, and status, belongs in a
separate run registry.

## Decision

Use LangGraph's checkpointer for resumable workflow execution state.

Use a small project-owned SQL table for application run metadata:

```sql
CREATE TABLE investigation_runs (
    run_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    incident_id TEXT NOT NULL,
    status TEXT NOT NULL,
    demo_provider TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

The application may use the same value for `investigation_runs.run_id` and
LangGraph's `thread_id`, but they remain separate concepts:

- `run_id` is the application-facing investigation run identity.
- `thread_id` is the LangGraph checkpoint lookup key.

Graph builders accept an optional checkpointer at compile time. They should not
create SQLite connections directly. SQLite-specific wiring belongs in the
composition/checkpointing module.

## Consequences

The graph can be interrupted for human review, resumed with the same
`thread_id`, and inspected through LangGraph checkpoint APIs.

The application can query its own run registry without depending on LangGraph's
internal checkpoint schema.

The project now has two persistence responsibilities:

- framework-owned checkpoint tables,
- application-owned run metadata tables.

This split adds a small amount of coordination, but it avoids reimplementing
LangGraph's checkpoint format and keeps application queries stable.

## Alternatives considered

One alternative was to avoid checkpointing and keep the first demo fully
synchronous. That would be simpler, but it would make human-review resume an
application-level re-run problem rather than a real continuation of graph state.

Another alternative was to use `InMemorySaver`. That is simpler and useful for
tests, but it does not survive process restarts and is not enough for a durable
API/UI review flow.

Another alternative was to design a custom checkpoint schema for graph state.
That was rejected because it would duplicate LangGraph's persistence semantics
and could diverge from what LangGraph expects.

Another alternative was to store only LangGraph checkpoints and skip the custom
run registry. That was rejected because application features such as listing
runs, showing incident/run mappings, and later tracking review status should
not query framework-owned checkpoint tables directly.

## Why this matters for Telemetry Investigation Agents

Human review is a risk-control step, not just a UI confirmation. When the graph
pauses for review, the system must preserve the exact state being reviewed and
resume from that state after approval or rejection.

Checkpointing gives LangGraph responsibility for resumable workflow state. The
run registry gives the application a stable way to list, read, and update demo
investigation status without querying framework-owned checkpoint tables.

# ADR 0004: Investigation workflows need checkpointing

## Status

Proposed

## Context

Telemetry investigations are multi-step workflows. A run may retrieve evidence,
generate hypotheses, validate evidence references, run an LLM critic, pause for
human review, and later resume.

If graph state only lives in process memory, a restart or pause loses the
workflow position and intermediate state. That is not acceptable for an
investigation system where conclusions must be inspectable and recoverable.

The project also needs application-owned run metadata, such as which incident a
run belongs to. That metadata is different from LangGraph's internal checkpoint
state.

## Decision

Use LangGraph's checkpointer for workflow execution state.

Use a small project-owned SQL table for application run metadata:

```sql
CREATE TABLE investigation_runs (
    run_id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL
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

The graph can be resumed or inspected through LangGraph checkpoint APIs.

The application can query its own run registry without depending on LangGraph's
internal checkpoint schema.

The project now has two persistence responsibilities:

- framework-owned checkpoint tables,
- application-owned run metadata tables.

This split adds a small amount of coordination, but it avoids reimplementing
LangGraph's checkpoint format and keeps application queries stable.

## Alternatives considered

One alternative was to use `InMemorySaver`. That is simpler and useful for
tests, but it does not survive process restarts.

Another alternative was to design a custom checkpoint schema for graph state.
That was rejected because it would duplicate LangGraph's persistence semantics
and could diverge from what LangGraph expects.

Another alternative was to store only LangGraph checkpoints and skip the custom
run registry. That was rejected because application features such as listing
runs, showing incident/run mappings, and later tracking review status should
not query framework-owned checkpoint tables directly.

## Why this matters for Telemetry Investigation Agents

Incident investigations need recoverable state, explicit run identity, and
inspectable progress. Checkpointing lets the graph resume safely, while the run
registry gives the application a stable way to track investigations.

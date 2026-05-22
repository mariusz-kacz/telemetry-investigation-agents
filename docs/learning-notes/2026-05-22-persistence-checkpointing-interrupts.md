# Session: Persistence, checkpointing, and interrupts

## Goal

Learn how LangGraph persists workflow state, how application run metadata differs
from checkpoint state, and how interrupts pause and resume execution.

## What I built

- A SQLite-backed LangGraph checkpointer factory.
- An application-owned `investigation_runs` registry table.
- A main `investigation_workflow` graph that accepts a checkpointer at compile
  time.
- Checkpointing tests that inspect stored graph state by `thread_id`.
- A simulated resume test using a new graph instance and the same SQLite
  checkpoint database.
- A report review gate that interrupts execution and resumes with a decision.
- A small marker node that records review completion after resume.
- ADR 0004 explaining why investigation workflows need checkpointing.

## LangGraph concept learned

`thread_id` is the checkpoint lookup key LangGraph uses to persist, inspect, and
resume workflow state.

A checkpointer must be configured when the graph is compiled. Without a
checkpointer, interrupts cannot reliably pause and resume because LangGraph has
nowhere durable to store the paused execution state.

`interrupt(...)` pauses graph execution and returns a payload to the caller.
Execution resumes later with `Command(resume=...)` using the same `thread_id`.

## Mapping to .NET/C# thinking

LangGraph checkpointing is closer to durable orchestration state than a normal
repository. The framework owns the checkpoint format.

The application-owned `run_id` is similar to a business-facing operation ID. It
can use the same value as LangGraph's `thread_id`, but it is not the same
concept.

The graph builder accepting a checkpointer is a lightweight Python form of
dependency injection. No DI container is needed; the composition root passes the
concrete dependency into the graph builder.

## What confused me

The boundary between the application run registry and LangGraph checkpoint
tables was initially unclear.

It was also tempting to let the checkpointing module compile the workflow graph,
but that coupled infrastructure to workflow composition. The cleaner boundary is
that the graph module builds the graph and infrastructure creates persistence
adapters.

## Tradeoffs noticed

SQLite checkpointing is more realistic than `InMemorySaver` because it survives
new graph instances and process restarts. `InMemorySaver` is still useful for
focused interrupt tests where durable storage is not the learning target.

The run registry is intentionally small. It should hold application metadata,
not LangGraph's internal checkpoint state.

Interrupts are now present, but full human-review policy is deferred to the next
phase.

## Production concerns

- LangGraph checkpoint tables should be treated as framework-owned internals.
- Application features should query application-owned tables, not checkpoint
  internals.
- Re-running from scratch is not the same as resuming from checkpointed state,
  especially when LLM calls or external tools are involved.
- Interrupt payloads should be structured so external callers can render or act
  on them predictably.

## Tests/evals added

- Run registry tests.
- SQLite checkpointer factory test.
- Investigation workflow checkpointing integration tests.
- State inspection and simulated resume tests.
- Report review interrupt/resume test.

## Next step

Move to Phase 12: human-in-the-loop review. Build on the existing interrupt
mechanism by adding explicit review decision models, review routing conditions,
and rejection/request-more-evidence paths.

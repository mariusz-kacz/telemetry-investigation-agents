# Session: LangGraph fundamentals

## Goal

Learn the smallest LangGraph workflow model: typed state, node functions, fixed edges, graph compilation, and graph invocation.

## What I built

Built a minimal investigation graph that accepts an incident title, normalizes it, and creates an initial investigation summary.

The graph shape is:

```text
START
  -> normalize_incident_title
  -> create_initial_summary
  -> END
```

## LangGraph concept learned

`StateGraph` is a builder for a workflow that moves through explicit steps while carrying shared state.

The state is the workflow context. In this phase it is represented by `MinimalInvestigationState`, a `TypedDict` with:

- `incident_title`
- `normalized_title`
- `investigation_summary`

Nodes are plain Python functions. Each node receives the current state and returns a partial state update. The normalization node returns `normalized_title`; the summary node returns `investigation_summary`.

Edges define control flow. `START` and `END` are special markers for the graph entry and exit. The graph must be compiled before it can be invoked.

## Mapping to .NET/C# thinking

The graph state is similar to a workflow context DTO in a .NET workflow engine or Durable Functions orchestration.

Each node is similar to a small application-service handler or MediatR handler that receives a request/context and returns a result. The difference is that LangGraph keeps the workflow state explicit and lets the graph decide which handler runs next.

Fixed edges are similar to deterministic state-machine transitions. In this phase there is no branching, so the graph behaves like a simple pipeline, but the control flow is still declared explicitly.

`StateGraph(...)` is the workflow definition builder. `compile()` produces the executable workflow. This is similar to configuring an ASP.NET application builder before running the built app.

## What confused me

TODO: Add your own note here. Suggested topics:

- Why `builder.compile()` must be returned instead of returning the builder.
- Why PyCharm can show type warnings even when `pytest` and `mypy` pass.
- Whether returning partial state updates feels natural compared with mutating an object in C#.

## Tradeoffs noticed

A plain Python function pipeline would be simpler for this exact example. LangGraph becomes useful when the workflow needs branching, resumability, interrupts, tool calls, human review, or durable state.

The tradeoff is extra ceremony: state schema, node registration, edge registration, and compilation. The benefit is that workflow structure becomes explicit and testable instead of being hidden inside nested function calls.

## Production concerns

This graph is intentionally minimal and not production-grade yet.

Before this pattern becomes production-ready, the project will need stronger state modeling, explicit domain models, error handling, observability, checkpointing, evaluation cases, and clear boundaries between deterministic code and LLM-assisted reasoning.

The current graph also assumes `incident_title` exists. Later phases should make input validation and failure behavior explicit.

## Tests/evals added

Added a unit test that invokes the compiled graph with:

```text
"  Checkout API latency spike  "
```

The test verifies that:

- the original `incident_title` remains in state,
- `normalized_title` is trimmed and lowercased,
- `investigation_summary` is created from the normalized title.

Verification run:

```powershell
uv run pytest
uv run mypy src
uv run ruff check
```

All checks passed after returning the compiled graph from `build_minimal_investigation_graph`.

## Next step

After Phase 2 review is complete, move to Phase 3: typed state and domain modeling.

# Session: Agent observability is not optional

## Goal

Make the LangGraph investigation workflow inspectable from structured logs and
trace spans.

## What I built

Phase 15 added observability across the workflow:

- structured JSON events through `telemetry_agents.observability`;
- stdout logging configuration for local and future FastAPI entrypoints;
- opt-in local OpenTelemetry console tracing;
- graph node lifecycle events and spans;
- evidence retrieval events and span;
- workflow LLM adapter events and spans for hypothesis generation and critique;
- decision events for validation, critic review, hypothesis review, human-review
  routing, and eval scoring.

## LangGraph concept learned

LangGraph nodes are natural observability boundaries. Each node consumes graph
state, performs one workflow step, and returns a state update. Wrapping nodes in
`observe_graph_node(...)` makes the workflow timeline visible without spreading
logging calls through every node implementation.

The root execution is represented as:

```text
investigation.run
  evidence.retrieval
  graph.node.*
    llm.call.*
```

## Mapping to .NET/C# thinking

The closest .NET analogy is structured logging and tracing around application
service and adapter boundaries. The Python implementation stays lighter:

- module-level helpers instead of framework-heavy logging services;
- explicit context managers for timed LLM calls;
- logger/tracer configuration at entrypoints;
- no broad root logger mutation.

## What confused me

It was easy to mix evaluation judge calls with production workflow calls. The
unsupported-claim reviewer uses an LLM, but it is part of the evaluation
framework, not the investigation workflow. It should not appear as
`llm.call.*` in the production workflow trace.

## Tradeoffs noticed

Structured logs and spans are complementary:

- logs record facts, counts, statuses, and decisions;
- spans show parent/child execution flow and latency.

The project keeps both because neither replaces the other.

Tracing is opt-in through `TELEMETRY_AGENTS_TRACING=true` because console span
output is intentionally verbose.

## Production concerns

Agentic workflows need observability because failures and bad outcomes are not
limited to exceptions:

- model calls can be slow or unavailable;
- model output can be structurally valid but semantically risky;
- critic fallback changes risk posture;
- weak or missing evidence affects confidence;
- human-review routing must be explainable.

The observability boundary intentionally avoids sensitive content:

- no prompts;
- no raw model responses;
- no evidence payloads;
- no hypothesis statements;
- no full graph state.

## Tests/evals added

Focused tests now verify:

- graph workflow event timeline;
- LLM adapter event shape for hypothesis generation and critique;
- stdout logging configuration remains compatible with the eval CLI;
- evaluation judge calls do not emit production workflow LLM events.

## Next step

Use `docs/observability.md` as the reference for reading structured logs and
local spans from an eval run.

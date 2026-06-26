# Observability

## Purpose

The investigation workflow uses two complementary observability signals:

- structured JSON logs for audit/debug facts;
- OpenTelemetry spans for execution timeline and nesting.

Structured logs answer what happened and what decision was made. Spans answer
where time was spent and which operation was nested inside which parent
operation.

## Runtime Configuration

Structured observability logging is configured by the FastAPI app lifecycle. The
eval CLI keeps normal scorecard output readable by default and prints structured
JSON events only when `--show-telemetry` is passed:

```text
telemetry_agents.observability
```

```powershell
uv run telemetry-evals --provider azure --show-telemetry
```

Local OpenTelemetry console tracing is opt-in:

```powershell
$env:TELEMETRY_AGENTS_TRACING_ENABLED="true"
uv run telemetry-evals --provider azure --show-telemetry
```

The same setting is read when running the FastAPI backend. For the backend,
structured JSON logs are enabled by app startup. For eval CLI runs, structured
JSON logs are opt-in so the pass/fail report remains readable.

## Structured Event Logging

Structured events are emitted with `emit_event(...)`. Each event is one JSON
object written as one line.

Example:

```json
{"event":"graph.node.completed","run_id":"1b1c1266-7006-4809-bbfc-8e9b6088797e","incident_id":"inc-checkout-db-timeout-001","node_name":"hypothesis_generation","duration_ms":20745.047}
```

Important correlation fields:

- `run_id`: one investigation or eval execution.
- `incident_id`: incident being investigated.
- `case_id`: eval case, when the event belongs to evaluation.
- `node_name`: LangGraph node boundary.
- `operation`: adapter operation such as `hypothesis_generation`.

## Event Taxonomy

Graph lifecycle events:

- `graph.node.started`
- `graph.node.completed`
- `graph.node.failed`

Evidence retrieval events:

- `evidence.retrieval.completed`
- `telemetry.source.unavailable`

Workflow LLM adapter events:

- `llm.call.started`
- `llm.call.completed`
- `llm.call.failed`

Decision events:

- `hypothesis.validation.confidence_adjusted`
- `hypothesis.validation.rejected`
- `hypothesis.critic.completed`
- `hypothesis.critic.fallback`
- `hypothesis.review.completed`
- `human_review.routing_decided`
- `eval.case.scored`

Evaluation judge calls, such as unsupported-claim review, are not emitted as
workflow `llm.call.*` events. They are evaluation infrastructure, not production
investigation workflow steps.

## Span Model

With `TELEMETRY_AGENTS_TRACING_ENABLED=true`, a local eval case maps to one logical
trace:

```text
investigation.run
  evidence.retrieval
  graph.node.hypothesis_generation
    llm.call.hypothesis_generation
  graph.node.hypothesis_validation
  graph.node.hypothesis_critic
    llm.call.hypothesis_critic
  graph.node.hypothesis_review
  graph.node.human_review_assessment
  graph.node.human_review_not_required_marker
  graph.node.report_ready_marker
```

If human review is required, the routing path includes the review gate and
approval/rejection marker nodes instead of the not-required marker.

## Reading A Run

To investigate one run, filter by `run_id`.

Example retrieval event:

```json
{"event":"evidence.retrieval.completed","run_id":"1b1c1266-7006-4809-bbfc-8e9b6088797e","incident_id":"inc-checkout-db-timeout-001","log_count":6,"trace_count":8,"metric_count":20,"strong_count":6,"medium_count":28,"weak_count":0,"missing_count":0}
```

This tells us retrieval found log, trace, and metric evidence and no source was
missing.

Example LLM event:

```json
{"event":"llm.call.completed","run_id":"1b1c1266-7006-4809-bbfc-8e9b6088797e","incident_id":"inc-checkout-db-timeout-001","provider":"azure_openai","operation":"hypothesis_generation","deployment_name":"hypothesis-model","output_schema":"InvestigationHypothesisResponse","hypothesis_count":2,"duration_ms":20744.296}
```

This tells us the hypothesis generation adapter called Azure OpenAI, returned
two structured hypotheses, and spent about 20.7 seconds in the provider call.

Example decision events:

```json
{"event":"hypothesis.critic.completed","run_id":"1b1c1266-7006-4809-bbfc-8e9b6088797e","incident_id":"inc-checkout-db-timeout-001","finding_count":0,"finding_types":[],"affected_hypothesis_ids":[],"evidence_reference_count":0}
```

```json
{"event":"human_review.routing_decided","run_id":"1b1c1266-7006-4809-bbfc-8e9b6088797e","incident_id":"inc-checkout-db-timeout-001","human_review_required":false,"reason":null}
```

Together, the event stream explains that the critic found no semantic issues and
human review was not required.

## Reading Spans

Console span output is verbose, but the important fields are:

- `name`: operation name, such as `graph.node.hypothesis_generation`.
- `trace_id`: shared across all spans in one investigation trace.
- `span_id`: current operation ID.
- `parent_id`: parent operation ID.
- `attributes`: safe metadata such as `run_id`, `incident_id`, `node_name`, and
  LLM provider metadata.

Example span relationship:

```text
trace_id: 0x45c1372840c46c0966cc7a056a95210b

investigation.run
  span_id: 0xf1e2f85e5e530ef9

graph.node.hypothesis_generation
  span_id: 0x74c511bb5291aa0e
  parent_id: 0xf1e2f85e5e530ef9

llm.call.hypothesis_generation
  span_id: 0x4f412d69c1abd254
  parent_id: 0x74c511bb5291aa0e
```

This proves the LLM generation call occurred inside the hypothesis-generation
graph node, which occurred inside the investigation run.

## Privacy Boundary

Observability must not include:

- prompts;
- raw LLM responses;
- full evidence payloads;
- evidence summaries;
- hypothesis statements;
- critic or reviewer reasons;
- full graph state.

Safe fields include:

- IDs;
- counts;
- node names;
- operation names;
- provider/deployment/schema metadata;
- durations;
- error types;
- decision statuses.

## Current Boundaries

Structured events and spans are emitted at these boundaries:

- `retrieve_evidence(...)` emits retrieval events and an `evidence.retrieval`
  span.
- `observe_graph_node(...)` emits graph node lifecycle events and
  `graph.node.*` spans.
- `observe_llm_call(...)` emits workflow LLM events and `llm.call.*` spans for
  the hypothesis generator and critic adapters.
- `build_graph_case_runner(...)` creates the root `investigation.run` span for
  eval case execution.

The unsupported-claim reviewer is intentionally excluded from workflow LLM
observability because it is an evaluation judge call, not part of the
investigation graph.

## Debugging Checklist

For a given `run_id`, the event stream and spans should answer:

- Which evidence sources were retrieved?
- Which graph nodes ran?
- Which node failed, if any?
- Which LLM calls occurred inside which graph nodes?
- How long did each node and LLM call take?
- Were hypotheses rejected or confidence-adjusted?
- Did the critic complete or fall back?
- How many hypotheses were accepted, disputed, or blocked?
- Was human review required?
- Which eval dimensions passed or failed?

# ADR 0006: Bounded Trace ID Expansion For Evidence Retrieval

## Status

Accepted

## Context

The first evidence retrieval implementation matched each source independently
against filters supplied in the incident retrieval request.

That worked when the incident already contained a precise `trace_id`, but it was
too limited when only query terms were available. A query such as `timeout` could
find relevant log lines, but retrieval did not reuse the `trace_id` values from
those logs to collect companion logs or trace spans.

The project also originally carried a separate `correlation_id` field in
synthetic logs and incident retrieval input. In the current data model it did not
represent a distinct business identifier. It duplicated `trace_id` without
adding a scenario where one business request maps to several traces or async
workflows.

Keeping both identifiers made the retrieval contract harder to explain and made
tests more ceremonial than useful.

## Decision

Evidence retrieval will use trace-only correlation for the current synthetic
telemetry model.

Structured log records contain:

```text
timestamp level service trace_id=<id> message
```

They do not contain `correlation_id`.

Retrieval uses bounded two-pass log matching:

```text
parsed logs
    -> pass 1: query-matched seed logs discover trace IDs
    -> pass 2: logs match query terms, request trace ID, or discovered trace IDs
    -> trace matching: spans match request trace ID or discovered trace IDs
```

Expansion is intentionally one hop:

- query-matched logs may discover trace IDs;
- logs sharing those discovered trace IDs may be included as companion evidence;
- trace spans sharing those discovered trace IDs may be included;
- companion logs do not discover additional trace IDs.

Matching provenance is preserved:

- `QUERY_TERM` means the log matched request query terms;
- `REQUEST_TRACE_ID` means the record matched a trace ID supplied by incident
  input;
- `DISCOVERED_TRACE_ID` means the record matched a trace ID discovered from a
  query-matched seed log.

Trace spans also preserve request-vs-discovered provenance so citation reasons
and scoring can distinguish direct incident input from one-hop inferred
correlation.

## Consequences

Positive consequences:

- Retrieval works when only query terms are supplied.
- Trace evidence can be discovered from logs without requiring the incident file
  to know the trace ID upfront.
- Companion logs are retrieved deterministically from trace IDs instead of asking
  an LLM to infer related telemetry.
- Selection reasons remain auditable because request trace IDs and discovered
  trace IDs are separate match reasons.
- Removing `correlation_id` simplifies the synthetic data contract.

Tradeoffs:

- Query terms become more important because they define seed logs for expansion.
- A noisy query can discover noisy trace IDs, so scoring must treat discovered
  evidence as lower provenance than explicit request trace evidence.
- The current trace-only model does not represent business-level correlation
  across multiple traces.
- Async or retry-heavy scenarios may need a separate business correlation field
  later, but only when the data model demonstrates that need.

## Alternatives considered

### Require incident input to provide a trace ID

Rejected. This made retrieval too brittle. A useful incident input may only know
symptoms such as `timeout`, `database`, or a downstream service name.

### Recursively expand from every newly matched log

Rejected. Recursive expansion can grow evidence sets in surprising ways and
pull in loosely related telemetry. One-hop expansion is easier to reason about
and test.

### Keep `correlation_id` as an optional field

Rejected for now. An unused optional field creates misleading API surface. A
business correlation ID should be reintroduced only when a concrete scenario
needs to connect multiple traces or asynchronous work that `trace_id` cannot
represent.

### Use vector search or LLM retrieval for related evidence

Rejected for this phase. The retrieval lesson is deterministic, cited evidence
selection. Probabilistic retrieval can be evaluated later after the deterministic
baseline is measurable.

## Why this matters for Telemetry Investigation Agents

The system needs evidence retrieval that is useful without being opaque.

Bounded trace ID expansion improves recall while keeping deterministic control:
the LLM still receives structured cited evidence, and the retrieval layer can
explain exactly why each item was selected.

# Current Architecture

## Scope

This document describes the architecture after Phase 7: evidence retrieval and citations.

The system is still intentionally incomplete. It has deterministic telemetry parsing, matching, scoring, and cited evidence retrieval. It does not yet include LLM hypothesis generation, validation, persistence, interrupts, evaluation runners, observability, or an external API.

## Module Boundaries

### `telemetry`

Owns normalized telemetry record shapes and parsing for the local synthetic data format.

Examples:

- `ParsedLogRecord`
- `ParsedTraceSpan`
- `ParsedMetricSample`
- `parse_log_line`
- `parse_trace_span_json`
- `parse_metric_sample_json`

This package is source-neutral within the project. It is not responsible for file access or evidence ranking.

### `infrastructure`

Owns local file access and source-location preservation.

The current reader reads synthetic telemetry files and returns parsed records with:

- source file,
- line number,
- parsed telemetry record.

Infrastructure may depend on telemetry parsing. Application matching should not depend on file paths or file IO.

### `application`

Owns deterministic investigation logic.

Current responsibilities:

- log matching,
- trace span matching,
- metric sample matching,
- log evidence classification,
- shared evidence strength vocabulary,
- retrieval of cited evidence.

Matching functions accept already-read source records. They do not open files and do not manufacture missing evidence.

Evidence retrieval is the application orchestration boundary. It calls infrastructure readers, invokes matchers, creates `TelemetryEvidence`, attaches citation metadata, and represents missing evidence explicitly.

### `domain`

Owns core investigation models that should not depend on LangGraph or infrastructure.

Examples:

- `Incident`
- `TelemetryEvidence`
- `EvidenceSource`
- `InvestigationHypothesis`
- `InvestigationReport`

Domain models are intentionally small at this stage.

### `graph`

Owns LangGraph state and early workflow experiments.

The graph layer should orchestrate application functions. It should not parse telemetry, read files directly, or contain source-specific matching rules.

## Dependency Direction

Current intended dependency shape:

```text
infrastructure -> telemetry
application -> telemetry
application -> domain
application -> infrastructure at retrieval orchestration boundary
graph -> application
graph -> domain/state models
```

Avoid these directions:

```text
telemetry -> application
domain -> application
domain -> infrastructure
matching modules -> file readers
graph nodes -> raw file parsing
```

## Evidence Retrieval Flow

```text
local sample files
    -> LocalFileTelemetryReader
    -> parsed source records with file/line metadata
    -> source-specific matching
    -> source-specific evidence construction
    -> RetrievedEvidence with citation metadata
```

Current source-specific matching:

- logs: service, time window, query terms, correlation ID, trace ID;
- traces: service, time window, exact trace ID;
- metrics: service and time window.

Matching returns matched records only. Retrieval decides whether to create actual evidence or explicit missing evidence.

## Citation Contract

Every retrieved evidence item should preserve:

- source file,
- line number or record ID,
- timestamp when available,
- service/component,
- reason it was selected.

The purpose is to make future hypotheses and final reports inspectable. Later LLM-generated hypotheses should cite evidence IDs, not raw telemetry or unsupported claims.

## Evidence Strength

Evidence strength is intentionally conservative.

- Exact trace ID evidence can be strong.
- Log evidence can be strong, medium, or weak depending on match reasons.
- Metric evidence is currently medium because service + time-window matching alone is not a strong relevance signal.
- Missing evidence is represented explicitly.

Metric evidence may become weak unless later phases add anomaly detection, baselines, metric-name intent, or threshold-based relevance.

## Current Deliberate Limits

- No LLM hypothesis generation yet.
- No vector search.
- No deployment-event evidence in the MVP.
- No persistence or checkpointing yet.
- No human review routing yet.
- No API or CLI boundary yet.
- No production observability yet.

These are later learning phases, not accidental omissions.

## Open Questions

- Should metric evidence remain `MEDIUM`, or should it be downgraded to `WEAK` until anomaly logic exists?
- Should evidence retrieval helpers remain in one module, or split into source-specific modules if the file grows?
- What exact evidence contract should Phase 8 hypothesis generation consume?
- Should missing evidence be included in prompts, or only in validator/reporting context?

# Current Architecture

## Scope

This document describes the architecture after Phase 9: evidence validation.

The system is still intentionally incomplete. It has deterministic telemetry parsing, matching, scoring, cited evidence retrieval, bounded hypothesis generation, and deterministic hypothesis validation. It does not yet include the LLM critic, persistence, interrupts, evaluation runners, observability, or an external API.

## Module Boundaries

### `telemetry`

Owns normalized telemetry record shapes, parsing, and local telemetry readers for
the synthetic data format.

Examples:

- `ParsedLogRecord`
- `ParsedTraceSpan`
- `ParsedMetricSample`
- `parse_log_line`
- `parse_trace_span_json`
- `parse_metric_sample_json`
- `LocalFileTelemetryReader`

The current reader reads synthetic telemetry files and returns parsed records with:

- source file,
- line number,
- parsed telemetry record.

Readers may depend on telemetry parsing. Investigation matching should not open
files or parse raw lines directly.

### `investigation`

Owns investigation application logic, including deterministic evidence processing and small LLM adapter boundaries.

Current responsibilities:

- log matching,
- trace span matching,
- metric sample matching,
- log evidence classification,
- shared evidence strength vocabulary,
- retrieval of cited evidence,
- bounded hypothesis generation through an adapter protocol,
- deterministic hypothesis validation.

Matching functions accept already-read source records. They do not open files and do not manufacture missing evidence.

Evidence retrieval is the deterministic investigation boundary for telemetry. It calls telemetry readers, invokes matchers, creates `TelemetryEvidence`, attaches citation metadata, and represents missing evidence explicitly.

Hypothesis generation is the LLM boundary. It calls a `HypothesisGenerator` adapter and returns typed candidate `InvestigationHypothesis` objects. These raw generated hypotheses are untrusted candidate state.

Hypothesis validation is the deterministic trust boundary for hypotheses. It checks evidence references, rejects unsupported or missing-evidence support, caps confidence based on evidence strength, and records audit details in `HypothesisValidationResult`.

### `domain`

Owns core investigation models that should not depend on LangGraph or telemetry readers.

Examples:

- `Incident`
- `TelemetryEvidence`
- `EvidenceSource`
- `InvestigationHypothesis`
- `HypothesisValidationResult`
- `RejectedHypothesis`
- `ConfidenceAdjustment`
- `InvestigationReport`

Domain models are intentionally small at this stage.

### `graph`

Owns LangGraph state and early workflow experiments.

The graph layer should orchestrate investigation functions. It should not parse telemetry, read files directly, contain source-specific matching rules, or hide evidence-policy decisions inside graph nodes.

## Dependency Direction

Current intended dependency shape:

```text
telemetry -> shared
investigation -> telemetry
investigation -> domain
investigation -> shared
graph -> investigation
graph -> domain/state models
```

Avoid these directions:

```text
telemetry -> investigation
domain -> investigation
domain -> telemetry readers
matching modules -> file readers
graph nodes -> raw file parsing
downstream nodes -> raw generated hypotheses as trusted output
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

The purpose is to make generated hypotheses and final reports inspectable. LLM-generated hypotheses should cite evidence IDs, not raw telemetry or unsupported claims. The validator decides whether those cited IDs are usable support.

## Hypothesis Generation And Validation Flow

```text
RetrievedEvidence with citation metadata
    -> HypothesisGenerator adapter
    -> candidate InvestigationHypothesis objects
    -> HypothesisValidatorNode
    -> HypothesisValidationResult
```

Generation and validation have separate responsibilities:

- generation produces typed candidate hypotheses from bounded incident and evidence context;
- validation decides whether candidates are evidence-usable;
- downstream nodes should trust `validation_result`, not raw `hypotheses`.

The validator owns these deterministic policies:

- every accepted hypothesis must have supporting evidence IDs;
- cited evidence IDs must exist in retrieved evidence;
- missing evidence cannot be used as support;
- confidence is capped according to supporting evidence strength;
- confidence changes and rejections are recorded as structured audit data.

The validator intentionally does not perform broad semantic contradiction detection. That belongs to the later LLM critic phase.

## Evidence Strength

Evidence strength is intentionally conservative.

- Exact trace ID evidence can be strong.
- Log evidence can be strong, medium, or weak depending on match reasons.
- Metric evidence is currently medium because service + time-window matching alone is not a strong relevance signal.
- Missing evidence is represented explicitly.

Metric evidence may become weak unless later phases add anomaly detection, baselines, metric-name intent, or threshold-based relevance.

## Current Deliberate Limits

- No vector search.
- No deployment-event evidence in the MVP.
- No LLM critic for semantic review yet.
- No persistence or checkpointing yet.
- No human review routing yet.
- No API or CLI boundary yet.
- No production observability yet.

These are later learning phases, not accidental omissions.

## Open Questions

- Should metric evidence remain `MEDIUM`, or should it be downgraded to `WEAK` until anomaly logic exists?
- Should evidence retrieval helpers remain in one module, or split into source-specific modules if the file grows?
- Should graph state eventually rename raw `hypotheses` to `candidate_hypotheses` to make trust boundaries clearer?
- Should missing evidence be included in prompts, or only in validator/reporting context?

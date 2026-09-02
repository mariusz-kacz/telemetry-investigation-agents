# ADR 0002: Deterministic Evidence Retrieval Before LLM Reasoning

## Status

Accepted

## Context

The system will eventually generate root-cause hypotheses with LLM assistance. Before that happens, the workflow needs reliable evidence retrieval with citations.

Raw telemetry files are not an appropriate direct input contract for hypothesis generation. If an LLM is asked to inspect raw logs, traces, or metrics directly, it can blur parsing, filtering, ranking, and reasoning into one opaque step. That makes the system harder to test and increases the risk of unsupported claims.

Phase 7 introduced deterministic retrieval for logs, trace spans, and metric samples. Each retrieved item carries citation metadata:

- source file,
- line number or record ID,
- timestamp,
- service/component,
- reason it was selected.

It also represents missing evidence explicitly instead of treating either an empty match or an absent telemetry source file as an exceptional failure.

## Decision

Evidence retrieval, source-specific matching, citation assembly, evidence strength assignment, and missing-evidence representation will be deterministic investigation logic.

LLM-based hypothesis generation must consume structured retrieved evidence, not raw telemetry files.

The current boundary is:

```text
local telemetry files
    -> telemetry readers
    -> parsed telemetry records with source location
    -> investigation matching
    -> RetrievedEvidence with citation metadata
    -> later LLM hypothesis generation
```

Matching functions return matched records only. Evidence retrieval decides whether to create actual evidence or explicit missing evidence. A missing source file is translated at this application boundary into `MISSING` evidence for that source.

Evidence retrieved from logs, traces, and metrics is merged and ranked by descending relevance score before downstream consumers see it. The source assembly order is not a ranking policy.

## Consequences

Positive consequences:

- Evidence retrieval is testable without an LLM.
- Citation correctness can be verified before hypothesis generation exists.
- Later prompts can be smaller and more controlled.
- Final reports can cite evidence IDs backed by inspectable source metadata.
- Missing evidence can reduce confidence instead of causing hallucinated certainty.
- Absent local telemetry files produce explicit missing-source evidence rather than terminating retrieval.
- Cross-source ranking can be regression-tested independently of fixture file order.

Tradeoffs:

- More deterministic code is required before the first LLM feature.
- Retrieval quality depends on explicit matching and scoring rules.
- Some relevance decisions are conservative until richer logic exists.
- The LLM receives a curated evidence set, so poor retrieval can limit hypothesis quality.

## Alternatives considered

### Let the LLM inspect raw telemetry

Rejected. This would make parsing, filtering, citation extraction, and reasoning difficult to test independently. It also creates a higher risk of unsupported claims.

### Use vector retrieval immediately

Rejected for now. Vector search may become useful later, but Phase 7 needs simple deterministic retrieval first so citation behavior and missing-evidence semantics are clear.

### Keep retrieval inside graph nodes

Rejected. LangGraph should orchestrate workflow state and transitions. Source-specific matching and evidence construction are ordinary deterministic application logic and should remain testable outside graph execution.

## Why this matters for Telemetry Investigation Agents

The implementation uses an auditable AI workflow rather than a chatbot over logs.

This decision creates the evidence contract that later phases must respect: hypotheses and reports should be grounded in retrieved evidence with citations. LLM reasoning starts after deterministic evidence retrieval, not before it.

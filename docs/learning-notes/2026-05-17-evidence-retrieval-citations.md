# Session: Evidence retrieval and citations

## Goal

Build deterministic evidence retrieval before hypothesis generation.

## What I built

Retrieved log, trace, and metric evidence from local synthetic telemetry. Each returned item preserves source file, line number, timestamp, service, and a reason it was selected.

## LangGraph concept learned

This phase stayed outside LangGraph nodes intentionally. The learning target was deterministic retrieval logic that a later graph node can call.

## Mapping to .NET/C# thinking

File readers are infrastructure adapters. Matching and evidence assembly are application logic. Python protocols and simple module functions kept this boundary without interface-heavy ceremony.

## What confused me

The distinction between matching and retrieval mattered: matching returns records, while retrieval decides whether to produce evidence or explicit missing evidence.

## Tradeoffs noticed

Metric samples matched only by service and time window are weaker than trace ID or correlation ID evidence, so they should not be treated as strong evidence.

## Production concerns

Evidence must remain inspectable. Later hypotheses and reports should cite evidence IDs backed by file, line, timestamp, and selection reason metadata.

## Tests/evals added

Unit tests cover log, trace, and metric matching. Retrieval tests verify source coverage, citation metadata, trace citations, metric citations, ranking, and missing evidence behavior.

## Next step

Start bounded hypothesis generation only after confirming the evidence contract is stable.

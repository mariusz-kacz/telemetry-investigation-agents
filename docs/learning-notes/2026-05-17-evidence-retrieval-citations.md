# Session: Evidence retrieval and citations

## Goal

Build deterministic evidence retrieval before hypothesis generation.

## What I built

Retrieved log, trace, and metric evidence from local synthetic telemetry. Each returned item preserves source file, line number, timestamp, service, and a reason it was selected.

Retrieval now treats an absent log, trace, or metric source file as explicit `MISSING` evidence instead of allowing `FileNotFoundError` to escape. After evidence from all available sources is assembled, it is sorted by descending relevance score so source read order does not masquerade as ranking.

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

Follow-up regression coverage verifies that:

- retrieval returns `MISSING` log, trace, and metric evidence when source files are absent;
- merged evidence is ranked across telemetry sources rather than returned in log/trace/metric assembly order.

On 2026-05-26, `.\.venv\Scripts\python.exe -m pytest tests\test_evidence_retrieval.py -q` completed with `7 passed`.

## Next step

Start bounded hypothesis generation only after confirming the evidence contract is stable.

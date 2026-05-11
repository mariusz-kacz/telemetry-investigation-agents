# Session: Tool Abstraction and Adapters

## Goal

Understand how telemetry tools should be represented as explicit adapter boundaries instead of mixing file access, parsing, and graph orchestration together.

## What I built

Created local-file telemetry tools for synthetic investigation data:

- `LogSearchTool`
- `TraceLookupTool`
- `MetricWindowTool`
- `DeploymentEventTool`

Each tool has a `Protocol` contract and a local-file implementation that reads from `sample_data`.

The adapters return typed `TelemetryEvidence` objects with citation metadata so later graph nodes can reason over evidence without knowing where it came from.

## LangGraph concept learned

A LangGraph node and a tool are different responsibilities.

A node belongs to orchestration. It receives graph state, decides what workflow step is happening, and returns state updates.

A tool belongs to an external boundary. It retrieves or performs something outside the graph's core workflow logic, such as reading logs, looking up traces, querying metrics, or checking deployment history.

Keeping these separate prevents graph nodes from becoming infrastructure scripts.

## Mapping to .NET/C# thinking

Python `Protocol` is similar to a C# interface, but it is structural rather than nominal.

In C#, a class explicitly implements an interface:

```csharp
public interface ILogSearchTool
{
    IReadOnlyList<TelemetryEvidence> Search(string service, string query);
}
```

In Python, an object satisfies a `Protocol` if it has the expected methods with compatible signatures. This makes the graph depend on behavior instead of a concrete implementation.

The local-file adapters map to infrastructure implementations, similar to classes like `FileLogSearchClient`, `ElasticLogSearchClient`, or `ApplicationInsightsTraceReader` behind an application port.

## What confused me

Type annotations do not create runtime objects. Annotating a list as `list[TelemetryEvidence]` does not prevent appending dictionaries. The adapter must explicitly construct `TelemetryEvidence` models.

## Tradeoffs noticed

The adapters currently use simple deterministic filtering:

- log query matching uses case-insensitive substring matching,
- trace lookup filters by `trace_id` and service,
- metric and deployment windows compare ISO-8601 UTC timestamp strings,
- malformed JSON raises the native `json.JSONDecodeError`.

This is intentionally simple for Phase 5. A custom exception hierarchy and parsed timestamp handling would be premature here.

## Production concerns

In a production system, these adapters would need clearer error contracts, parsed timestamps, schema validation for every JSONL record, observability around tool latency/failures, and possibly retry behavior for remote systems.

The current local-file adapters are enough to prove the boundary and keep tests independent of LLMs.

## Tests/evals added

Added tests proving:

- tools return typed `TelemetryEvidence`,
- citations include local source paths,
- missing data raises `FileNotFoundError`,
- malformed JSON raises `json.JSONDecodeError`,
- adapters can be tested without LangGraph or an LLM.

## Next step

Move to Phase 6: deterministic telemetry parsing. The next learning target is to replace lightweight adapter parsing with explicit parsers for logs, traces, metrics, and deployment events.

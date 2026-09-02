# Repository maintenance guidance

## Working context

Before changing system behavior, read `README.md`, `docs/architecture.md`,
`docs/agent-responsibilities.md`, `docs/ai-workflow-design.md`, and the relevant
ADRs under `docs/adr/`.

Update tests and documentation whenever behavior or contracts change. Do not
broaden this bounded implementation into a production observability platform
without an explicit requirement.

## Architecture invariants

- Deterministic Python owns evidence retrieval, evidence IDs, scoring, citation
  validation, confidence policy, review routing, report assembly, persistence
  boundaries, API DTOs, and evaluation scoring.
- LLM calls are bounded to structured hypothesis generation and semantic
  critique. Treat all model output as untrusted candidate state.
- LangGraph owns orchestration, typed workflow state, checkpointing, conditional
  routing, interrupts, and resume behavior.
- Do not move deterministic evidence handling or approval policy into prompts or
  model decisions.
- Keep graph nodes thin. Put testable behavior in ordinary application
  functions.
- Preserve provider boundaries so offline tests do not require a live model.

## Python design

Prefer simple, explicit, testable, idiomatic Python over C# architecture
translated into Python.

- Prefer a module-level function when it is clearer than a class.
- Use `Protocol` only for a meaningful substitutable boundary.
- Avoid unnecessary abstractions, class hierarchies, factories, and enterprise
  boilerplate.
- Use exceptions, iterators, context managers, dataclasses, `pathlib`, pytest,
  and typing idiomatically where they improve clarity.

## Review quality bar

Review both behavior and maintainability. Explicitly check for:

- unclear names such as `item`, `data`, `result`, `obj`, or `temp` when a domain
  name would be clearer;
- tuple or list indexing where destructuring or a small named model would
  improve readability;
- clever comprehensions or control flow that are difficult to audit;
- missing negative tests and edge cases;
- tests that pass for the wrong reason;
- unnecessary abstractions or C#-style ceremony;
- duplicated logic that should be extracted only when the shared concept is
  meaningful.

Include a short `Maintainability` section in every code review, even when there
are no issues.

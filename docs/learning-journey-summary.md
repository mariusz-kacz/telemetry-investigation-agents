# Learning Journey Summary

> **Historical development material:** This document records how the repository
> was developed. It is not normative system documentation and is not part of
> the recommended initial review path. See `README.md` and the current technical
> documents under `docs/` for the implemented system.

This document compresses the session-by-session learning notes into a shorter
historical summary. The original files in `docs/learning-notes/` remain as an
archive.

## What This Learning Journey Was For

The project started as a LangGraph learning path, but the real goal was broader:
learn how to build an AI-assisted workflow that behaves like maintainable
software rather than a chatbot wrapped around telemetry.

The final system investigates synthetic incidents by retrieving logs, traces,
metrics, and incident context; generating candidate root-cause hypotheses;
validating those hypotheses against cited evidence; applying semantic critique;
escalating to human review when risk remains; and producing a cited report.

The most important lesson was that LangGraph is useful when workflow state,
branching, persistence, interrupts, and review gates need to be explicit. It is
not valuable just because a project uses an LLM.

## Core LangGraph Lessons

The first useful mental model was simple:

```text
state + nodes + edges = explicit workflow
```

State is the workflow context. Nodes are ordinary Python functions that receive
state and return partial state updates. Edges define which node runs next. A
compiled graph turns that declaration into an executable workflow.

For a two-step example, a plain Python pipeline would be simpler than
LangGraph. LangGraph starts to pay for itself when the workflow needs conditional
routing, retry or fallback behavior, checkpoints, interrupts, human review, or
inspection of intermediate state.

The project gradually moved from fixed edges to conditional routing. The key
design rule was that routing should be deterministic when possible. A rule-based
router is easier to test, explain, and reproduce than an LLM router. LLM-based
routing may be useful later, but only when deterministic inputs are insufficient.

The later checkpointing and interrupt work made the framework choice clearer.
`thread_id` became the durable lookup key for persisted graph state. A graph
compiled with a checkpointer can pause with `interrupt(...)` and resume later
with `Command(resume=...)`. That is materially different from rerunning a
function from scratch, especially once the workflow includes LLM calls or
external tools.

## Deterministic Code Owns Trust

The strongest architectural lesson was that the LLM should not own trust.

Deterministic Python owns the parts that must be auditable:

- parsing local telemetry;
- filtering by time window, severity, service, and trace ID;
- preserving evidence IDs and citations;
- ranking evidence by explicit relevance signals;
- rejecting unknown or missing evidence references;
- capping confidence when evidence is weak;
- deciding when human review is required;
- scoring evaluations.

The LLM is bounded to two jobs:

- propose structured candidate hypotheses from supplied evidence;
- critique validated hypotheses for semantic risks.

Generated hypotheses are candidate state, not conclusions. A candidate becomes
usable only after deterministic validation confirms that it cites known,
non-missing evidence and obeys confidence policy.

This separation avoids a common failure mode in AI workflow projects: asking the
model to both invent an answer and decide whether its answer is trustworthy.

## Evidence Before Hypotheses

Evidence retrieval came before hypothesis generation on purpose. The project
first built local telemetry adapters and deterministic retrieval logic for logs,
traces, metrics, and deployment-style evidence.

Each evidence item needed enough metadata to be inspected later:

- evidence ID;
- source type;
- source file and line or record identifier;
- timestamp;
- service or component;
- selection reason;
- evidence strength.

Missing source files are represented as explicit missing evidence instead of
escaping as unhandled file errors. Weak metric evidence is not treated like
strong trace or error-log evidence. Ranking is explicit so source read order does
not accidentally become evidence priority.

The lesson was that retrieval is not just "find some text for the model." In a
reliable investigation workflow, retrieval creates the evidence contract that
every later step must respect.

## Generation, Validation, And Critique Are Different Jobs

The project split hypothesis handling into three distinct steps.

First, the generator proposes candidate hypotheses. It uses a small protocol so
tests can use a fake generator and production can use an Azure OpenAI adapter.
The graph node remains thin: read graph state, build a request, call the
generator, write hypotheses back to state.

Second, the validator applies deterministic evidence policy. It rejects
hypotheses with no supporting evidence, unknown evidence IDs, or missing
evidence used as support. It allows weak or medium evidence only with confidence
limits and records adjustment reasons. The validator creates an audit trail for
reports, evals, observability, and human review.

Third, the critic reviews validated hypotheses for semantic risks such as
contradictions, unsupported causal leaps, alternative interpretations, or
overstated confidence. Critic output is still untrusted. It must cite known
hypothesis and evidence IDs, and unsafe critic output fails loudly.

The critic does not mutate validated hypotheses. It produces findings. A
deterministic review policy then maps those findings to reviewed hypothesis
statuses such as accepted, disputed, or blocked. This preserves a clean boundary:
confidence remains an evidence-support signal, while review status represents
whether a hypothesis is safe to use automatically.

## Human Review Is Workflow Policy

Human review is not just a UI button. It is a risk-control transition in the
graph.

The review flow ended up with three separate concerns:

- assessment: decide whether review is required;
- gate: interrupt the graph and wait for a reviewer decision;
- outcome routing: continue after approval or terminate after rejection.

The assessment policy is deterministic and lives outside graph orchestration.
The graph routes based on that assessment. This keeps policy testable and avoids
hiding business decisions inside edge wiring.

Review can be triggered by high incident impact, weak or missing evidence, no
validated hypothesis, an accepted uncertain or insufficient-evidence outcome,
blocked or disputed top hypotheses, close competing alternatives, warnings, or
conflicting explanations without a dominant accepted hypothesis.

The important distinction was that `human_review_required` means policy required
review. It does not mean the run is still resumable. The UI enables approve or
reject only while the backend status is actually awaiting review.

## Persistence Boundaries Matter

Checkpointing introduced an important boundary:

```text
LangGraph checkpoints != application run registry
```

LangGraph owns checkpoint tables and checkpoint state. Application features
should not query those internals directly. The project uses a small
application-owned run registry for business-facing metadata such as run IDs,
case IDs, statuses, and history.

This distinction also influenced the API and frontend. The React UI does not
read checkpoints or know LangGraph exists. It consumes FastAPI DTOs. The API
delegates to an application service. The service composes retrieval, graph
execution, checkpointing, and registry updates.

That boundary keeps the public contract stable even if the graph internals
change.

## Evaluation Before Prompt Optimization

Evaluation was added before prompt tuning. That forced the project to define
what "good" means instead of manually judging individual model responses.

The scorecard checks deterministic dimensions:

- expected hypothesis category;
- expected evidence-source coverage;
- citation correctness;
- expected human-review behavior.

It also includes a semantic unsupported-claim review that runs after workflow
execution. This reviewer is separate from the workflow critic and does not
influence graph state.

A key refinement was that evals should inspect accepted reviewed hypotheses
only. A blocked or disputed hypothesis should not make an expected-category
score pass, because it is not an auto-usable conclusion.

The eval work also improved retrieval and prompts. Query terms became weak
seeds rather than the whole retrieval strategy. Severity-based log retrieval was
added so incident-window warnings and errors for the affected service are not
missed just because the user's wording was incomplete.

## Observability Is Part Of The Design

Agentic workflow failures are not limited to exceptions. A model can return
valid JSON that is semantically risky. A critic can be unavailable. Weak
evidence can lower confidence. Human-review routing can change the final
outcome.

For that reason, observability became a first-class feature:

```text
investigation.run
  evidence.retrieval
  graph.node.*
    llm.call.*
```

Structured JSON events record facts, counts, statuses, decisions, warnings, and
timings. Optional OpenTelemetry console spans show execution flow and latency.
The implementation avoids logging sensitive or noisy content such as prompts,
raw model responses, full evidence payloads, hypothesis statements, or full
graph state.

LangGraph nodes are natural observability boundaries because each node consumes
state, performs one workflow step, and returns a state update.

## Python Lessons From A .NET Background

The project deliberately avoided translating C# architecture into Python.

The main Python habits were:

- prefer modules, functions, dataclasses or Pydantic models, and protocols over
  broad class hierarchies;
- use `Protocol` when behavior needs to be substitutable, not by default;
- pass dependencies at composition points instead of adding a DI container;
- keep graph nodes small and push behavior into testable application functions;
- use explicit typed models where the data crosses important boundaries;
- avoid interface-heavy ceremony unless it protects a real seam.

The closest .NET analogies were useful but not exact. Graph state resembles a
workflow context DTO. Nodes resemble small application handlers. Checkpointing
resembles durable orchestration state. The run registry resembles an
application-owned read model. But the Python implementation should remain
lighter than a typical enterprise service stack.

## Final Takeaways

The learning journey produced one central design position:

> LangGraph orchestrates the investigation, but deterministic Python owns the
> evidence boundary, validation policy, review routing, evaluation, and public
> API contract.

The implementation is intentionally not a production observability product, not
a general incident portal, and not an autonomous root-cause engine. It is a
bounded implementation of an evidence-backed AI workflow.

The most defensible parts are the controls around model output: cited evidence,
validation, semantic critique, deterministic review policy, checkpointed human
review, evaluation, and observability.

The original notes remain useful as historical detail, but this summary is the
compressed learning narrative.

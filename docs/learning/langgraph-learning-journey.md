# LangGraph Learning Journey — Telemetry Investigation Agents

## Purpose

This repository is a structured learning journey for building a production-oriented Python + LangGraph investigation system.

The goal is not to learn LangGraph as a trendy framework.

The goal is to learn how to design reliable AI workflow systems with:

- explicit workflow state,
- bounded LLM reasoning,
- deterministic processing,
- evidence-backed conclusions,
- confidence and uncertainty handling,
- evaluation,
- observability,
- maintainable Python architecture.

This journey should teach native Python and LangGraph engineering approaches first. .NET/C# comparisons may be used only when they clarify tradeoffs or expose habits that do not translate well into Python.

---

# Final project vision

## Project

`Telemetry Investigation Agents`

## Portfolio thesis

> A production-oriented incident investigation workflow system that analyzes synthetic telemetry evidence, generates and validates root-cause hypotheses, and produces cited investigation reports with confidence and uncertainty handling.

---

# System workflow

```text
Incident intake
    ↓
Telemetry retrieval
    ↓
Log analysis
    ↓
Trace correlation
    ↓
Metrics review
    ↓
Hypothesis generation
    ↓
Evidence validation
    ↓
LLM critic semantic review
    ↓
Human review when needed
    ↓
Final cited report
```

---

# Architectural principles

1. LangGraph orchestrates workflow state and transitions.
2. Domain models do not depend on LangGraph.
3. Deterministic logic owns parsing, filtering, correlation, and scoring where possible.
4. LLMs assist with summarization, hypothesis generation, contradiction analysis, and narrative synthesis.
5. Every report claim should reference evidence.
6. Weak evidence should reduce confidence rather than produce hallucinated certainty.
7. Human review is a risk-control mechanism.
8. Evaluation should exist before prompt optimization.
9. Observability is a first-class concern.
10. Prefer idiomatic Python over translated enterprise Java/.NET patterns.

---

# Repository target

```text
telemetry-investigation-agents/
├── src/telemetry_agents/
│   ├── domain/
│   ├── application/
│   ├── graph/
│   ├── infrastructure/
│   ├── api/
│   └── shared/
├── tests/
├── evals/
├── sample_data/
├── docs/
└── scripts/
```

---

### Folder intent

| Folder | Purpose |
|---|---|
| `domain` | Core incident, telemetry, evidence, hypothesis, and report models. No LangGraph dependency. |
| `application` | Use-case services and deterministic investigation logic. |
| `graph` | LangGraph state, nodes, edges, routing, interrupts, and workflow composition. |
| `infrastructure` | LLM clients, vector store, telemetry readers, persistence, external adapters. |
| `api` | FastAPI or CLI entrypoints. |
| `evals` | Golden cases and evaluation runners. |
| `sample_data` | Synthetic logs, traces, metrics, and incident tickets. |
| `docs/adr` | Architecture decision records. |
| `docs/learning-notes` | Personal learning notes after each checkpoint. |

---

## 3. Journey rules

Codex must follow these rules during the journey:

1. Teach one concept at a time.
2. Implement one small vertical slice at a time.
3. Do not generate the full project prematurely.
4. Explain concepts from the native Python/LangGraph perspective first. Use .NET/C# comparisons only when they clarify a tradeoff, expose a habit to unlearn, or help connect a difficult concept.
5. Keep LLM calls behind small adapters or protocols when substitution, testing, or isolation requires it.
6. Keep deterministic logic outside LLM prompts.
7. Prefer explicit state and typed models, without turning Python into Java/C#.
8. Add tests as soon as there is behavior worth testing.
9. Add evaluation cases before optimizing prompts.
10. Add observability before the system becomes complex.
11. Maintain a learning journal.
12. Use architecture decision records for meaningful tradeoffs.
13. Every phase must end with a checkpoint that can be marked complete.

---

## Plan challenge rule

This learning journey is a baseline, not final architecture law.

Before implementing each checkpoint:
1. Restate what the plan proposes.
2. Identify the architectural assumptions behind it.
3. Present 2–3 viable alternatives.
4. Explain tradeoffs.
5. Ask the learner to choose.
6. Critique the learner’s choice.
7. Only then proceed with skeletons/tests/implementation.

Do not treat existing architecture decisions as final unless the learner explicitly accepts them.

---

## 4. Progress board

Codex may recommend checkpoint completion, but the learner must approve it.

Before any phase is marked DONE:
1. Codex asks 3–5 verification questions.
2. Learner answers.
3. Codex reviews the answers critically.
4. If understanding is sufficient, learner approves the checkpoint.
5. Only then Codex updates the progress board.

| Phase | Status | Completion date | Notes |
|---|---|---:|---|
| 1. Python project foundation | DONE | 2026-05-09 | Minimal package foundation, README, learning note, and import test added. |
| 2. LangGraph fundamentals | DONE | 2026-05-11 | Minimal graph, typed state, fixed edges, unit test, and learning note exist. |
| 3. Typed state and domain modeling | DONE | 2026-05-11 | Domain models, explicit graph state, validation tests, and ADR added. |
| 4. Control flow and conditional routing | DONE | 2026-05-11 | Deterministic routing function, conditional graph wiring, tests, and learning note exist. |
| 5. Tool abstraction and adapters | DONE | 2026-05-11 | Local telemetry tool protocols/adapters, typed evidence results, explicit file/malformed-data behavior, tests, and learning note exist. |
| 6. Deterministic telemetry parsing | DONE | 2026-05-14 | Deterministic parsers, filtering helpers, malformed-input tests, and one synthetic incident fixture exist. |
| 7. Evidence retrieval and citations | DONE | 2026-05-25 | Retrieval preserves citations, represents absent source files as missing evidence, and ranks merged evidence by relevance with regression tests. |
| 8. Agentic hypothesis generation | DONE | 2026-05-18 | Bounded hypothesis generation uses a protocol-backed generator to produce typed candidate hypotheses, fake LLM tests, and a learning note. Evidence policy is owned by validation. |
| 9. Evidence validator | DONE | 2026-05-19 | Deterministic hypothesis validator owns evidence-reference policy, structured validation result, graph node, confidence adjustment audit trail, focused tests, and learning note. Semantic contradiction detection is deferred to the LLM critic phase. |
| 10. LLM critic for semantic review | DONE | 2026-05-21 | Separate critic node and protocol-backed adapter review accepted hypotheses for semantic issues, validate cited IDs, reject missing evidence as critique support, and safely fall back with a warning when the critic is unavailable. |
| 11. Persistence, checkpointing, and interrupts | DONE | 2026-05-22 | SQLite-backed LangGraph checkpointing, app-owned run registry, state inspection, simulated resume, interrupt/resume gate, ADR, and learning note exist. |
| 12. Human-in-the-loop review | DONE | 2026-05-25 | Risk-based review assessment, typed status, conditional interrupt/bypass routing, approval/rejection outcomes, focused tests, and learning note exist. Evidence re-entry and edited recommendations are deferred. |
| 13. Azure OpenAI integration and graph smoke | DONE | 2026-05-28 | Azure OpenAI generator and critic adapters use Microsoft Entra ID, structured outputs, mocked adapter tests, adapter-level live smoke tests, and one graph-level live smoke run through generation, validation, critique, human review, and approval resume. |
| 14. Evaluation framework | IN_PROGRESS |  | Deterministic scorecard, citation-correctness invariant scoring, and protocol-backed semantic unsupported-claim review guardrails exist. Azure reviewer integration, golden-case expansion, batch execution, reproducible reporting, ADR, and learning note remain. |
| 15. Observability and tracing | TODO |  |  |
| 16. API / CLI interface | TODO |  |  |
| 17. Portfolio skeleton hardening | TODO |  |  |
| 18. Final review and roadmap | TODO |  |  |

Status values: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`, `REWORK`.

---

# Phase 1 — Python project foundation

## Goal

Set up a clean Python project that feels maintainable to a senior enterprise developer.

## Concepts

- Python packaging.
- `pyproject.toml`.
- Dependency management with `uv` or Poetry.
- Test layout.
- Source layout.
- Environment configuration.
- Formatting and linting.
- Why Python projects often become messy and how to prevent it.

## Implementation tasks

- Create initial repository structure.
- Add `pyproject.toml`.
- Add `src/telemetry_agents`.
- Add `tests`.
- Add basic test runner.
- Add `.env.example`.
- Add `README.md` with project thesis.
- Add `/docs/learning-notes`.
- Add `/docs/adr`.

## Learning tasks

- Compare Python package/module boundaries with .NET project boundaries.
- Write a short note: “What replaces solution/project boundaries in this Python repo?”
- Decide whether to use `TypedDict`, Pydantic, or dataclasses in different layers.

## Checkpoint

- [x] Project can install dependencies.
- [x] Tests can run.
- [x] Basic package import works.
- [x] Repository structure exists.
- [x] First learning note exists.
- [x] README states portfolio thesis clearly.

## Codex stop condition

Stop after project foundation is runnable. Do not add LangGraph yet unless explicitly requested.

---

# Phase 2 — LangGraph fundamentals

## Goal

Understand LangGraph’s core mental model: state, nodes, edges, graph compilation, and invocation.

LangGraph’s official docs define the Graph API around shared **State**, executable **Nodes**, and **Edges** that determine what node runs next. Nodes are just functions; edges define control flow.

## Concepts

- `StateGraph`.
- State schema.
- Node function.
- Fixed edge.
- `START` and `END`.
- Graph compilation.
- Graph invocation.
- Difference between a graph and a normal function pipeline.

## Implementation tasks

- Build the smallest graph:
  - input incident title,
  - normalize incident title,
  - create initial investigation summary.
- Use a minimal typed state.
- Add a simple unit test.

## Learning tasks

- Explain graph state as a workflow context object.
- Compare LangGraph with:
  - .NET state machine,
  - workflow engine,
  - mediator pipeline,
  - durable function orchestration.
- Write one paragraph explaining why graph execution matters for agentic workflows.

## Checkpoint

- [x] Minimal LangGraph graph runs.
- [x] State is typed.
- [x] At least two nodes exist.
- [x] At least one fixed edge exists.
- [x] Unit test verifies final state.
- [x] Learning note explains state/nodes/edges.

## Codex stop condition

Stop after the minimal graph and explanation. Do not introduce tools, agents, or RAG yet.

---

# Phase 3 — Typed state and domain modeling

## Goal

Separate graph state from domain models and avoid turning the graph state into an unstructured dictionary.

## Concepts

- `TypedDict` vs Pydantic.
- Domain models.
- Application DTOs.
- State as orchestration context.
- Immutable-ish state thinking.
- Reducers and state updates.
- Clear state ownership.

## Implementation tasks

Create early domain models:

- `Incident`
- `TelemetryEvidence`
- `EvidenceSource`
- `InvestigationHypothesis`
- `InvestigationReport`

Create graph state:

- incident input,
- normalized incident,
- collected evidence,
- intermediate findings,
- hypotheses,
- validation result,
- final report,
- errors/warnings.

## Learning tasks

- Decide which objects belong in `domain` and which belong in `graph`.
- Write an ADR: “Graph state is not the domain model.”
- Explain how this maps to C# records, DTOs, and application services.

## Checkpoint

- [x] Domain models exist.
- [x] Graph state is explicit and typed.
- [x] State does not contain random untyped dictionaries.
- [x] Tests cover model validation.
- [x] ADR exists.

## Codex stop condition

Stop after model/state design and tests.

---

# Phase 4 — Control flow and conditional routing

## Goal

Learn how LangGraph handles branching and decision-making.

## Concepts

- Fixed edges.
- Conditional edges.
- Routing functions.
- Deterministic routing.
- LLM-assisted routing.
- Safe fallback routing.
- Error paths.

## Implementation tasks

Add routing after incident intake:

```text
incident intake
    ↓
classify incident type
    ↓
route to:
    - log-focused investigation
    - trace-focused investigation
    - metric-focused investigation
    - broad investigation
```

Initial classification should be deterministic or rule-based. LLM routing can be introduced later.

## Learning tasks

- Explain why deterministic routing should be preferred when possible.
- Compare LangGraph conditional edges with strategy pattern and state machine transitions.
- Add test cases for routing decisions.

## Checkpoint

- [x] Conditional route exists.
- [x] Routing function is tested.
- [x] Unknown incident type has fallback behavior.
- [x] State captures routing decision.
- [x] Learning note explains deterministic vs LLM routing.

## Codex stop condition

Stop after routing and tests.

---

# Phase 5 — Tool abstraction and adapters

## Goal

Learn how tools should be represented without coupling domain logic directly to external systems.

## Concepts

- Tool functions.
- Adapters.
- Ports and interfaces.
- Mockable tools.
- Side-effect boundaries.
- Tool error handling.
- Tool result schemas.

## Implementation tasks

Create tool-like adapters for synthetic telemetry:

- `LogSearchTool`
- `TraceLookupTool`
- `MetricWindowTool`

Initially they should read from local files in `sample_data`.

## Learning tasks

- Explain the difference between a LangGraph node and a tool.
- Explain how tool adapters map to C# interfaces.
- Add failure behavior for missing files and malformed data.

## Checkpoint

- [x] Telemetry tool interfaces/adapters exist.
- [x] Tools return typed results.
- [x] Tools are testable without LLMs.
- [x] Missing-data behavior is explicit.
- [x] Learning note explains ports/adapters.

## Codex stop condition

Stop after local telemetry adapters and tests.

---

# Phase 6 — Deterministic telemetry parsing

## Goal

Build deterministic parsing and normalization before using LLM reasoning.

## Concepts

- Structured logs.
- Trace spans.
- Metric samples/windows.
- Normalization.
- Error signatures.
- Time-window filtering.
- Trace IDs as the current correlation key.

## Implementation tasks

Create parsers for synthetic data:

- logs: timestamp, level, service, message, trace ID, exception type.
- traces: trace ID, span ID, service, operation, duration, status.
- metrics: timestamp, service, metric name, value.

## Learning tasks

- Define what the LLM should not do.
- Write tests for parsing and filtering.
- Add one synthetic incident with known root cause.

## Checkpoint

- [x] Parsers exist.
- [x] Time-window filtering works.
- [x] Trace ID filtering works.
- [x] Synthetic incident data exists.
- [x] Tests cover normal and malformed inputs.

## Codex stop condition

Stop after deterministic telemetry foundation.

---

# Phase 7 — Evidence retrieval and citations

## Goal

Build evidence retrieval before hypothesis generation.

## Concepts

- Evidence object.
- Evidence source.
- Citation.
- Relevance scoring.
- Strong vs weak evidence.
- Missing evidence.
- Retrieval without vector DB first.
- Later vector retrieval if needed.

## Implementation tasks

Build evidence retrieval nodes:

```text
retrieve logs
retrieve traces
retrieve metrics
merge evidence
rank evidence
```

Each evidence item should preserve citation metadata:

- source file,
- line number or record ID,
- timestamp,
- service/component,
- reason it was selected.

## Learning tasks

- Implement simple keyword/time/trace-correlation retrieval before vector search.
- Write “insufficient evidence” behavior.
- Add tests proving every evidence item has citation metadata.

## Checkpoint

- [x] Evidence retrieval works.
- [x] Evidence has source/citation metadata.
- [x] Weak evidence is represented explicitly.
- [x] Missing evidence does not crash graph.
- [x] Tests validate citations.

## Codex stop condition

Stop after cited evidence retrieval. Do not add LLM hypothesis generation yet.

---

# Phase 8 — Agentic hypothesis generation

## Goal

Introduce LLM reasoning in a bounded way.

## Concepts

- Agent node.
- Prompt boundaries.
- Structured LLM output.
- Hypothesis schema.
- Confidence.
- Evidence references.
- Hallucination risk.
- “No hypothesis” as valid output.

## Implementation tasks

Create a `HypothesisGeneratorNode` that:

- receives incident and evidence,
- returns structured candidate hypotheses,
- asks the LLM to reference evidence IDs,
- assigns preliminary confidence,
- states uncertainty.

Use an LLM adapter interface so the graph does not depend directly on a provider SDK.

## Learning tasks

- Define prompt contract.
- Add fake LLM for tests.
- Treat generator output as untrusted candidate state.
- Defer evidence-reference policy to the validator.

## Checkpoint

- [x] LLM adapter interface exists.
- [x] Hypothesis node uses structured output.
- [x] Fake LLM tests exist.
- [x] Hypothesis generation returns typed candidate hypotheses.
- [x] Raw generated hypotheses are treated as untrusted until validation.
- [x] Learning note explains bounded LLM reasoning.

## Codex stop condition

Stop after bounded hypothesis generation.

---

# Phase 9 — Evidence validator

## Goal

Add a deterministic validator step that reviews generated candidate hypotheses against retrieved evidence before they can be used downstream.

## Concepts

- Evidence validation.
- Confidence adjustment.
- Reference integrity.
- Missing evidence handling.
- Weak evidence handling.
- Separation between generation and validation.
- Validation as an audit trail.

## Implementation tasks

Create a `HypothesisValidatorNode` that checks:

- every hypothesis has supporting evidence,
- cited evidence IDs exist,
- missing evidence is not used as support,
- confidence is adjusted,
- unsupported claims are downgraded or rejected.

Downstream nodes should treat `validation_result`, not raw generated `hypotheses`, as the trusted evidence-reviewed hypothesis state.

Semantic contradiction detection is intentionally out of scope for this phase and belongs to the LLM critic phase.

## Learning tasks

- Add tests for:
  - unsupported hypothesis,
  - unknown evidence references,
  - missing evidence as support,
  - weak-but-plausible hypothesis,
  - strong evidence hypothesis.
- Explain why deterministic validation should stay narrow and auditable.
- Explain why semantic contradiction review is deferred to an LLM critic.

## Checkpoint

- [x] Validator node exists.
- [x] Unsupported claims are rejected or downgraded.
- [x] Semantic contradiction detection is explicitly deferred.
- [x] Confidence changes are explainable.
- [x] Tests cover validation cases.
- [x] Learning note explains generator/validator separation.

## Codex stop condition

Stop after deterministic evidence validation.

---

# Phase 10 — LLM critic for semantic review

## Goal

Add a separate LLM critic node that reviews validated hypotheses for semantic problems that deterministic code should not pretend to understand.

The deterministic validator owns reference integrity, missing evidence handling, and confidence policy. The LLM critic reviews higher-level reasoning quality while still being constrained by structured output and deterministic guardrails.

## Concepts

- Critic node.
- Semantic contradiction review.
- Unsupported causal leaps.
- Alternative interpretations.
- Structured critic output.
- Cited critique evidence.
- LLM output validation.
- Separation between deterministic validation and probabilistic critique.
- Failure fallback when critic LLM is unavailable.

## Implementation tasks

Create a `HypothesisCriticNode` that:

- receives retrieved evidence and `HypothesisValidationResult`,
- reviews accepted hypotheses for semantic contradictions or unsupported causal claims,
- returns structured critic findings,
- cites evidence IDs for every contradiction or concern,
- cannot invent hypothesis IDs or evidence IDs,
- enriches the existing validation result or returns a critic result that can be merged into it.

Use an LLM critic adapter interface so the graph does not depend directly on a provider SDK.

The critic should be a separate LangGraph node, not hidden inside the deterministic validator.

## Learning tasks

- Explain why the critic is separate from the deterministic validator.
- Define the critic prompt contract.
- Add fake LLM critic tests.
- Add deterministic guardrails for critic output:
  - critic findings must reference known hypothesis IDs,
  - critic findings must cite known evidence IDs,
  - critic cannot cite missing evidence as contradiction support,
  - critic cannot increase confidence.
- Explain fallback behavior if the critic LLM fails.

## Checkpoint

- [x] Critic node exists separately from validator node.
- [x] Critic adapter interface exists.
- [x] Fake critic LLM tests exist.
- [x] Critic output is structured.
- [x] Critic findings cite evidence IDs.
- [x] Critic cannot invent hypothesis or evidence IDs.
- [x] Critic failure has safe fallback behavior.
- [x] Learning note explains deterministic validation vs LLM critique.

## Codex stop condition

Stop after LLM critic review is implemented and tested. Do not add checkpointing yet.

---

# Phase 11 — Persistence, checkpointing, and interrupts

## Goal

Learn durable execution and interruption patterns.

LangGraph supports durable execution by persisting agent state so workflows can resume after failures or pauses. Checkpointers are also required for human-in-the-loop workflows because the graph must preserve inspectable state before resuming.

## Concepts

- Checkpointer.
- Thread ID.
- Durable execution.
- Resume.
- State inspection.
- Interrupt.
- Recovery after failure.
- Long-running workflows.

## Implementation tasks

- Add a simple checkpointer.
- Persist graph state between steps.
- Assign investigation run IDs.
- Simulate failure and resume.
- Add one interrupt before final report generation.

## Learning tasks

- Compare LangGraph persistence with durable orchestrations.
- Write an ADR: “Why investigation workflows need checkpointing.”
- Add test or scripted demo showing resume behavior.

## Checkpoint

- [x] Checkpointer is configured.
- [x] Investigation run ID exists.
- [x] State can be inspected.
- [x] Simulated resume works.
- [x] Interrupt point exists.
- [x] ADR exists.

## Codex stop condition

Stop after durable execution demonstration.

---

# Phase 12 — Human-in-the-loop review

## Goal

Add human review for low-confidence or high-impact investigations.

LangGraph interrupts allow graph execution to pause and wait for external input before continuing. This enables approval/edit/reject workflows.

## Concepts

- Human approval.
- Edit-and-resume.
- Reject path.
- Escalation policy.
- Risk threshold.
- Approval audit trail.
- Human review as workflow state, not UI magic.

## Implementation tasks

Add human review if:

- confidence is below threshold,
- evidence is weak,
- incident impact is high,
- LLM critic finds contradictions.

Human reviewer can:

- approve,
- reject,
- request more evidence,
- edit final recommendation.

## Learning tasks

- Design review decision model.
- Add tests for routing to human review.
- Write note: “Human-in-the-loop is a risk control, not a UX feature.”

## Checkpoint

- [x] Human review condition exists.
- [x] Interrupt/resume path works.
- [x] Approval decision is stored.
- [x] Rejection path is explicit.
- [x] Tests cover review routing.
- [x] Learning note exists.

## Codex stop condition

Stop after human review flow.

---

# Phase 13 - Azure OpenAI integration and graph smoke

## Goal

Connect the existing probabilistic workflow boundaries to Azure OpenAI in Microsoft Foundry, then prove the compiled graph can execute end-to-end with the live provider adapters before building the formal evaluation framework.

This phase is intentionally an infrastructure integration step. LangGraph remains responsible for workflow state, deterministic validation, checkpointing, and human-review routing. Azure OpenAI supplies bounded structured model calls only.

## Concepts

- Concrete provider adapter behind a Python `Protocol`.
- Azure OpenAI deployment versus application model contract.
- Microsoft Entra ID authentication and Azure RBAC.
- Structured model output validated into existing Pydantic models.
- Adapter-level live smoke validation versus graph-level live smoke validation.
- Provider failure translation and safe fallback behavior.
- End-to-end graph execution with live LLM adapters.

## Architectural decision

Use Azure OpenAI because the portfolio objective includes enterprise AI positioning in the Microsoft ecosystem.

Use Microsoft Entra ID authentication only for the initial integration, implemented
through `DefaultAzureCredential`. Do not add API-key fallback in this phase. This
keeps the credential model aligned with Azure RBAC and prevents a second
configuration path from obscuring the adapter lesson.

The accepted boundary is:

```text
LangGraph workflow
    -> HypothesisGenerator / HypothesisCritic protocols
    -> Azure OpenAI infrastructure adapters
    -> Azure OpenAI deployed model in Microsoft Foundry
```

Do not use hosted agent orchestration or move deterministic evidence policy into the provider layer. This project demonstrates LangGraph workflow ownership with Azure-backed model calls, not two overlapping orchestration systems.

## Implementation tasks

- Select an Azure OpenAI deployment supporting structured outputs.
- Configure local Azure access, preferably through Microsoft Entra ID.
- Add one concrete Azure OpenAI adapter for hypothesis generation.
- Add one concrete Azure OpenAI adapter for hypothesis critique.
- Parse structured responses into the existing typed domain contracts.
- Translate known provider unavailability into the existing safe workflow behavior where applicable.
- Add mocked adapter tests that require no Azure credentials.
- Add opt-in adapter-level live smoke invocations using existing synthetic evidence.
- Add one opt-in graph-level live smoke test that wires the compiled graph with the Azure generator and critic adapters in a single execution.
- Verify the graph-level smoke run exercises the existing graph nodes together: hypothesis generation, validation, critic review, human-review assessment, and review/ready routing.
- Document configuration, credential handling, nondeterminism, and live-call cost expectations.

## Deliberate non-goals

- Do not create Foundry hosted agents.
- Do not add Azure AI Search or vector retrieval.
- Do not optimize prompts before evaluation exists.
- Do not put live Azure calls in the normal unit-test suite.
- Do not add telemetry/tracing before the observability phase.
- Do not build CLI/API exposure in this phase.
- Do not build the full evaluation framework in this phase.
- Do not tune prompts from a single graph-level smoke result.

## Learning tasks

- Explain why an infrastructure adapter is sufficient for Azure OpenAI integration.
- Compare Microsoft Entra ID authentication with API-key configuration and choose explicitly.
- Define which provider errors should fail the run and which critic failures may trigger the existing safe fallback.
- Explain what an end-to-end smoke test proves and what it does not prove.
- Run one live graph execution and inspect whether generated hypotheses and critic findings remain bounded by supplied evidence IDs.

## Checkpoint

- [x] Azure OpenAI authentication approach is selected and documented.
- [x] Concrete hypothesis generator adapter exists.
- [x] Concrete hypothesis critic adapter exists.
- [x] Structured outputs are validated into existing typed models.
- [x] Mocked adapter tests cover success and provider failure behavior.
- [x] One opt-in adapter-level live smoke invocation succeeds.
- [x] One opt-in graph-level live smoke execution succeeds.
- [x] Graph-level smoke couples all current graph nodes with live Azure OpenAI generator and critic adapters in one run.
- [x] Live graph output is inspected for evidence-reference discipline before accepting the checkpoint.
- [x] Learning note records provider boundaries, risks, and limitations.

## Codex stop condition

Stop after Azure OpenAI-backed graph smoke validation. Do not begin evaluation cases or prompt optimization yet.

---

# Phase 14 — Evaluation framework

## Goal

Make the system measurable.

## Concepts

- Golden datasets.
- Expected outputs.
- Classification accuracy.
- Evidence recall.
- Citation correctness.
- Hallucination checks.
- Regression evaluation.
- Cost/latency tracking.
- Prompt regression.

## Implementation tasks

Create `/evals` with synthetic cases:

- database timeout during checkout traffic,
- latency spike caused by downstream dependency,
- conflicting evidence with no dominant explanation,
- insufficient evidence case.

For each case define:

- expected category,
- expected evidence sources,
- expected escalation behavior.

Do not maintain speculative unsupported-claim blacklists in golden cases.
Semantic unsupported-claim review should independently compare accepted
hypotheses with retrieved evidence.

Build a bounded MVP scorecard with visibly separate dimensions:

Deterministic dimensions:

- expected hypothesis category,
- expected evidence-source coverage,
- citation correctness,
- expected human-review behavior.

Probabilistic dimension:

- semantic unsupported causal-claim review.

Use a separate protocol-backed reviewer after workflow execution. The evaluator
may use similar inputs and structural guardrails as the workflow critic, but it
must not call the workflow critic or influence graph state. Evaluation measures
whether unsupported causal claims passed through the workflow controls.

Keep the MVP constrained:

- add one Azure OpenAI reviewer adapter,
- add mocked adapter tests and one opt-in live smoke test,
- load eval cases from JSON,
- run all golden cases through a batch runner,
- emit a simple reproducible pass/fail report.

Do not add embeddings, multiple judges, weighted score aggregation,
statistical benchmarking, dashboards, or prompt optimization in this phase.

## Learning tasks

- [x] Build simple deterministic eval runner.
- [x] Add expected-category scoring.
- [x] Add expected evidence-source scoring.
- [x] Add expected human-review scoring.
- [x] Add citation-correctness invariant scoring.
- [x] Add protocol-backed semantic unsupported-claim reviewer with deterministic
  output guardrails.
- [x] Add Azure OpenAI semantic reviewer adapter.
- [x] Add mocked adapter tests and one opt-in live smoke test.
- [x] Add semantic-review scorecard integration.
- [x] Add MVP golden cases.
- [ ] Add JSON loading and batch execution.
- [ ] Track pass/fail over time with a simple reproducible report.
- [ ] Write ADR: “Evaluation before prompt optimization.”

## Checkpoint

- [x] At least four eval cases exist.
- [x] Eval runner exists.
- [x] Citation correctness is scored.
- [ ] Unsupported claims are detected.
- [ ] Results are reproducible.
- [ ] ADR exists.

## Codex stop condition

Stop after basic evaluation loop.

---

# Phase 15 — Observability and tracing

## Goal

Make the agentic workflow inspectable like a production system.

## Concepts

- Structured logs.
- Trace IDs.
- Span boundaries.
- Node-level latency.
- Tool latency.
- LLM latency/cost.
- Error telemetry.
- Trace IDs and run IDs.
- OpenTelemetry.
- Debuggability of agent workflows.

## Implementation tasks

Add observability for:

- graph run ID,
- incident ID,
- node execution,
- tool calls,
- evidence count,
- confidence changes,
- LLM call metadata,
- errors/fallbacks,
- eval results.

## Learning tasks

- Map graph nodes to tracing spans.
- Add structured logs.
- Add one OpenTelemetry exporter or local trace demonstration.
- Write learning note: “Agent observability is not optional.”

## Checkpoint

- [ ] Structured logging exists.
- [ ] Graph run has a run ID.
- [ ] Nodes emit useful telemetry.
- [ ] Tool failures are observable.
- [ ] LLM calls are traceable through adapter.
- [ ] Learning note exists.

## Codex stop condition

Stop after local observability demonstration.

---

# Phase 16 — API / CLI interface

## Goal

Expose the workflow in a clean way without polluting core design.

## Concepts

- FastAPI boundary.
- CLI runner.
- Request/response schemas.
- Async execution.
- Run ID.
- Resume endpoint.
- Human review endpoint.
- Separation between API and graph.

## Implementation tasks

Create either CLI first or FastAPI first:

CLI commands:

```text
investigate --incident sample_data/incidents/db-timeout.json
resume --run-id <id> --decision approve
eval run
```

Optional FastAPI endpoints:

```text
POST /investigations
GET /investigations/{run_id}
POST /investigations/{run_id}/review
POST /evals/run
```

## Learning tasks

- Explain why API should not know graph internals.
- Add one integration test.
- Add README usage examples.

## Checkpoint

- [ ] CLI or API exists.
- [ ] Investigation can be launched externally.
- [ ] Resume/review path exists if HITL is implemented.
- [ ] API/CLI does not contain business logic.
- [ ] README has usage instructions.

## Codex stop condition

Stop after external interface is usable.

---

# Phase 17 — Portfolio skeleton hardening

## Goal

Make the repository credible as a public portfolio artifact.

## Concepts

- Portfolio narrative.
- Architecture documentation.
- ADRs.
- Reproducibility.
- Developer experience.
- Limitations.
- Roadmap.
- Demo scenarios.
- Avoiding overclaims.

## Implementation tasks

Add:

- architecture diagram,
- README walkthrough,
- sample investigation report,
- ADR index,
- eval report,
- observability screenshots or trace examples,
- limitations section,
- roadmap.

## Learning tasks

- Write project positioning:
  - what it demonstrates,
  - what it does not claim,
  - why LangGraph was chosen,
  - how this would map to enterprise systems.
- Add “design tradeoffs” section.

## Checkpoint

- [ ] README is portfolio-quality.
- [ ] Architecture diagram exists.
- [ ] Sample data and sample output exist.
- [ ] ADRs document major decisions.
- [ ] Eval results are included.
- [ ] Limitations are honest.
- [ ] Setup is reproducible.

## Codex stop condition

Stop after portfolio hardening. Do not add unnecessary features.

---

# Phase 18 — Final review and roadmap

## Goal

Pressure-test the project as if it were discussed in a Senior AI Engineer interview.

## Review questions

- Can I explain why LangGraph is used here?
- Can I explain state, nodes, edges, checkpoints, and interrupts?
- Can I show where deterministic code ends and LLM reasoning begins?
- Can I explain how hallucination is controlled?
- Can I show evals?
- Can I show telemetry/traces?
- Can I explain failure modes?
- Can I compare this with MAF conceptually?
- Can I explain what would change in a real enterprise deployment?
- Can I explain what is intentionally out of scope?

## Final checkpoint

- [ ] I can explain the graph architecture from memory.
- [ ] I can add a new node without Codex.
- [ ] I can add a new eval case without Codex.
- [ ] I can debug a failed investigation run.
- [ ] I can explain confidence scoring.
- [ ] I can explain human review triggers.
- [ ] I can defend architecture decisions.
- [ ] I can discuss LangGraph vs MAF tradeoffs clearly.

---

## 5. Learning journal template

For every session, create or update a note in:

```text
docs/learning-notes/YYYY-MM-DD-session-title.md
```

Use this template:

```markdown
# Session: <title>

## Goal

## What I built

## LangGraph concept learned

## Mapping to .NET/C# thinking

## What confused me

## Tradeoffs noticed

## Production concerns

## Tests/evals added

## Next step
```

---

## 6. ADR template

For meaningful decisions, create:

```text
docs/adr/NNNN-short-title.md
```

Template:

```markdown
# ADR NNNN: <decision>

## Status

Proposed / Accepted / Superseded

## Context

## Decision

## Consequences

## Alternatives considered

## Why this matters for Telemetry Investigation Agents
```

---

## 7. Codex usage rule

At the start of every Codex session, provide the mentor prompt and remind Codex:

```text
Read docs/langgraph-learning-journey.md.
Continue from the first incomplete checkpoint.
Do not regenerate the entire project.
Teach one concept, implement one vertical slice, update the checklist, then stop.
```

---

## 8. Quality bar

The project is successful only if it demonstrates senior engineering quality.

The minimum acceptable standard:

- typed state,
- clear module boundaries,
- deterministic processing separated from LLM reasoning,
- citations for claims,
- weak evidence behavior,
- evaluation cases,
- observability,
- human review for risky decisions,
- honest documentation,
- reproducible setup.

The project fails if it becomes:

- a chatbot,
- prompt spaghetti,
- untyped Python scripts,
- a LangGraph tutorial clone,
- an overengineered distributed system,
- a demo with no evals,
- a system that produces confident answers from weak evidence.

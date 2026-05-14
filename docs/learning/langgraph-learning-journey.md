# LangGraph Learning Journey — Telemetry Investigation Agents

**Purpose:** Private learning plan stored in the repository and used by Codex across multiple clean sessions.  
**Final portfolio target:** `Telemetry Investigation Agents` — a production-oriented Python + LangGraph system that investigates synthetic incidents using logs, traces, metrics, and deployment events, then produces cited investigation reports with confidence levels and explicit uncertainty.

---

## 0. Strategic intent

This journey is not about learning LangGraph as a trendy framework.

The goal is to acquire enough LangGraph skill to design, implement, explain, and defend an enterprise-grade agentic workflow system. The final project should demonstrate that I can build reliable AI systems with:

- explicit graph state,
- bounded LLM decision points,
- deterministic processing where possible,
- evidence-backed reasoning,
- human review checkpoints,
- evaluation cases,
- observability,
- clean architecture,
- maintainable Python code.

I am a Senior .NET Developer / Tech Lead. The journey should deliberately map LangGraph concepts to familiar enterprise engineering concepts such as workflow engines, state machines, orchestration layers, domain services, adapters, observability pipelines, and integration boundaries.

---

## 1. Final project vision

### Project name

`Telemetry Investigation Agents`

### Portfolio thesis

> A LangGraph-based incident investigation system that analyzes telemetry evidence from synthetic enterprise services, correlates logs/traces/metrics/deployment events, generates root-cause hypotheses, validates those hypotheses against evidence, and produces a cited investigation report with confidence and escalation behavior.

### Final workflow

```text
Incident intake
    ↓
Telemetry retrieval
    ↓
Log pattern analysis
    ↓
Trace correlation
    ↓
Metrics anomaly review
    ↓
Deployment/change correlation
    ↓
Hypothesis generation
    ↓
Evidence validation / critic
    ↓
Human review if confidence is low or impact is high
    ↓
Final cited investigation report
```

### Expected final output

Each investigation should produce:

- incident summary,
- affected service/component,
- suspected failure category,
- top root-cause hypotheses,
- supporting evidence,
- contradicting evidence,
- confidence level,
- uncertainty statement,
- recommended next actions,
- citations to log lines, traces, metric windows, and deployment events.

### Non-goals

This project is **not**:

- a chatbot over logs,
- an autonomous incident commander,
- a generic RAG demo,
- a fake multi-agent swarm,
- a system where LLMs perform deterministic calculations,
- a framework showcase without engineering discipline.

---

## 2. Repository structure target

The final repository should gradually evolve toward:

```text
telemetry-investigation-agents/
├── README.md
├── pyproject.toml
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── sample_data/
│   ├── incidents/
│   ├── logs/
│   ├── traces/
│   ├── metrics/
│   └── deployments/
├── src/
│   └── telemetry_agents/
│       ├── domain/
│       ├── application/
│       ├── graph/
│       ├── infrastructure/
│       ├── api/
│       └── shared/
├── tests/
├── evals/
├── docs/
│   ├── learning-notes/
│   ├── adr/
│   └── architecture/
└── scripts/
```

### Folder intent

| Folder | Purpose |
|---|---|
| `domain` | Core incident, telemetry, evidence, hypothesis, and report models. No LangGraph dependency. |
| `application` | Use-case services and deterministic investigation logic. |
| `graph` | LangGraph state, nodes, edges, routing, interrupts, and workflow composition. |
| `infrastructure` | LLM clients, vector store, telemetry readers, persistence, external adapters. |
| `api` | FastAPI or CLI entrypoints. |
| `evals` | Golden cases and evaluation runners. |
| `sample_data` | Synthetic logs, traces, metrics, deployment events, incident tickets. |
| `docs/adr` | Architecture decision records. |
| `docs/learning-notes` | Personal learning notes after each checkpoint. |

---

## 3. Journey rules

Codex must follow these rules during the journey:

1. Teach one concept at a time.
2. Implement one small vertical slice at a time.
3. Do not generate the full project prematurely.
4. Always explain concepts from a .NET/C# enterprise-engineering perspective.
5. Keep LLM calls behind interfaces/adapters.
6. Keep deterministic logic outside LLM prompts.
7. Prefer explicit state and typed models.
8. Add tests as soon as there is behavior worth testing.
9. Add evaluation cases before optimizing prompts.
10. Add observability before the system becomes complex.
11. Maintain a learning journal.
12. Use architecture decision records for meaningful tradeoffs.
13. Every phase must end with a checkpoint that can be marked complete.

---

## 4. Progress board

Codex should update this board as work progresses.

| Phase | Status | Completion date | Notes |
|---|---|---:|---|
| 1. Python project foundation | DONE | 2026-05-09 | Minimal package foundation, README, learning note, and import test added. |
| 2. LangGraph fundamentals | DONE | 2026-05-11 | Minimal graph, typed state, fixed edges, unit test, and learning note exist. |
| 3. Typed state and domain modeling | DONE | 2026-05-11 | Domain models, explicit graph state, validation tests, and ADR added. |
| 4. Control flow and conditional routing | DONE | 2026-05-11 | Deterministic routing function, conditional graph wiring, tests, and learning note exist. |
| 5. Tool abstraction and adapters | DONE | 2026-05-11 | Local telemetry tool protocols/adapters, typed evidence results, explicit file/malformed-data behavior, tests, and learning note exist. |
| 6. Deterministic telemetry parsing | DONE | 2026-05-14 | Deterministic parsers, filtering helpers, malformed-input tests, and one synthetic incident fixture exist. |
| 7. Evidence retrieval and citations | TODO |  |  |
| 8. Agentic hypothesis generation | TODO |  |  |
| 9. Critic / evidence validator | TODO |  |  |
| 10. Persistence, checkpointing, and interrupts | TODO |  |  |
| 11. Human-in-the-loop review | TODO |  |  |
| 12. Evaluation framework | TODO |  |  |
| 13. Observability and tracing | TODO |  |  |
| 14. API / CLI interface | TODO |  |  |
| 15. Portfolio skeleton hardening | TODO |  |  |
| 16. Final review and roadmap | TODO |  |  |

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
- `DeploymentEventTool`

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
- Deployment event records.
- Normalization.
- Error signatures.
- Time-window filtering.
- Correlation IDs.

## Implementation tasks

Create parsers for synthetic data:

- logs: timestamp, level, service, message, correlation ID, exception type.
- traces: trace ID, span ID, service, operation, duration, status.
- metrics: timestamp, service, metric name, value.
- deployments: timestamp, service, version, commit, change summary.

## Learning tasks

- Define what the LLM should not do.
- Write tests for parsing and filtering.
- Add one synthetic incident with known root cause.

## Checkpoint

- [x] Parsers exist.
- [x] Time-window filtering works.
- [x] Correlation ID filtering works.
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
retrieve deployments
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

- Implement simple keyword/time/correlation retrieval before vector search.
- Write “insufficient evidence” behavior.
- Add tests proving every evidence item has citation metadata.

## Checkpoint

- [ ] Evidence retrieval works.
- [ ] Evidence has source/citation metadata.
- [ ] Weak evidence is represented explicitly.
- [ ] Missing evidence does not crash graph.
- [ ] Tests validate citations.

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
- returns structured hypotheses,
- references evidence IDs,
- assigns preliminary confidence,
- states uncertainty.

Use an LLM adapter interface so the graph does not depend directly on a provider SDK.

## Learning tasks

- Define prompt contract.
- Add fake LLM for tests.
- Add guardrails:
  - hypothesis must cite evidence IDs,
  - hypothesis cannot cite missing evidence,
  - low evidence means low confidence.

## Checkpoint

- [ ] LLM adapter interface exists.
- [ ] Hypothesis node uses structured output.
- [ ] Fake LLM tests exist.
- [ ] Hypotheses cite evidence IDs.
- [ ] Weak evidence produces uncertainty.
- [ ] Learning note explains bounded LLM reasoning.

## Codex stop condition

Stop after bounded hypothesis generation.

---

# Phase 9 — Critic / evidence validator

## Goal

Add a reviewer step that challenges the generated hypotheses.

## Concepts

- Critic node.
- Evidence validation.
- Contradicting evidence.
- Confidence adjustment.
- Claim verification.
- Separation between generation and validation.
- Avoiding self-confirming agent loops.

## Implementation tasks

Create a `EvidenceValidatorNode` that checks:

- every hypothesis has supporting evidence,
- evidence actually relates to claim,
- contradicting signals are surfaced,
- confidence is adjusted,
- unsupported claims are downgraded or rejected.

Start deterministic where possible. Add LLM critic only after deterministic checks exist.

## Learning tasks

- Explain why critic should not be just “another agent vibes-checking.”
- Add tests for:
  - unsupported hypothesis,
  - contradicted hypothesis,
  - weak-but-plausible hypothesis,
  - strong evidence hypothesis.

## Checkpoint

- [ ] Validator node exists.
- [ ] Unsupported claims are rejected or downgraded.
- [ ] Contradicting evidence is represented.
- [ ] Confidence changes are explainable.
- [ ] Tests cover validation cases.
- [ ] Learning note explains generator/critic separation.

## Codex stop condition

Stop after critic/validator implementation.

---

# Phase 10 — Persistence, checkpointing, and interrupts

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

- [ ] Checkpointer is configured.
- [ ] Investigation run ID exists.
- [ ] State can be inspected.
- [ ] Simulated resume works.
- [ ] Interrupt point exists.
- [ ] ADR exists.

## Codex stop condition

Stop after durable execution demonstration.

---

# Phase 11 — Human-in-the-loop review

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
- validator finds contradictions.

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

- [ ] Human review condition exists.
- [ ] Interrupt/resume path works.
- [ ] Approval decision is stored.
- [ ] Rejection path is explicit.
- [ ] Tests cover review routing.
- [ ] Learning note exists.

## Codex stop condition

Stop after human review flow.

---

# Phase 12 — Evaluation framework

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

- database timeout after deployment,
- auth failures after config change,
- latency spike caused by downstream dependency,
- flaky metric anomaly,
- insufficient evidence case.

For each case define:

- expected category,
- expected evidence sources,
- acceptable hypotheses,
- forbidden unsupported claims,
- expected escalation behavior.

## Learning tasks

- Build simple eval runner.
- Add scoring dimensions.
- Track pass/fail over time.
- Write ADR: “Evaluation before prompt optimization.”

## Checkpoint

- [ ] At least five eval cases exist.
- [ ] Eval runner exists.
- [ ] Citation correctness is scored.
- [ ] Unsupported claims are detected.
- [ ] Results are reproducible.
- [ ] ADR exists.

## Codex stop condition

Stop after basic evaluation loop.

---

# Phase 13 — Observability and tracing

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
- Correlation IDs.
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
- [ ] Graph run has correlation ID.
- [ ] Nodes emit useful telemetry.
- [ ] Tool failures are observable.
- [ ] LLM calls are traceable through adapter.
- [ ] Learning note exists.

## Codex stop condition

Stop after local observability demonstration.

---

# Phase 14 — API / CLI interface

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

# Phase 15 — Portfolio skeleton hardening

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

# Phase 16 — Final review and roadmap

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

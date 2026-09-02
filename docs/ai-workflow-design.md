# AI Workflow Design

## Why This Is Not A Generic Chatbot

The system is designed around a controlled workflow, not an open-ended chat
interface. A chatbot-style design would make it too easy for the model to blend
retrieval, interpretation, citation, and reporting into one opaque answer.

This project separates those responsibilities:

- deterministic code retrieves and scores evidence;
- the LLM proposes structured candidate hypotheses;
- deterministic validation checks evidence references;
- a critic reviews semantic risk;
- deterministic policy decides whether human review is required;
- final reports are assembled from accepted reviewed hypotheses.

The result is easier to test, debug, explain, and evaluate.

## Why Not Delegate Everything To The LLM

LLMs are useful for interpreting evidence and producing structured hypotheses,
but they should not own the whole investigation. Deterministic code is better
for tasks that require repeatability and direct verification:

- parsing telemetry formats;
- filtering by time window and service;
- matching trace IDs;
- preserving source files and line numbers;
- validating IDs;
- enforcing confidence caps;
- routing to human review;
- scoring eval cases.

If those behaviors lived inside prompts, a reviewer would have to trust model
behavior instead of inspecting code and tests.

## What The LLM Is Allowed To Do

The provider boundary allows two workflow actions:

1. Generate candidate hypotheses from supplied incident and evidence context.
2. Critique validated hypotheses for semantic concerns.

The generator must return structured `InvestigationHypothesis` objects. It must
cite evidence IDs from the supplied context and include uncertainty for
low-confidence hypotheses.

The critic must return structured critique findings. It can identify
contradictions, unsupported causal leaps, alternative interpretations, and
overstated confidence. It does not route the graph, rewrite hypotheses, or build
the final report.

## What Deterministic Code Owns

Deterministic code owns:

- local telemetry parsing;
- evidence retrieval and ranking;
- citation metadata;
- evidence strength;
- missing-evidence representation;
- hypothesis reference validation;
- confidence adjustment;
- mapping critique findings to accepted/disputed/blocked statuses;
- human review routing;
- final report construction;
- eval scoring.

This keeps the main risk-control behavior inspectable in normal Python modules.

## How Unsupported Conclusions Are Reduced

The project reduces unsupported conclusions through several layers:

1. The LLM receives retrieved evidence, not raw files.
2. Evidence has stable IDs and citations.
3. Hypotheses must cite evidence IDs.
4. The validator rejects missing citations and unknown evidence IDs.
5. Missing evidence cannot support a hypothesis.
6. Confidence is capped when evidence strength is limited.
7. The semantic critic can flag unsupported causal leaps.
8. Deterministic review policy can block, dispute, or escalate hypotheses.
9. Evaluation checks accepted hypotheses for unsupported claims.

This does not eliminate all model risk. It makes the risk visible and creates
places to test and improve the workflow.

## Human-In-The-Loop Strategy

Human review is a risk-control mechanism. It is required when the workflow should
not automatically finalize a report:

- evidence is weak or missing;
- no validated hypothesis exists;
- the accepted hypothesis says the cause is uncertain or insufficiently
  evidenced;
- the top reviewed hypothesis is disputed or blocked;
- competing explanations are too close;
- warnings are present;
- incident impact is high.

The review gate is implemented through LangGraph interrupt/resume and SQLite
checkpointing. A reviewer can approve or reject the paused workflow.

## Tradeoffs

The controlled design has more code than a single prompt-based workflow, but the
extra structure creates clear ownership:

- retrieval quality can be tested without the LLM;
- model behavior can be evaluated against stable cases;
- review routing is explainable;
- reports are tied to evidence IDs;
- failures are easier to diagnose.

The tradeoff is that the workflow is narrower than a general chatbot. It handles
predefined synthetic cases and known telemetry formats so evidence boundaries,
evaluation, and review policy remain explicit and inspectable.

## Current Limits

- Synthetic telemetry only.
- Small evaluation suite.
- No real observability integrations.
- No arbitrary incident upload.
- No production security or deployment layer.
- Semantic review still depends on provider-backed model behavior in live evals.

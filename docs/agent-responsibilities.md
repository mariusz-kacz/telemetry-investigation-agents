# Agent And Control Responsibilities

## Purpose

This document explains what each investigation step does, how it contributes to
the overall incident investigation, and what it verifies.

The project uses the word "agent" carefully. Only the hypothesis generator and
semantic critic are LLM-backed reasoning steps. The other steps are
deterministic controls around evidence, policy, routing, reporting, and
evaluation.

## Responsibility Map

| Step | Implementation | Role in investigation | What it verifies |
|---|---|---|---|
| Evidence retrieval | `telemetry_agents.investigation.evidence_retrieval.retrieve_evidence` | Finds relevant log, trace, and metric evidence before the graph starts. Produces ranked evidence with citations and strength labels. | Verifies telemetry can be read, records match the incident service/time window/query terms/trace IDs, citations point to source files and line numbers when available, and missing files or empty matches are represented as missing evidence rather than ignored. |
| Hypothesis generator | `hypothesis_generation` graph node through `HypothesisGenerator` | Proposes candidate root-cause hypotheses from the incident and retrieved evidence. This is candidate state, not trusted output. | Does not verify truth. It is constrained to structured `InvestigationHypothesis` output and asked to cite supplied evidence IDs, but downstream validation decides whether those references are usable. If unavailable, the graph records a warning and continues with no generated hypotheses. |
| Evidence validator | `hypothesis_validation` graph node through `validate_hypotheses` | Converts raw generated hypotheses into evidence-reviewed hypotheses. This is the main deterministic trust boundary after generation. | Verifies every hypothesis has supporting evidence IDs, cited IDs exist, missing evidence is not used as support, and confidence does not exceed what cited evidence strength can support. It records rejected hypotheses and confidence adjustments. |
| Semantic critic | `hypothesis_critic` graph node through `HypothesisCritic` | Reviews validated hypotheses for semantic risks that deterministic code should not pretend to understand. | Checks for structured critique findings such as contradictions, unsupported causal leaps, alternative interpretations, and overstated confidence. Guardrails verify critic findings reference known validated hypothesis IDs, known evidence IDs, and do not cite missing evidence. The critic does not rewrite hypotheses, change confidence, route the graph, or build reports. |
| Hypothesis review policy | `hypothesis_review` graph node through `review_hypotheses` | Turns critic findings into workflow usability status for each validated hypothesis. | Deterministically maps contradictions and unsupported causal leaps to `blocked`, alternative interpretations and overstated confidence to `disputed`, and hypotheses with no findings to `accepted`. It verifies policy precedence, not semantic truth. |
| Human-review assessment | `human_review_assessment` graph node through `assess_human_review_requirement` | Decides whether the workflow may finalize automatically or must pause for human review. | Verifies risk conditions: high incident impact, weak or missing evidence, no validated hypotheses, insufficient-evidence or uncertain-root-cause accepted outcomes, blocked/disputed top hypotheses, no accepted hypothesis, close competing blocked/disputed alternatives, and warnings. |
| Review gate | `report_review_gate` graph node | Pauses the graph when human review is required and resumes after approval or rejection. | Verifies the paused state has the incident, validation result, critique findings, evidence, assessment, and warnings needed to build a review packet. On resume, it verifies the reviewer supplied an `approved` decision. |
| Report builder | `final_report_builder` graph node through `build_investigation_report` | Produces the final cited report from accepted reviewed hypotheses. | Selects the highest-confidence accepted hypothesis and maps its evidence IDs back to retrieved evidence citations. It verifies referenced evidence IDs still exist before writing report citations. If no accepted hypothesis exists, it produces an explicit no-accepted-hypothesis report instead of inventing a conclusion. |
| Report status markers | `human_review_not_required_marker`, `report_ready_marker`, `report_rejected_marker` | Record workflow status after review routing or resume. | Verify and persist status transitions such as not-required, ready, or rejected. They do not perform evidence or semantic review. |
| Unsupported-claim reviewer | `telemetry_agents.evaluation.unsupported_claim_review` | Runs after workflow execution as part of evaluation. It checks whether unsupported semantic claims escaped the runtime controls. | Reviews accepted hypotheses only. Guardrails verify reviewer findings reference known accepted hypothesis IDs, known evidence IDs, and do not cite missing evidence. It does not mutate graph state, affect routing, or replace the workflow critic. |

## Investigation Flow

The system intentionally separates proposal, validation, critique, policy, and
evaluation:

```text
evidence retrieval
  -> hypothesis generation
  -> deterministic evidence validation
  -> semantic critique
  -> deterministic hypothesis review policy
  -> human-review assessment
  -> final report or review interrupt
  -> post-run evaluation
```

This structure prevents a common failure mode in AI investigation systems: a
model produces a polished explanation, and the rest of the system merely
displays it. Here, each step has a narrower responsibility and a different kind
of verification.

## What Each Verification Layer Catches

Evidence retrieval catches missing or irrelevant telemetry inputs before the LLM
sees context.

Evidence validation catches structural citation failures: no evidence, unknown
evidence IDs, missing evidence used as support, and confidence that is too high
for the available evidence strength.

The semantic critic catches reasoning risks that are hard to encode as simple
deterministic checks, such as unsupported causal leaps or contradictions.

The hypothesis review policy turns critic observations into deterministic
workflow status. The LLM reports findings; Python policy decides whether a
hypothesis is accepted, disputed, or blocked.

Human-review assessment catches situations where automation should not finalize
a report even if some hypothesis is technically accepted.

The unsupported-claim reviewer catches evaluation regressions: accepted outputs
that still contain claims not supported by the retrieved evidence.

## Boundaries

The workflow critic and unsupported-claim reviewer are intentionally separate.
The critic is a runtime control inside graph execution. The unsupported-claim
reviewer is a post-run evaluation control that checks whether runtime controls
were sufficient.

The API and UI do not act as investigation agents. They expose and present
workflow results through DTOs, including run status, hypotheses, evidence
citations, review reasons, and final report state.

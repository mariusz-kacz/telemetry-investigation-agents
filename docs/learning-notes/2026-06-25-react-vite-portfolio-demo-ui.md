# Session: React/Vite portfolio demo UI

## Goal

Add a polished visual demo surface for the FastAPI investigation interface
without coupling the frontend to LangGraph internals.

## What I built

Phase 16.5 added a React/Vite dashboard that can:

- list predefined demo cases;
- start a demo investigation;
- show the selected incident, top hypothesis, confidence, evidence citations,
  hypothesis review status, and human-review gate;
- approve or reject a run only while the backend status is `awaiting_review`;
- list past runs from a registry-backed API endpoint;
- reload completed or rejected run outcomes without rerunning the workflow.

The backend also gained a lightweight run-summary endpoint:

```text
GET /api/v1/investigations
```

The UI uses that endpoint for dashboard history and the existing detail endpoint
for full run outcomes:

```text
GET /api/v1/investigations/{run_id}
```

## LangGraph concept learned

The UI should not know that LangGraph exists. LangGraph remains an orchestration
detail behind the application service and API contract.

The important boundary is:

```text
React UI
  -> FastAPI DTOs
  -> application service
  -> LangGraph workflow / registry / checkpoints
```

This keeps workflow state, checkpoints, and interrupt/resume mechanics out of
the browser.

## Mapping to .NET/C# thinking

The frontend consumes a public API contract, similar to a SPA consuming
controller DTOs in an ASP.NET application. The Python project keeps the same
boundary without adding heavy view-model factories or enterprise-style mapping
layers where simple route mapping is enough.

The run-history endpoint is a read model over the run registry. It is not a
workflow query that reconstructs every checkpoint.

## What confused me

`human_review_required` describes whether the workflow policy required review.
It does not mean the run is still resumable. The approve/reject buttons should
only be enabled when the current run status is `awaiting_review`.

After a review decision, the run can be `completed` or `rejected`; repeated
review submissions should be blocked by the UI and rejected by the backend.

## Tradeoffs noticed

React/Vite adds a Node-based frontend toolchain, but it gives the portfolio a
better presentation surface than static HTML.

The UI intentionally stays thin:

- no direct SQLite access;
- no checkpoint reads;
- no graph-state rendering;
- no arbitrary incident upload;
- no dynamic workflow builder.

The past-runs dashboard uses registry summaries because it is cheap and stable.
Full investigation details are loaded only when a user selects a run.

## Production concerns

A real production UI would likely need background execution, polling or
WebSockets, authentication, authorization, pagination, timestamps, and clearer
error recovery.

Those are intentionally outside this learning checkpoint. The current UI is a
portfolio demo over synthetic cases, not a production incident-ingestion portal.

## Tests/evals added

Verification included:

- Vite TypeScript production build;
- FastAPI route tests for investigation start/read/review;
- run-registry tests;
- route coverage for the run-history API response shape and lowercase status
  mapping.

## Next step

Return to Phase 17: portfolio skeleton hardening. The UI now provides the visual
demo surface for the README walkthrough, sample output, architecture diagram,
and honest limitations section.

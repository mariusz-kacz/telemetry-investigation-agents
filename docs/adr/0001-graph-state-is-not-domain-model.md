# ADR 0001: Graph state is not the domain model

## Status

Proposed

## Context

The core incident investigation model should be testable without LangGraph. The project needs stable domain objects for incidents, telemetry evidence, hypotheses, and reports. LangGraph state is used to orchestrate workflow execution between nodes, so it should not become the only place where domain concepts are defined.

## Decision

Domain models will represent stable investigation concepts: Incident, EvidenceSource, TelemetryEvidence, InvestigationHypothesis, and InvestigationReport.

Graph state may reference domain models, but it also contains workflow-only fields such as the raw incident input, errors, warnings, intermediate findings, hypotheses being evaluated, and validation results.

Domain models must not depend on LangGraph.

## Consequences

This creates more classes to maintain, but it gives the project clearer separation and better testability.

Domain models can be validated without running a graph. Graph nodes can focus on orchestration and state transitions instead of owning the entire application model.

## Alternatives considered

One alternative was to use a single graph state dictionary for both workflow state and domain concepts. This was rejected because it would couple tests and domain validation to LangGraph execution.

Another alternative was to put most behavior directly inside graph nodes. This was rejected because it would make deterministic business rules harder to test independently.

## Why this matters for Telemetry Investigation Agents

Evidence, hypotheses, validation, and reports need to be reliable and explainable. Keeping them as domain models makes them testable outside LangGraph and keeps LangGraph focused on workflow orchestration.
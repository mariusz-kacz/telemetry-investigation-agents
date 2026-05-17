# Telemetry Investigation Agents

Telemetry Investigation Agents is a learning-oriented portfolio project for building a production-minded LangGraph investigation workflow.

The target system will analyze synthetic enterprise telemetry such as logs, traces, metrics, and incident tickets. It will produce cited investigation reports with suspected root causes, supporting and contradicting evidence, confidence levels, explicit uncertainty, and recommended next actions.

The project is intentionally incremental. The foundation starts as a small Python package with tests and clear boundaries. LangGraph, telemetry adapters, LLM-backed hypothesis generation, validation, persistence, human review, evaluations, and observability will be added only when the learning checkpoints call for them.

## Engineering Thesis

LangGraph should orchestrate workflow state and transitions. Deterministic parsing, validation, telemetry access, and domain behavior should remain in normal Python modules that are easy to test without an LLM.

This mirrors the useful part of enterprise layering without copying its ceremony: the graph is the orchestration layer, domain models stay framework-independent, telemetry modules own parsing and local readers, and investigation modules hold deterministic retrieval, matching, and scoring logic.

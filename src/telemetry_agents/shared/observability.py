import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any
from uuid import uuid4


LOGGER_NAME = "telemetry_agents.observability"
EVENT_NODE_STARTED = "graph.node.started"
EVENT_NODE_COMPLETED = "graph.node.completed"
EVENT_NODE_FAILED = "graph.node.failed"
EVENT_LLM_CALL_STARTED = "llm.call.started"
EVENT_LLM_CALL_COMPLETED = "llm.call.completed"
EVENT_LLM_CALL_FAILED = "llm.call.failed"
EVENT_EVIDENCE_RETRIEVAL_COMPLETED = "evidence.retrieval.completed"
EVENT_TELEMETRY_SOURCE_UNAVAILABLE = "telemetry.source.unavailable"
EVENT_HYPOTHESIS_VALIDATION_CONFIDENCE_ADJUSTED = (
    "hypothesis.validation.confidence_adjusted"
)
EVENT_HYPOTHESIS_VALIDATION_REJECTED = "hypothesis.validation.rejected"
EVENT_HYPOTHESIS_CRITIC_FALLBACK = "hypothesis.critic.fallback"
EVENT_HYPOTHESIS_CRITIC_COMPLETED = "hypothesis.critic.completed"
EVENT_HYPOTHESIS_REVIEW_COMPLETED = "hypothesis.review.completed"
EVENT_HUMAN_REVIEW_ROUTING_DECIDED = "human_review.routing_decided"
EVENT_EVAL_CASE_SCORED = "eval.case.scored"

logger = logging.getLogger(LOGGER_NAME)


def new_run_id() -> str:
    """Create an opaque workflow execution ID."""
    return str(uuid4())


def emit_event(event_name: str, **fields: Any) -> None:
    """Emit a machine-readable observability event.

    Keep the public shape small: event name plus flat JSON fields. This makes
    tests and local demos straightforward without committing to a vendor backend.
    """
    event = {"event": event_name, **fields}
    logger.info(json.dumps(event, sort_keys=True, default=str))


class LlmCallObservation:
    def __init__(self, *, started_at: float, fields: dict[str, Any]) -> None:
        self._started_at = started_at
        self._fields = fields
        self._ended = False

    def complete(self, **completion_fields: Any) -> None:
        event_fields = {
            **self._fields,
            **completion_fields,
            "duration_ms": round((perf_counter() - self._started_at) * 1000, 3),
        }
        emit_event(EVENT_LLM_CALL_COMPLETED, **event_fields)
        self._ended = True

    def fail(self, exc: Exception) -> None:
        emit_event(
            EVENT_LLM_CALL_FAILED,
            **self._fields,
            duration_ms=round((perf_counter() - self._started_at) * 1000, 3),
            error_type=type(exc).__name__,
        )
        self._ended = True


@contextmanager
def observe_llm_call(**fields: Any) -> Iterator[LlmCallObservation]:
    """Emit start/end events for one provider-backed LLM call.

    Callers should pass only safe metadata. Prompts, raw responses, evidence
    payloads, hypothesis statements, and critic reasons do not belong here.
    """
    started_at = perf_counter()
    emit_event(EVENT_LLM_CALL_STARTED, **fields)
    observation = LlmCallObservation(started_at=started_at, fields=fields)
    try:
        yield observation
    except Exception as exc:
        if not observation._ended:
            observation.fail(exc)
        raise

    if not observation._ended:
        exc = RuntimeError("LLM call didn't complete successfully")
        observation.fail(exc)
        raise exc

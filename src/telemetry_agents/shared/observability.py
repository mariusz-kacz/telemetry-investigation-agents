import json
import logging
from typing import Any
from uuid import uuid4


LOGGER_NAME = "telemetry_agents.observability"
EVENT_NODE_STARTED = "graph.node.started"
EVENT_NODE_COMPLETED = "graph.node.completed"
EVENT_NODE_FAILED = "graph.node.failed"
EVENT_EVIDENCE_RETRIEVAL_COMPLETED = "evidence.retrieval.completed"
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

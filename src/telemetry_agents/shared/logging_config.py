import logging
import sys

from telemetry_agents.shared.observability import LOGGER_NAME

_CONFIGURED = False


def configure_observability_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)

    if not any(
        getattr(handler, "_telemetry_agents_handler", False)
        for handler in logger.handlers
    ):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        handler.setLevel(logging.INFO)
        handler._telemetry_agents_handler = True
        logger.addHandler(handler)

    _CONFIGURED = True

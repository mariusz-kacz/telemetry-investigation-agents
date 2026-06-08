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
    logger.propagate = False

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    _CONFIGURED = True

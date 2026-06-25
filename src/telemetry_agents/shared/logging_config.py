import logging
import sys

from telemetry_agents.shared.observability import LOGGER_NAME

_CONFIGURED = False


class _TelemetryAgentsStreamHandler(logging.StreamHandler):
    pass


def configure_observability_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)

    if not any(
        isinstance(handler, _TelemetryAgentsStreamHandler)
        for handler in logger.handlers
    ):
        handler = _TelemetryAgentsStreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)

    _CONFIGURED = True

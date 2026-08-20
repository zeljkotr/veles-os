"""
VELES OS Core Events.

Central event logging interface for the VELES Core layer.

All Core components should use this subsystem for recording
important runtime events.
"""

import json
import logging
from datetime import datetime, timezone


_logger = logging.getLogger("veles.core.events")


if not _logger.handlers:

    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "[VELES EVENT] %(message)s"
    )

    handler.setFormatter(formatter)

    _logger.addHandler(handler)

    _logger.setLevel(logging.INFO)


def log_event(event_type, data=None):
    """
    Record a VELES Core event.

    Parameters
    ----------
    event_type:
        Short identifier describing the event.

    data:
        Optional dictionary containing event details.

    Returns
    -------
    dict
        The normalized event record.
    """

    event = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "event": str(event_type),

        "data": data if isinstance(data, dict) else {}
    }

    _logger.info(
        json.dumps(
            event,
            ensure_ascii=False,
            default=str
        )
    )

    return event
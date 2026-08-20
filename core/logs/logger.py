"""
VELES Core Logging.

Simple append-only event log in JSON Lines format.
"""

import datetime
import json
from pathlib import Path


LOG_FILE = Path(__file__).parent / "veles.log"


def log_event(event_type: str, details: dict) -> None:
    entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        **details,
    }

    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(
            json.dumps(
                entry,
                ensure_ascii=False
            ) + "\n"
        )

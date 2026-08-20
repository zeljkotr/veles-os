"""
VELES OS Core Runtime

Coordinates the existing VELES Core subsystems.
"""

from core.database.connection import test_connection
from core.events import log_event


class CoreRuntime:
    """Runtime coordinator for the VELES Core layer."""

    def __init__(self):
        self.database = None
        self.ready = False

    def start(self):
        """Initialize the VELES Core."""

        print("[CORE] Initializing VELES Core...")

        # ----------------------------------
        # DATABASE
        # ----------------------------------

        database_result = test_connection()

        if database_result is None:
            print("[CORE] Database: OFFLINE")
        else:
            self.database = {
                "status": "ready"
            }

            print("[CORE] Database: READY")

        # ----------------------------------
        # EVENTS
        # ----------------------------------

        try:
            log_event(
                "core.started",
                {
                    "database": (
                        "ready"
                        if self.database is not None
                        else "offline"
                    )
                }
            )

            print("[CORE] Events: READY")

        except Exception as error:
            print(
                "[CORE] Events: OFFLINE"
            )
            print(
                "[CORE] Event system error:",
                error
            )

        # ----------------------------------
        # CORE STATE
        # ----------------------------------

        self.ready = True

        print("[CORE] VELES Core: READY")

        return self

    def stop(self):
        """Stop the VELES Core."""

        if not self.ready:
            return

        print("[CORE] Stopping VELES Core...")

        try:
            log_event("core.stopped")
        except Exception:
            pass

        self.ready = False
        self.database = None

        print("[CORE] VELES Core: OFFLINE")
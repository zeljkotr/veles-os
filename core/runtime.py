"""
VELES OS Core Runtime

Coordinates the existing VELES Core subsystems
and the VELES OS module registry.
"""

from core.database.connection import test_connection
from core.events import log_event
from core.modules.registry import ModuleRegistry


class CoreRuntime:
    """Runtime coordinator for the VELES Core layer."""

    def __init__(self):
        self.database = None
        self.registry = ModuleRegistry()
        self.ready = False

    def start(self):
        """Initialize the VELES Core."""

        print("[CORE] Initializing VELES Core...")

        # ----------------------------------
        # DATABASE
        # ----------------------------------

        try:
            database_result = test_connection()

            if database_result is None:
                print("[CORE] Database: OFFLINE")
            else:
                self.database = {
                    "status": "ready"
                }

                print("[CORE] Database: READY")

        except Exception as error:
            print("[CORE] Database: OFFLINE")
            print("[CORE] Database error:", error)

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
            print("[CORE] Events: OFFLINE")
            print("[CORE] Event system error:", error)

        # ----------------------------------
        # MODULE REGISTRY
        # ----------------------------------

        self.registry = ModuleRegistry()

        print("[CORE] Module Registry: READY")

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

        # ----------------------------------
        # MODULE REGISTRY
        # ----------------------------------

        try:
            self.registry.stop_all()
        except Exception:
            pass

        # ----------------------------------
        # EVENTS
        # ----------------------------------

        try:
            log_event("core.stopped")
        except Exception:
            pass

        self.ready = False
        self.database = None

        print("[CORE] VELES Core: OFFLINE")
"""
VELES OS Kernel Runtime

Coordinates the complete VELES OS runtime lifecycle.
"""

import threading

from boot.bootstrap import bootstrap


class VelesRuntime:
    """Coordinates the complete VELES OS runtime lifecycle."""

    def __init__(self):
        self.system = None
        self.core = None
        self.services = None
        self.desktop = None

        self.running = False
        self._stop_event = threading.Event()

    def start(self):
        """Start the complete VELES OS runtime."""

        if self.running:
            return self

        print("[KERNEL] Starting VELES runtime...")

        state = bootstrap()

        self.system = state.get("system_layer")
        self.core = state.get("core")
        self.services = state.get("services")
        self.desktop = state.get("desktop")

        self.running = True
        self._stop_event.clear()

        print("[KERNEL] VELES runtime is ONLINE.")

        return self

    def wait(self):
        """
        Keep the VELES OS runtime alive until shutdown.
        """

        if not self.running:
            return

        try:
            self._stop_event.wait()

        except KeyboardInterrupt:
            raise

    def stop(self):
        """Stop the complete VELES OS runtime."""

        if not self.running:
            return

        print("[KERNEL] Stopping VELES runtime...")

        self._stop_event.set()

        # --------------------------------------
        # DESKTOP
        # --------------------------------------

        if self.desktop:
            self.desktop.stop()

        self.desktop = None

        # --------------------------------------
        # SERVICES
        # --------------------------------------

        if self.services:
            self.services.stop()

        self.services = None

        # --------------------------------------
        # CORE
        # --------------------------------------

        if self.core:
            self.core.stop()

        self.core = None

        # --------------------------------------
        # SYSTEM
        # --------------------------------------

        if self.system:
            self.system.stop()

        self.system = None

        # --------------------------------------
        # KERNEL STATE
        # --------------------------------------

        self.running = False

        print("[KERNEL] VELES runtime is OFFLINE.")
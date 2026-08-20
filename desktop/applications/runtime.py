"""
VELES OS Application Runtime

Provides application lifecycle management through
the VELES Application Registry.
"""

from desktop.applications.registry import ApplicationRegistry


class ApplicationRuntime:

    def __init__(self):
        self.registry = ApplicationRegistry()

        self.state = "offline"
        self.ready = False

    def start(self):

        if self.ready:
            return self

        print("[APPLICATIONS] Initializing Application Runtime...")

        self.state = "starting"

        self.registry.start()

        self.state = "online"
        self.ready = True

        print("[APPLICATIONS] Application Runtime: READY")

        return self

    def register(self, name, application):

        if not self.ready:
            raise RuntimeError(
                "Application Runtime is not running."
            )

        return self.registry.register(
            name,
            application,
        )

    def unregister(self, name):

        if not self.ready:
            raise RuntimeError(
                "Application Runtime is not running."
            )

        return self.registry.unregister(name)

    def get(self, name):

        if not self.ready:
            raise RuntimeError(
                "Application Runtime is not running."
            )

        return self.registry.get(name)

    def list(self):

        if not self.ready:
            raise RuntimeError(
                "Application Runtime is not running."
            )

        return self.registry.list()

    def status(self):

        return {
            "state": self.state,
            "ready": self.ready,
            "registry": self.registry.status(),
            "applications": (
                self.registry.list()
                if self.ready
                else {}
            ),
        }

    def stop(self):

        if not self.ready:
            return

        print("[APPLICATIONS] Stopping Application Runtime...")

        self.state = "stopping"

        self.registry.stop()

        self.ready = False
        self.state = "offline"

        print("[APPLICATIONS] Application Runtime: OFFLINE")
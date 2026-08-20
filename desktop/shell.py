"""
VELES OS Desktop Shell

Central UI shell for VELES Desktop.
"""


class DesktopShell:

    def __init__(self, runtime):
        self.runtime = runtime
        self.active_view = "dashboard"
        self.running = False

        self.views = [
            "dashboard",
            "operations",
            "infrastructure",
            "monitoring",
            "network",
            "security",
            "delivery",
            "intelligence",
            "terminal",
            "services",
            "system",
        ]

    def start(self):

        if self.running:
            return self

        self.running = True
        self.active_view = "dashboard"

        print("[SHELL] VELES Desktop Shell: READY")
        print("[SHELL] Active view: Dashboard")

        return self

    def navigate(self, view):

        if view not in self.views:
            raise ValueError(
                f"Unknown Desktop view: {view}"
            )

        self.active_view = view

        print(
            f"[SHELL] Active view: "
            f"{view.replace('_', ' ').title()}"
        )

        return self.active_view

    def status(self):

        return {
            "running": self.running,
            "active_view": self.active_view,
            "views": self.views,
        }

    def stop(self):

        if not self.running:
            return

        print("[SHELL] Stopping VELES Desktop Shell...")

        self.running = False
        self.active_view = "dashboard"

        print("[SHELL] VELES Desktop Shell: OFFLINE")
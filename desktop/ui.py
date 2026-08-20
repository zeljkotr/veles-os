"""
VELES OS Desktop UI

Connects the VELES Desktop UI with the
VELES Desktop Shell.
"""


class DesktopUI:

    def __init__(self, shell):
        self.shell = shell
        self.running = False

    def start(self):

        if self.running:
            return self

        print("[UI] Initializing VELES Desktop UI...")

        self.running = True

        print("[UI] VELES Desktop UI: READY")

        return self

    def open(self, view="dashboard"):

        if not self.running:
            raise RuntimeError(
                "VELES Desktop UI is not running."
            )

        self.shell.navigate(view)

        return {
            "view": view,
            "status": "open",
        }

    def status(self):

        return {
            "running": self.running,
            "application": "VELES Desktop UI",
            "active_view": self.shell.active_view,
        }

    def stop(self):

        if not self.running:
            return

        print("[UI] Stopping VELES Desktop UI...")

        self.running = False

        print("[UI] VELES Desktop UI: OFFLINE")

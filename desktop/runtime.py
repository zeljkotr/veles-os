"""
VELES OS Desktop Runtime

Owns the VELES Desktop lifecycle and coordinates
the Desktop Shell, UI, Window Manager, Applications,
and Desktop Web Interface.
"""

from desktop.shell import DesktopShell
from desktop.ui import DesktopUI
from desktop.web_init import start_web, wait_for_web
from desktop.applications.runtime import ApplicationRuntime
from desktop.window.manager import WindowManager


class DesktopRuntime:

    def __init__(self, system=None, core=None, services=None):
        self.system = system
        self.core = core
        self.services = services

        self.dashboard = None
        self.shell = None
        self.ui = None

        self.application_runtime = ApplicationRuntime()
        self.window_manager = WindowManager()

        self.state = "offline"
        self.ready = False

        self.web_thread = None
        self.web_ready = False

    def start(self):

        if self.ready:
            return self

        print("[DESKTOP] Initializing VELES Desktop...")

        self.state = "starting"

        try:

            # --------------------------------------
            # DASHBOARD
            # --------------------------------------

            self.dashboard = {
                "name": "VELES Dashboard",
                "status": "ready",
            }

            print("[DESKTOP] Dashboard: READY")

            # --------------------------------------
            # DESKTOP SHELL
            # --------------------------------------

            self.shell = DesktopShell(self)
            self.shell.start()

            if not self.shell.running:
                raise RuntimeError(
                    "Desktop Shell failed to start."
                )

            print("[DESKTOP] Shell: READY")

            # --------------------------------------
            # DESKTOP UI
            # --------------------------------------

            self.ui = DesktopUI(self.shell)
            self.ui.start()

            if not self.ui.running:
                raise RuntimeError(
                    "Desktop UI failed to start."
                )

            print("[DESKTOP] UI: READY")

            # --------------------------------------
            # WINDOW MANAGER
            # --------------------------------------

            self.window_manager.start()

            if not self.window_manager.ready:
                raise RuntimeError(
                    "Window Manager failed to start."
                )

            print("[DESKTOP] Window Manager: READY")

            # --------------------------------------
            # APPLICATION RUNTIME
            # --------------------------------------

            self.application_runtime.start()

            if not self.application_runtime.ready:
                raise RuntimeError(
                    "Application Runtime failed to start."
                )

            self._register_applications()

            print("[DESKTOP] Application Runtime: READY")

            # --------------------------------------
            # DESKTOP WEB
            # --------------------------------------

            self.web_thread = start_web()

            self.web_ready = wait_for_web(
                self.web_thread
            )

            if not self.web_ready:
                raise RuntimeError(
                    "Desktop Web Interface failed readiness check."
                )

            print("[DESKTOP] Web Interface: READY")

            # --------------------------------------
            # DESKTOP READY
            # --------------------------------------

            self.state = "online"
            self.ready = True

            print("[DESKTOP] VELES Desktop: READY")

            return self

        except Exception:

            self.state = "failed"
            self.ready = False

            self._cleanup()

            raise

    def _register_applications(self):

        applications = {
            "dashboard": {
                "name": "Dashboard",
                "status": "ready",
            },
            "operations": {
                "name": "Operations Center",
                "status": "available",
            },
            "infrastructure": {
                "name": "Infrastructure",
                "status": "available",
            },
            "monitoring": {
                "name": "Monitoring",
                "status": "available",
            },
            "network": {
                "name": "Network",
                "status": "available",
            },
            "security": {
                "name": "Security",
                "status": "available",
            },
            "delivery": {
                "name": "Delivery",
                "status": "available",
            },
            "intelligence": {
                "name": "Intelligence",
                "status": "available",
            },
            "terminal": {
                "name": "Terminal",
                "status": "available",
            },
            "services": {
                "name": "Services",
                "status": "available",
            },
            "system": {
                "name": "System",
                "status": "available",
            },
        }

        for name, application in applications.items():
            self.application_runtime.register(
                name,
                application,
            )

    def status(self):

        return {
            "state": self.state,
            "ready": self.ready,
            "dashboard": self.dashboard,
            "shell": (
                self.shell.status()
                if self.shell
                else None
            ),
            "ui": (
                self.ui.status()
                if self.ui
                else None
            ),
            "applications": self.application_runtime.list(),
            "application_runtime": (
                self.application_runtime.status()
            ),
            "window_manager": (
                self.window_manager.status()
            ),
            "web": {
                "thread_alive": (
                    self.web_thread.is_alive()
                    if self.web_thread
                    else False
                ),
                "ready": self.web_ready,
            },
        }

    def get_application(self, name):

        return self.application_runtime.get(name)

    def stop(self):

        if (
            not self.ready
            and self.state != "starting"
        ):
            return

        print("[DESKTOP] Stopping VELES Desktop...")

        self.state = "stopping"

        self._cleanup()

        self.ready = False
        self.state = "offline"

        print("[DESKTOP] VELES Desktop: OFFLINE")

    def _cleanup(self):

        # --------------------------------------
        # DESKTOP UI
        # --------------------------------------

        if self.ui:
            self.ui.stop()

        self.ui = None

        # --------------------------------------
        # DESKTOP SHELL
        # --------------------------------------

        if self.shell:
            self.shell.stop()

        self.shell = None

        # --------------------------------------
        # WINDOW MANAGER
        # --------------------------------------

        self.window_manager.stop()

        # --------------------------------------
        # APPLICATION RUNTIME
        # --------------------------------------

        self.application_runtime.stop()

        # --------------------------------------
        # DESKTOP STATE
        # --------------------------------------

        self.dashboard = None
        self.web_thread = None
        self.web_ready = False
"""
VELES OS Desktop Runtime

Owns the VELES Desktop lifecycle and coordinates:

    Application Runtime
    Window Manager
    Desktop Shell
    Desktop UI
    Desktop Web Interface

The Desktop Runtime does not own the lifecycle of:

    System Layer
    VELES Core
    VELES Services

Those layers are provided by the VELES OS bootstrap/runtime.
"""

from desktop.applications.runtime import ApplicationRuntime
from desktop.shell import DesktopShell
from desktop.ui import DesktopUI
from desktop.web_init import start_web, wait_for_web
from desktop.window.manager import WindowManager


class DesktopRuntime:
    """Coordinate the complete VELES Desktop runtime."""

    def __init__(
        self,
        system=None,
        core=None,
        services=None,
    ):
        # ==========================================
        # EXTERNAL DEPENDENCIES
        # ==========================================

        self.system = system
        self.core = core
        self.services = services

        # ==========================================
        # DESKTOP COMPONENTS
        # ==========================================

        self.applications = None
        self.window_manager = None
        self.shell = None
        self.ui = None
        self.web = None

        # ==========================================
        # RUNTIME STATE
        # ==========================================

        self.running = False
        self._started = False

    # ==============================================
    # START
    # ==============================================

    def start(self):
        """Start the complete VELES Desktop."""

        if self.running:
            print("[DESKTOP] Desktop already running.")
            return self

        if self._started:
            print("[DESKTOP] Desktop startup already completed.")
            return self

        print("[DESKTOP] Starting VELES Desktop...")

        try:
            self._start_applications()
            self._start_window_manager()
            self._start_shell()
            self._start_ui()
            self._start_web()

            self.running = True
            self._started = True

            print("[DESKTOP] VELES Desktop is ONLINE.")

            return self

        except Exception as exc:
            print("[DESKTOP] Desktop startup FAILED:", exc)

            self._cleanup_failed_start()

            raise

    # ==============================================
    # APPLICATION RUNTIME
    # ==============================================

    def _start_applications(self):
        """Start the Desktop Application Runtime."""

        print("[DESKTOP] Starting Application Runtime...")

        self.applications = ApplicationRuntime()

        self.applications.start()

        print("[DESKTOP] Application Runtime: ONLINE")

    # ==============================================
    # WINDOW MANAGER
    # ==============================================

    def _start_window_manager(self):
        """Start the Desktop Window Manager."""

        print("[DESKTOP] Starting Window Manager...")

        self.window_manager = WindowManager()

        self.window_manager.start()

        print("[DESKTOP] Window Manager: ONLINE")

    # ==============================================
    # DESKTOP SHELL
    # ==============================================

    def _start_shell(self):
        """Start the Desktop Shell."""

        print("[DESKTOP] Starting Desktop Shell...")

        self.shell = DesktopShell(
            runtime=self,
        )

        self.shell.start()

        print("[DESKTOP] Desktop Shell: ONLINE")

    # ==============================================
    # DESKTOP UI
    # ==============================================

    def _start_ui(self):
        """Start the Desktop UI."""

        print("[DESKTOP] Starting Desktop UI...")

        self.ui = DesktopUI(
            shell=self.shell,
        )

        self.ui.start()

        print("[DESKTOP] Desktop UI: ONLINE")

    # ==============================================
    # WEB INTERFACE
    # ==============================================

    def _start_web(self):
        """Start the Desktop Web Interface."""

        print("[DESKTOP] Starting Desktop Web Interface...")

        self.web = start_web()

        print("[DESKTOP] Desktop Web Interface: ONLINE")

    # ==============================================
    # WAIT
    # ==============================================

    def wait(self):
        """
        Keep the Desktop runtime alive.

        The Web Interface owns its own waiting/lifecycle
        mechanism.
        """

        if not self.running:
            return

        try:
            wait_for_web(self.web)

        except KeyboardInterrupt:
            raise

    # ==============================================
    # STOP
    # ==============================================

    def stop(self):
        """Stop the complete VELES Desktop."""

        if not self.running and not self._started:
            return

        print("[DESKTOP] Stopping VELES Desktop...")

        self._stop_component(
            "Desktop Web Interface",
            self.web,
        )
        self.web = None

        self._stop_component(
            "Desktop UI",
            self.ui,
        )
        self.ui = None

        self._stop_component(
            "Desktop Shell",
            self.shell,
        )
        self.shell = None

        self._stop_component(
            "Window Manager",
            self.window_manager,
        )
        self.window_manager = None

        self._stop_component(
            "Application Runtime",
            self.applications,
        )
        self.applications = None

        self.running = False
        self._started = False

        print("[DESKTOP] VELES Desktop is OFFLINE.")

    # ==============================================
    # COMPONENT STOP
    # ==============================================

    @staticmethod
    def _stop_component(name, component):
        """
        Safely stop a Desktop component.

        A failure in one component must not prevent
        the remaining Desktop components from shutting
        down.
        """

        if component is None:
            return

        stop_method = getattr(
            component,
            "stop",
            None,
        )

        if not callable(stop_method):
            print(
                f"[DESKTOP] {name} has no stop() method."
            )
            return

        print(f"[DESKTOP] Stopping {name}...")

        try:
            stop_method()

            print(
                f"[DESKTOP] {name}: OFFLINE"
            )

        except Exception as exc:
            print(
                f"[DESKTOP] {name} shutdown error:",
                exc,
            )

    # ==============================================
    # FAILED START CLEANUP
    # ==============================================

    def _cleanup_failed_start(self):
        """
        Roll back every Desktop component that was
        successfully started.

        Cleanup is performed in strict reverse order
        of startup.
        """

        print(
            "[DESKTOP] Cleaning up failed Desktop startup..."
        )

        self._stop_component(
            "Desktop Web Interface",
            self.web,
        )
        self.web = None

        self._stop_component(
            "Desktop UI",
            self.ui,
        )
        self.ui = None

        self._stop_component(
            "Desktop Shell",
            self.shell,
        )
        self.shell = None

        self._stop_component(
            "Window Manager",
            self.window_manager,
        )
        self.window_manager = None

        self._stop_component(
            "Application Runtime",
            self.applications,
        )
        self.applications = None

        self.running = False
        self._started = False

        print(
            "[DESKTOP] Desktop startup cleanup complete."
        )
"""
VELES OS Desktop Shell

Central UI shell for VELES Desktop.

The Desktop Shell owns:
    - Desktop navigation
    - Active view
    - Shell lifecycle
    - Desktop runtime context

It does not own the lifecycle of:
    - System Layer
    - VELES Core
    - VELES Services
    - Applications
    - Window Manager
    - Desktop UI
"""

from typing import Optional


class DesktopShell:
    """Central navigation and state shell for VELES Desktop."""

    DEFAULT_VIEW = "dashboard"

    DEFAULT_VIEWS = (
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
    )

    def __init__(self, runtime):
        """
        Initialize the Desktop Shell.

        The Desktop Runtime is injected as the shell's
        runtime context and source of Desktop dependencies.
        """

        self.runtime = runtime

        self.active_view = self.DEFAULT_VIEW
        self.running = False

        self.views = list(self.DEFAULT_VIEWS)

    # ==============================================
    # START
    # ==============================================

    def start(self):
        """Start the Desktop Shell."""

        if self.running:
            return self

        self.running = True
        self.active_view = self.DEFAULT_VIEW

        print("[SHELL] VELES Desktop Shell: READY")
        print(
            "[SHELL] Active view: "
            f"{self._format_view(self.active_view)}"
        )

        return self

    # ==============================================
    # NAVIGATION
    # ==============================================

    def navigate(self, view):
        """
        Navigate to a registered Desktop view.

        Args:
            view: Registered view identifier.

        Returns:
            The newly active view.
        """

        if not self.running:
            raise RuntimeError(
                "Desktop Shell is not running."
            )

        normalized_view = self._normalize_view(view)

        if normalized_view not in self.views:
            raise ValueError(
                f"Unknown Desktop view: {view}"
            )

        self.active_view = normalized_view

        print(
            "[SHELL] Active view: "
            f"{self._format_view(normalized_view)}"
        )

        return self.active_view

    # ==============================================
    # VIEW REGISTRY
    # ==============================================

    def register_view(self, view):
        """
        Register a new Desktop view.

        Existing views are not duplicated.
        """

        normalized_view = self._normalize_view(view)

        if not normalized_view:
            raise ValueError(
                "Desktop view name cannot be empty."
            )

        if normalized_view not in self.views:
            self.views.append(normalized_view)

        return normalized_view

    def unregister_view(self, view):
        """
        Remove a Desktop view.

        The default Dashboard view cannot be removed.
        If the active view is removed, navigation returns
        to Dashboard.
        """

        normalized_view = self._normalize_view(view)

        if normalized_view == self.DEFAULT_VIEW:
            raise ValueError(
                "The default Dashboard view cannot be removed."
            )

        if normalized_view not in self.views:
            return False

        self.views.remove(normalized_view)

        if self.active_view == normalized_view:
            self.active_view = self.DEFAULT_VIEW

        return True

    def has_view(self, view):
        """Return whether a Desktop view is registered."""

        normalized_view = self._normalize_view(view)

        return normalized_view in self.views

    # ==============================================
    # STATUS
    # ==============================================

    def status(self):
        """Return the current Desktop Shell state."""

        return {
            "running": self.running,
            "active_view": self.active_view,
            "views": list(self.views),
        }

    # ==============================================
    # RUNTIME ACCESS
    # ==============================================

    def get_runtime(self):
        """Return the owning Desktop Runtime."""

        return self.runtime

    # ==============================================
    # STOP
    # ==============================================

    def stop(self):
        """Stop the Desktop Shell."""

        if not self.running:
            return

        print(
            "[SHELL] Stopping VELES Desktop Shell..."
        )

        self.running = False
        self.active_view = self.DEFAULT_VIEW

        print(
            "[SHELL] VELES Desktop Shell: OFFLINE"
        )

    # ==============================================
    # HELPERS
    # ==============================================

    @staticmethod
    def _normalize_view(view) -> str:
        """Normalize a Desktop view identifier."""

        if view is None:
            return ""

        if not isinstance(view, str):
            raise TypeError(
                "Desktop view must be a string."
            )

        return view.strip().lower().replace(" ", "_")

    @staticmethod
    def _format_view(view) -> str:
        """Convert a view identifier into display text."""

        return view.replace("_", " ").title()
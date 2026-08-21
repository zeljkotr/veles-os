"""
VELES OS Kernel Runtime

Coordinates the complete VELES OS runtime lifecycle.

Architecture:

    Kernel Runtime
        ↓
    Boot Bootstrap
        ↓
    System Layer
        ↓
    VELES Core
        ↓
    VELES Services
        ↓
    VELES Desktop

The kernel runtime owns the lifecycle of the complete
VELES operating system runtime.
"""

import threading


from boot.bootstrap import bootstrap


class VelesRuntime:
    """
    Top-level VELES OS runtime coordinator.

    The kernel runtime owns the lifetime of all major
    VELES OS runtime layers:

        System
        Core
        Services
        Desktop

    Bootstrapping is delegated to boot.bootstrap.
    Shutdown is performed in reverse dependency order.
    """

    def __init__(self):

        # ==========================================
        # RUNTIME COMPONENTS
        # ==========================================

        self.system = None
        self.core = None
        self.services = None
        self.desktop = None

        # ==========================================
        # RUNTIME STATE
        # ==========================================

        self.running = False

        self._started = False

        self._stop_event = threading.Event()

        self._lock = threading.RLock()

    # ==============================================
    # START
    # ==============================================

    def start(self):
        """
        Start the complete VELES OS runtime.

        Bootstrapping is performed once.

        Returns:
            VelesRuntime: this runtime instance.
        """

        with self._lock:

            if self.running:

                print(
                    "[KERNEL] VELES runtime already running."
                )

                return self

            if self._started:

                print(
                    "[KERNEL] VELES runtime already started."
                )

                return self

            print(
                "[KERNEL] Starting VELES runtime..."
            )

            self._stop_event.clear()

            try:

                # ----------------------------------
                # BOOTSTRAP
                # ----------------------------------

                print(
                    "[KERNEL] Executing VELES bootstrap..."
                )

                state = bootstrap()

                if state is None:

                    raise RuntimeError(
                        "VELES bootstrap returned no runtime state."
                    )

                if not isinstance(
                    state,
                    dict
                ):

                    raise RuntimeError(
                        "VELES bootstrap returned invalid runtime state."
                    )

                # ----------------------------------
                # SYSTEM
                # ----------------------------------

                self.system = state.get(
                    "system_layer"
                )

                # ----------------------------------
                # CORE
                # ----------------------------------

                self.core = state.get(
                    "core"
                )

                # ----------------------------------
                # SERVICES
                # ----------------------------------

                self.services = state.get(
                    "services"
                )

                # ----------------------------------
                # DESKTOP
                # ----------------------------------

                self.desktop = state.get(
                    "desktop"
                )

                # ----------------------------------
                # VALIDATE BOOTSTRAP STATE
                # ----------------------------------

                missing = []

                if self.system is None:

                    missing.append(
                        "system_layer"
                    )

                if self.core is None:

                    missing.append(
                        "core"
                    )

                if self.services is None:

                    missing.append(
                        "services"
                    )

                if self.desktop is None:

                    missing.append(
                        "desktop"
                    )

                if missing:

                    raise RuntimeError(
                        "VELES bootstrap did not provide "
                        "required runtime components: "
                        + ", ".join(missing)
                    )

                # ----------------------------------
                # RUNTIME ONLINE
                # ----------------------------------

                self.running = True

                self._started = True

                print(
                    "[KERNEL] System Layer: ONLINE"
                )

                print(
                    "[KERNEL] VELES Core: ONLINE"
                )

                print(
                    "[KERNEL] VELES Services: ONLINE"
                )

                print(
                    "[KERNEL] VELES Desktop: ONLINE"
                )

                print(
                    "[KERNEL] VELES runtime is ONLINE."
                )

                return self

            except Exception:

                print(
                    "[KERNEL] VELES runtime startup FAILED."
                )

                self._cleanup_failed_start()

                raise

    # ==============================================
    # WAIT
    # ==============================================

    def wait(self):
        """
        Keep the VELES OS runtime alive until shutdown.

        The main thread remains blocked while the runtime
        is active.
        """

        with self._lock:

            if not self.running:

                return

        try:

            self._stop_event.wait()

        except KeyboardInterrupt:

            raise

    # ==============================================
    # STOP
    # ==============================================

    def stop(self):
        """
        Stop the complete VELES OS runtime.

        Components are stopped in reverse dependency order:

            Desktop
            Services
            Core
            System
        """

        with self._lock:

            if not self.running:

                return

            print(
                "[KERNEL] Stopping VELES runtime..."
            )

            # ----------------------------------
            # SIGNAL SHUTDOWN
            # ----------------------------------

            self._stop_event.set()

            # ----------------------------------
            # DESKTOP
            # ----------------------------------

            self._stop_component(
                "DESKTOP",
                self.desktop
            )

            self.desktop = None

            # ----------------------------------
            # SERVICES
            # ----------------------------------

            self._stop_component(
                "SERVICES",
                self.services
            )

            self.services = None

            # ----------------------------------
            # CORE
            # ----------------------------------

            self._stop_component(
                "CORE",
                self.core
            )

            self.core = None

            # ----------------------------------
            # SYSTEM
            # ----------------------------------

            self._stop_component(
                "SYSTEM",
                self.system
            )

            self.system = None

            # ----------------------------------
            # FINAL STATE
            # ----------------------------------

            self.running = False

            self._started = False

            self._stop_event.clear()

            print(
                "[KERNEL] VELES runtime is OFFLINE."
            )

    # ==============================================
    # COMPONENT STOP
    # ==============================================

    def _stop_component(
        self,
        name,
        component
    ):
        """
        Stop one runtime component safely.

        A failure in one component must not prevent
        the remaining runtime layers from shutting down.
        """

        if component is None:

            return

        print(
            f"[KERNEL] Stopping {name}..."
        )

        stop_method = getattr(
            component,
            "stop",
            None
        )

        if not callable(
            stop_method
        ):

            print(
                f"[KERNEL] {name} has no stop() method."
            )

            return

        try:

            stop_method()

            print(
                f"[KERNEL] {name}: OFFLINE"
            )

        except Exception as exc:

            print(
                f"[KERNEL] {name} shutdown error:",
                exc
            )

    # ==============================================
    # FAILED START CLEANUP
    # ==============================================

    def _cleanup_failed_start(self):
        """
        Clean up components when startup fails.

        Startup cleanup follows the same reverse
        dependency order as normal shutdown.
        """

        print(
            "[KERNEL] Cleaning up failed startup..."
        )

        self._stop_component(
            "DESKTOP",
            self.desktop
        )

        self.desktop = None

        self._stop_component(
            "SERVICES",
            self.services
        )

        self.services = None

        self._stop_component(
            "CORE",
            self.core
        )

        self.core = None

        self._stop_component(
            "SYSTEM",
            self.system
        )

        self.system = None

        self.running = False

        self._started = False

        self._stop_event.clear()

        print(
            "[KERNEL] Failed startup cleanup complete."
        )
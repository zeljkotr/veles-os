"""
VELES OS Bootstrap

Boot sequence:

    UEFI
      ↓
    Linux Kernel
      ↓
    VELES OS Bootstrap
      ↓
    Configuration
      ↓
    System Layer
      ↓
    VELES Core
      ↓
    VELES Services
      ↓
    VELES Desktop
      ↓
    VELES OS Runtime

The bootstrap layer is responsible only for starting
the VELES OS layers and returning their runtime state.

After bootstrap succeeds, lifecycle ownership is transferred
to kernel.runtime.VelesRuntime.
"""

from pathlib import Path
import os


from system.layer import SystemLayer
from core.runtime import CoreRuntime
from services.runtime import ServicesRuntime
from desktop.runtime import DesktopRuntime


# ==============================================
# ENVIRONMENT CONFIGURATION
# ==============================================

ENVIRONMENT_VARIABLE = (
    "VELES_ENVIRONMENT_FILE"
)


# ==============================================
# ENVIRONMENT FILE DISCOVERY
# ==============================================

def _find_environment_file():
    """
    Locate the VELES runtime environment file.

    Resolution order:

        1. VELES_ENVIRONMENT_FILE
        2. /etc/veles/veles.env
        3. build/rootfs/etc/veles/veles.env

    No user or machine-specific value is hardcoded.
    """

    configured_path = os.getenv(
        ENVIRONMENT_VARIABLE
    )

    if configured_path:

        path = Path(
            configured_path
        )

        if path.is_file():

            return path

    # ------------------------------------------
    # INSTALLED SYSTEM
    # ------------------------------------------

    system_path = Path(
        "/etc/veles/veles.env"
    )

    if system_path.is_file():

        return system_path

    # ------------------------------------------
    # BUILD ROOTFS
    # ------------------------------------------

    project_root = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    build_path = (
        project_root
        / "build"
        / "rootfs"
        / "etc"
        / "veles"
        / "veles.env"
    )

    if build_path.is_file():

        return build_path

    raise FileNotFoundError(
        "VELES environment file not found. "
        "Checked configured path, "
        f"{system_path}, and {build_path}."
    )


# ==============================================
# ENVIRONMENT LOADER
# ==============================================

def load_environment(path=None):
    """
    Load VELES runtime configuration.

    Supports simple KEY=VALUE environment files
    and optional 'export KEY=VALUE' syntax.
    """

    environment_path = (
        Path(path)
        if path
        else _find_environment_file()
    )

    print(
        "[BOOT] Environment:",
        environment_path
    )

    content = environment_path.read_text(
        encoding="utf-8"
    )

    for line in content.splitlines():

        line = line.strip()

        # --------------------------------------
        # EMPTY / COMMENT
        # --------------------------------------

        if not line:
            continue

        if line.startswith("#"):
            continue

        # --------------------------------------
        # EXPORT PREFIX
        # --------------------------------------

        if line.startswith("export "):

            line = line[
                len("export "):
            ].strip()

        # --------------------------------------
        # KEY / VALUE
        # --------------------------------------

        if "=" not in line:

            continue

        name, value = line.split(
            "=",
            1
        )

        name = name.strip()
        value = value.strip()

        if not name:

            continue

        # --------------------------------------
        # QUOTED VALUE
        # --------------------------------------

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in (
                "'",
                '"'
            )
        ):

            value = value[1:-1]

        os.environ[
            name
        ] = value


# ==============================================
# COMPONENT STOP
# ==============================================

def _stop_component(
    name,
    component
):
    """
    Safely stop a single runtime component.

    Bootstrap cleanup must never hide the original
    startup exception.
    """

    if component is None:

        return

    print(
        f"[BOOT] Stopping {name}..."
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
            f"[BOOT] {name} has no stop() method."
        )

        return

    try:

        stop_method()

        print(
            f"[BOOT] {name}: OFFLINE"
        )

    except Exception as exc:

        print(
            f"[BOOT] {name} shutdown error:",
            exc
        )


# ==============================================
# BOOT FAILURE CLEANUP
# ==============================================

def _cleanup(state):
    """
    Roll back all successfully started layers.

    Shutdown order is the reverse of startup order:

        Desktop
        Services
        Core
        System
    """

    if not state:

        return

    print()
    print(
        "[BOOT] Rolling back started layers..."
    )

    _stop_component(
        "VELES Desktop",
        state.get("desktop")
    )

    state["desktop"] = None

    _stop_component(
        "VELES Services",
        state.get("services")
    )

    state["services"] = None

    _stop_component(
        "VELES Core",
        state.get("core")
    )

    state["core"] = None

    _stop_component(
        "System Layer",
        state.get("system_layer")
    )

    state["system_layer"] = None

    state["ready"] = False
    state["stopped"] = True

    print(
        "[BOOT] Startup rollback complete."
    )


# ==============================================
# PUBLIC STOP
# ==============================================

def stop(state):
    """
    Stop a previously bootstrapped VELES OS state.

    This function remains available for compatibility,
    but normal runtime shutdown is owned by VelesRuntime.
    """

    if not state:

        return

    print()
    print(
        "[BOOT] Stopping VELES OS..."
    )

    _stop_component(
        "VELES Desktop",
        state.get("desktop")
    )

    state["desktop"] = None

    _stop_component(
        "VELES Services",
        state.get("services")
    )

    state["services"] = None

    _stop_component(
        "VELES Core",
        state.get("core")
    )

    state["core"] = None

    _stop_component(
        "System Layer",
        state.get("system_layer")
    )

    state["system_layer"] = None

    state["ready"] = False
    state["stopped"] = True

    print(
        "[BOOT] VELES OS stopped."
    )
    print()


# ==============================================
# BOOTSTRAP
# ==============================================

def bootstrap():
    """
    Start the complete VELES OS stack.

    Returns:

        {
            "system_layer": SystemLayer,
            "core": CoreRuntime,
            "services": ServicesRuntime,
            "desktop": DesktopRuntime,
            "ready": True,
            "stopped": False,
        }

    If any layer fails, every previously started layer
    is rolled back before the original exception is raised.
    """

    print()
    print(
        "========================================"
    )
    print(
        "           VELES OS BOOTSTRAP"
    )
    print(
        "========================================"
    )
    print()

    print(
        "[BOOT] Initializing VELES OS..."
    )

    state = {

        "system_layer":
            None,

        "core":
            None,

        "services":
            None,

        "desktop":
            None,

        "ready":
            False,

        "stopped":
            False,
    }

    try:

        # ======================================
        # CONFIGURATION
        # ======================================

        print(
            "[BOOT] Loading VELES configuration..."
        )

        load_environment()

        print(
            "[BOOT] VELES configuration: READY"
        )

        # ======================================
        # SYSTEM LAYER
        # ======================================

        print(
            "[BOOT] Starting System Layer..."
        )

        system = SystemLayer()

        system.start()

        state[
            "system_layer"
        ] = system

        print(
            "[BOOT] System Layer: ONLINE"
        )

        # ======================================
        # VELES CORE
        # ======================================

        print(
            "[BOOT] Starting VELES Core..."
        )

        core = CoreRuntime()

        core.start()

        state[
            "core"
        ] = core

        print(
            "[BOOT] VELES Core: ONLINE"
        )

        # ======================================
        # VELES SERVICES
        # ======================================

        print(
            "[BOOT] Starting VELES Services..."
        )

        services = ServicesRuntime()

        services.start()

        state[
            "services"
        ] = services

        print(
            "[BOOT] VELES Services: ONLINE"
        )

        # ======================================
        # VELES DESKTOP
        # ======================================

        print(
            "[BOOT] Starting VELES Desktop..."
        )

        desktop = DesktopRuntime(
            system=system,
            core=core,
            services=services,
        )

        desktop.start()

        state[
            "desktop"
        ] = desktop

        print(
            "[BOOT] VELES Desktop: ONLINE"
        )

        # ======================================
        # BOOT COMPLETE
        # ======================================

        state[
            "ready"
        ] = True

        state[
            "stopped"
        ] = False

        print()
        print(
            "[BOOT] VELES OS bootstrap complete."
        )
        print(
            "[BOOT] VELES OS: READY"
        )
        print()

        return state

    except Exception:

        print()
        print(
            "[BOOT] VELES OS startup FAILED."
        )

        _cleanup(
            state
        )

        raise
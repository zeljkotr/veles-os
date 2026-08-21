"""
VELES OS Bootstrap

UEFI
  -> Linux Kernel
  -> VELES OS Bootstrap
  -> Configuration
  -> System Layer
  -> VELES Core
  -> VELES Services
  -> VELES Desktop
"""

from pathlib import Path
import os

from system.layer import SystemLayer
from core.runtime import CoreRuntime
from services.runtime import ServicesRuntime
from desktop.runtime import DesktopRuntime


ENVIRONMENT_VARIABLE = "VELES_ENVIRONMENT_FILE"


def _find_environment_file():

    configured_path = os.getenv(
        ENVIRONMENT_VARIABLE
    )

    if configured_path:
        path = Path(configured_path)

        if path.is_file():
            return path

    system_path = Path(
        "/etc/veles/veles.env"
    )

    if system_path.is_file():
        return system_path

    project_root = Path(
        __file__
    ).resolve().parent.parent

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


def load_environment(path=None):
    """Load VELES runtime environment configuration."""

    environment_path = (
        Path(path)
        if path
        else _find_environment_file()
    )

    for line in environment_path.read_text(
        encoding="utf-8"
    ).splitlines():

        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[7:].strip()

        if "=" not in line:
            continue

        name, value = line.split("=", 1)

        name = name.strip()
        value = value.strip()

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in ("'", '"')
        ):
            value = value[1:-1]

        if name:
            os.environ[name] = value


def stop(state):

    if not state:
        return

    print()
    print("[BOOT] Stopping VELES OS...")

    desktop = state.get("desktop")
    services = state.get("services")
    core = state.get("core")
    system = state.get("system_layer")

    if desktop is not None:
        print("[BOOT] Stopping VELES Desktop...")
        desktop.stop()

    if services is not None:
        print("[BOOT] Stopping VELES Services...")
        services.stop()

    if core is not None:
        print("[BOOT] Stopping VELES Core...")
        core.stop()

    if system is not None:
        print("[BOOT] Stopping System Layer...")
        system.stop()

    print("[BOOT] VELES OS stopped.")
    print()


def bootstrap():

    print()
    print("========================================")
    print("           VELES OS BOOTSTRAP")
    print("========================================")
    print()

    print("[BOOT] Initializing VELES OS...")

    state = {
        "system_layer": None,
        "core": None,
        "services": None,
        "desktop": None,
    }

    try:

        # --------------------------------------
        # CONFIGURATION
        # --------------------------------------

        print("[BOOT] Loading VELES configuration...")

        load_environment()

        print("[BOOT] VELES configuration: READY")

        # --------------------------------------
        # SYSTEM LAYER
        # --------------------------------------

        system = SystemLayer()
        system.start()

        state["system_layer"] = system

        # --------------------------------------
        # VELES CORE
        # --------------------------------------

        core = CoreRuntime()
        core.start()

        state["core"] = core

        # --------------------------------------
        # VELES SERVICES
        # --------------------------------------

        services = ServicesRuntime()
        services.start()

        state["services"] = services

        # --------------------------------------
        # VELES DESKTOP
        # --------------------------------------

        desktop = DesktopRuntime(
            system=system,
            core=core,
            services=services,
        )

        desktop.start()

        state["desktop"] = desktop

        # --------------------------------------
        # RUNTIME STATE
        # --------------------------------------

        state["ready"] = True
        state["stopped"] = False

        print()
        print("[BOOT] VELES OS bootstrap complete.")
        print("[BOOT] VELES OS: READY")
        print()

        return state

    except Exception:

        print()
        print("[BOOT] VELES OS startup failed.")
        print("[BOOT] Cleaning up started layers...")

        try:
            stop(state)
        except Exception as cleanup_error:
            print(
                "[BOOT] Cleanup failed:",
                cleanup_error,
            )

        raise
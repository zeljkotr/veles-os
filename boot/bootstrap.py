"""
VELES OS Bootstrap

UEFI
  -> Linux Kernel
  -> VELES OS Bootstrap
  -> System Layer
  -> VELES Core
  -> VELES Services
  -> VELES Desktop
"""

from system.layer import SystemLayer
from core.runtime import CoreRuntime
from services.runtime import ServicesRuntime
from desktop.runtime import DesktopRuntime


def bootstrap():

    print()
    print("========================================")
    print("           VELES OS BOOTSTRAP")
    print("========================================")
    print()

    print("[BOOT] Initializing VELES OS...")

    # --------------------------------------
    # SYSTEM LAYER
    # --------------------------------------

    system = SystemLayer()
    system.start()

    # --------------------------------------
    # VELES CORE
    # --------------------------------------

    core = CoreRuntime()
    core.start()

    # --------------------------------------
    # VELES SERVICES
    # --------------------------------------

    services = ServicesRuntime()
    services.start()

    # --------------------------------------
    # VELES DESKTOP
    # --------------------------------------

    desktop = DesktopRuntime(
        system=system,
        core=core,
        services=services,
    )

    desktop.start()

    # --------------------------------------
    # RUNTIME STATE
    # --------------------------------------

    state = {
        "system_layer": system,
        "core": core,
        "services": services,
        "desktop": desktop,
    }

    print()
    print("[BOOT] VELES OS bootstrap complete.")
    print()

    return state
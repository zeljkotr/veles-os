"""
VELES OS Installer Runtime

Provides the foundation for building and installing
VELES OS images and installation media.
"""

import shutil


class InstallerRuntime:

    REQUIRED_TOOLS = (
        "grub-mkrescue",
        "xorriso",
        "mkfs.ext4",
        "rsync",
        "debootstrap",
        "mksquashfs",
    )

    def __init__(self):
        self.state = "offline"
        self.ready = False
        self.tools = {}

    def start(self):

        if self.ready:
            return self

        print("[INSTALLER] Initializing Installer Runtime...")

        self.state = "starting"

        self.tools = self.detect_tools()

        missing = [
            name
            for name, path in self.tools.items()
            if path is None
        ]

        if missing:
            self.state = "offline"

            raise RuntimeError(
                "Missing installer tools: "
                + ", ".join(missing)
            )

        self.ready = True
        self.state = "online"

        print("[INSTALLER] Build tools: READY")
        print("[INSTALLER] Installer Runtime: READY")

        return self

    def detect_tools(self):

        return {
            tool: shutil.which(tool)
            for tool in self.REQUIRED_TOOLS
        }

    def has_tool(self, name):

        return self.tools.get(name) is not None

    def get_tool(self, name):

        return self.tools.get(name)

    def status(self):

        return {
            "state": self.state,
            "ready": self.ready,
            "tools": dict(self.tools),
        }

    def stop(self):

        if not self.ready:
            return

        print("[INSTALLER] Stopping Installer Runtime...")

        self.tools = {}
        self.ready = False
        self.state = "offline"

        print("[INSTALLER] Installer Runtime: OFFLINE")

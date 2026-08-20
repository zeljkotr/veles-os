"""
VELES OS Package Manager

Provides package metadata and installed-package state
for the VELES operating system.
"""


class PackageManager:

    def __init__(self):
        self.packages = {}

        self.state = "offline"
        self.ready = False

    def start(self):

        if self.ready:
            return self

        print("[PACKAGE] Initializing Package Manager...")

        self.state = "starting"
        self.packages = {}

        self.state = "online"
        self.ready = True

        print("[PACKAGE] Package Manager: READY")

        return self

    def install(self, name, metadata):

        if not self.ready:
            raise RuntimeError(
                "Package Manager is not running."
            )

        if not name:
            raise ValueError(
                "Package name is required."
            )

        if not isinstance(metadata, dict):
            raise TypeError(
                "Package metadata must be a dictionary."
            )

        package = dict(metadata)
        package["installed"] = True

        self.packages[name] = package

        return package

    def uninstall(self, name):

        if not self.ready:
            raise RuntimeError(
                "Package Manager is not running."
            )

        return self.packages.pop(name, None)

    def get(self, name):

        return self.packages.get(name)

    def exists(self, name):

        return name in self.packages

    def list(self):

        return dict(self.packages)

    def status(self):

        return {
            "state": self.state,
            "ready": self.ready,
            "packages": dict(self.packages),
        }

    def stop(self):

        if not self.ready:
            return

        print("[PACKAGE] Stopping Package Manager...")

        self.state = "stopping"
        self.packages = {}

        self.ready = False
        self.state = "offline"

        print("[PACKAGE] Package Manager: OFFLINE")

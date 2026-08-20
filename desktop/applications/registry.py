"""
VELES OS Application Registry

Maintains application metadata and registration state
for the VELES Application Runtime.
"""


class ApplicationRegistry:

    def __init__(self):
        self.applications = {}

        self.state = "offline"
        self.ready = False

    def start(self):

        if self.ready:
            return self

        print("[APPREG] Initializing Application Registry...")

        self.state = "starting"
        self.applications = {}

        self.state = "online"
        self.ready = True

        print("[APPREG] Application Registry: READY")

        return self

    def register(self, name, metadata):

        if not self.ready:
            raise RuntimeError(
                "Application Registry is not running."
            )

        if not name:
            raise ValueError(
                "Application name is required."
            )

        if not isinstance(metadata, dict):
            raise TypeError(
                "Application metadata must be a dictionary."
            )

        self.applications[name] = dict(metadata)

        return self.applications[name]

    def unregister(self, name):

        return self.applications.pop(name, None)

    def get(self, name):

        return self.applications.get(name)

    def exists(self, name):

        return name in self.applications

    def list(self):

        return dict(self.applications)

    def status(self):

        return {
            "state": self.state,
            "ready": self.ready,
            "applications": dict(self.applications),
        }

    def stop(self):

        if not self.ready:
            return

        print("[APPREG] Stopping Application Registry...")

        self.state = "stopping"
        self.applications = {}

        self.ready = False
        self.state = "offline"

        print("[APPREG] Application Registry: OFFLINE")

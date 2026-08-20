"""
VELES OS Window Manager

Manages desktop window state and lifecycle.
"""


class WindowManager:

    def __init__(self):
        self.windows = {}
        self.active_window = None

        self.state = "offline"
        self.ready = False

    def start(self):

        if self.ready:
            return self

        print("[WINDOW] Initializing Window Manager...")

        self.state = "starting"
        self.windows = {}
        self.active_window = None

        self.state = "online"
        self.ready = True

        print("[WINDOW] Window Manager: READY")

        return self

    def create(self, name, metadata=None):

        if not self.ready:
            raise RuntimeError(
                "Window Manager is not running."
            )

        if not name:
            raise ValueError(
                "Window name is required."
            )

        if name in self.windows:
            raise ValueError(
                f"Window already exists: {name}"
            )

        window = {
            "name": name,
            "state": "open",
            "focused": False,
            "minimized": False,
            "maximized": False,
            "metadata": (
                dict(metadata)
                if isinstance(metadata, dict)
                else {}
            ),
        }

        self.windows[name] = window

        self.focus(name)

        return window

    def close(self, name):

        window = self.windows.pop(name, None)

        if window is None:
            return None

        if self.active_window == name:
            self.active_window = None

            if self.windows:
                next_window = next(iter(self.windows))
                self.focus(next_window)

        return window

    def focus(self, name):

        if name not in self.windows:
            return None

        if self.windows[name]["minimized"]:
            return None

        for window in self.windows.values():
            window["focused"] = False

        self.windows[name]["focused"] = True
        self.active_window = name

        return self.windows[name]

    def minimize(self, name):

        window = self.windows.get(name)

        if window is None:
            return None

        window["minimized"] = True
        window["focused"] = False

        if self.active_window == name:
            self.active_window = None

            for next_window_name, next_window in self.windows.items():
                if not next_window["minimized"]:
                    self.focus(next_window_name)
                    break

        return window

    def maximize(self, name):

        window = self.windows.get(name)

        if window is None:
            return None

        window["maximized"] = True
        window["minimized"] = False

        self.focus(name)

        return window

    def restore(self, name):

        window = self.windows.get(name)

        if window is None:
            return None

        window["minimized"] = False
        window["maximized"] = False

        self.focus(name)

        return window

    def get(self, name):

        return self.windows.get(name)

    def list(self):

        return dict(self.windows)

    def status(self):

        return {
            "state": self.state,
            "ready": self.ready,
            "active_window": self.active_window,
            "windows": dict(self.windows),
        }

    def stop(self):

        if not self.ready:
            return

        print("[WINDOW] Stopping Window Manager...")

        self.state = "stopping"
        self.windows = {}
        self.active_window = None

        self.ready = False
        self.state = "offline"

        print("[WINDOW] Window Manager: OFFLINE")
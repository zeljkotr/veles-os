"""
VELES OS Session Manager.

Provides the runtime representation of the active
local VELES OS session.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from system.users.service import UserService
from system.processes.service import ProcessService


class SessionManager:
    """Manages the active local VELES OS session."""

    def __init__(
        self,
        users: UserService | None = None,
        processes: ProcessService | None = None,
    ):
        self.users = users or UserService()
        self.processes = processes or ProcessService()

        self.session: dict[str, Any] | None = None
        self.ready = False

    def start(self):
        """Create the current local VELES OS session."""

        if self.ready:
            return self

        print("[SESSION] Initializing VELES OS Session...")

        pid = os.getpid()

        process = self.processes.get_process(pid)

        if not process:
            raise RuntimeError(
                "Unable to determine current VELES OS process."
            )

        username = process.get("username")

        if not username:
            raise RuntimeError(
                "Unable to determine current VELES OS user."
            )

        user = self.users.get_user(username)

        if not user:
            raise RuntimeError(
                f"Unable to resolve OS user: {username}"
            )

        self.session = {
            "session_id": str(uuid4()),
            "username": user["username"],
            "uid": user["uid"],
            "gid": user["gid"],
            "home": user["home"],
            "shell": user["shell"],
            "pid": pid,
            "state": "active",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        self.ready = True

        print(
            f"[SESSION] User: {self.session['username']}"
        )
        print(
            f"[SESSION] PID: {self.session['pid']}"
        )
        print("[SESSION] VELES OS Session: READY")

        return self

    def current(self) -> dict[str, Any] | None:
        """Return the current session."""

        if not self.ready:
            return None

        return self.session.copy() if self.session else None

    def status(self) -> dict[str, Any]:
        """Return the current session status."""

        return {
            "ready": self.ready,
            "state": (
                self.session["state"]
                if self.session
                else "offline"
            ),
            "session": self.current(),
        }

    def stop(self):
        """Close the current VELES OS session."""

        if not self.ready:
            return

        print("[SESSION] Stopping VELES OS Session...")

        if self.session:
            self.session["state"] = "closed"

        self.ready = False
        self.session = None

        print("[SESSION] VELES OS Session: OFFLINE")

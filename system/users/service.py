"""
VELES OS User System Service.

Read-only discovery of local Linux user accounts.
"""

from __future__ import annotations

import grp
import pwd
from typing import Any


class UserService:
    """Read-only local user information service."""

    def get_users(self) -> list[dict[str, Any]]:
        """Return all local user accounts."""
        users: list[dict[str, Any]] = []

        try:
            entries = pwd.getpwall()
        except Exception:
            return []

        for entry in entries:
            users.append(
                {
                    "username": entry.pw_name,
                    "uid": entry.pw_uid,
                    "gid": entry.pw_gid,
                    "home": entry.pw_dir,
                    "shell": entry.pw_shell,
                    "groups": self._get_groups(
                        entry.pw_name,
                        entry.pw_gid,
                    ),
                }
            )

        users.sort(key=lambda user: user["uid"])

        return users

    def get_user(
        self,
        username: str,
    ) -> dict[str, Any] | None:
        """Return information about one user."""
        try:
            entry = pwd.getpwnam(username)
        except (KeyError, OSError):
            return None

        return {
            "username": entry.pw_name,
            "uid": entry.pw_uid,
            "gid": entry.pw_gid,
            "home": entry.pw_dir,
            "shell": entry.pw_shell,
            "groups": self._get_groups(
                entry.pw_name,
                entry.pw_gid,
            ),
        }

    def get_user_count(self) -> int:
        """Return the number of local user accounts."""
        try:
            return len(pwd.getpwall())
        except Exception:
            return 0

    @staticmethod
    def _get_groups(
        username: str,
        primary_gid: int,
    ) -> list[str]:
        """Return groups associated with a user."""
        groups: list[str] = []

        try:
            primary_group = grp.getgrgid(primary_gid).gr_name

            if primary_group not in groups:
                groups.append(primary_group)
        except KeyError:
            pass

        try:
            for group in grp.getgrall():
                if username in group.gr_mem and group.gr_name not in groups:
                    groups.append(group.gr_name)
        except Exception:
            pass

        groups.sort()

        return groups

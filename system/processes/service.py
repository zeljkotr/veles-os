"""
VELES OS Process System Service.

Read-only discovery of local Linux processes.
"""

from __future__ import annotations

from typing import Any

import psutil


class ProcessService:
    """Read-only local process information service."""

    def get_process_count(self) -> int:
        """Return the current number of processes."""
        try:
            return len(psutil.pids())
        except Exception:
            return 0

    def get_processes(self) -> list[dict[str, Any]]:
        """Return information about all accessible processes."""
        processes: list[dict[str, Any]] = []

        for process in psutil.process_iter(
            [
                "pid",
                "ppid",
                "name",
                "username",
                "status",
                "cpu_percent",
                "memory_percent",
                "memory_info",
                "create_time",
                "cmdline",
            ]
        ):
            try:
                info = process.info
                memory_info = info.get("memory_info")

                processes.append(
                    {
                        "pid": info.get("pid"),
                        "ppid": info.get("ppid"),
                        "name": info.get("name"),
                        "username": info.get("username"),
                        "status": info.get("status"),
                        "cpu_percent": info.get("cpu_percent"),
                        "memory_percent": info.get("memory_percent"),
                        "memory_rss": (
                            memory_info.rss
                            if memory_info is not None
                            else None
                        ),
                        "memory_vms": (
                            memory_info.vms
                            if memory_info is not None
                            else None
                        ),
                        "create_time": info.get("create_time"),
                        "cmdline": info.get("cmdline"),
                    }
                )

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
            ):
                continue

        processes.sort(key=lambda item: item["pid"] or 0)

        return processes

    def get_process(self, pid: int) -> dict[str, Any] | None:
        """Return information for one process by PID."""
        try:
            process = psutil.Process(pid)

            info = process.as_dict(
                attrs=[
                    "pid",
                    "ppid",
                    "name",
                    "username",
                    "status",
                    "cpu_percent",
                    "memory_percent",
                    "memory_info",
                    "create_time",
                    "cmdline",
                ]
            )

            memory_info = info.get("memory_info")

            return {
                "pid": info.get("pid"),
                "ppid": info.get("ppid"),
                "name": info.get("name"),
                "username": info.get("username"),
                "status": info.get("status"),
                "cpu_percent": info.get("cpu_percent"),
                "memory_percent": info.get("memory_percent"),
                "memory_rss": (
                    memory_info.rss
                    if memory_info is not None
                    else None
                ),
                "memory_vms": (
                    memory_info.vms
                    if memory_info is not None
                    else None
                ),
                "create_time": info.get("create_time"),
                "cmdline": info.get("cmdline"),
            }

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            return None

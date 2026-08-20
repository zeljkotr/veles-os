"""
VELES OS System Services Service.

Read-only discovery of local Linux systemd services.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Any


class SystemService:
    """Read-only local systemd service information service."""

    def __init__(self) -> None:
        self._systemctl = shutil.which("systemctl")

    def is_available(self) -> bool:
        """Return whether systemctl is available."""
        return self._systemctl is not None

    def get_service_status(
        self,
        service_name: str,
    ) -> dict[str, Any]:
        """Return the current status of one systemd service."""

        if not self.is_available():
            return {
                "service": service_name,
                "status": "unavailable",
                "active": False,
                "enabled": False,
                "description": None,
                "available": False,
            }

        status = self._run_systemctl(
            "is-active",
            service_name,
        )

        enabled = self._run_systemctl(
            "is-enabled",
            service_name,
        )

        description = self._get_description(
            service_name
        )

        return {
            "service": service_name,
            "status": status or "unknown",
            "active": status == "active",
            "enabled": enabled in {
                "enabled",
                "enabled-runtime",
            },
            "description": description,
            "available": True,
        }

    def get_services(self) -> list[dict[str, Any]]:
        """
        Return installed systemd service units.

        Uses bulk systemctl queries instead of invoking systemctl
        separately for every service.
        """

        if not self.is_available():
            return []

        units = self._list_service_units()

        if not units:
            return []

        enabled_services = self._list_enabled_services()
        active_services = self._list_active_services()

        result: list[dict[str, Any]] = []

        for service_name in units:
            unit_info = active_services.get(service_name, {})

            status = str(
                unit_info.get("status", "inactive")
            )

            active = status == "active"

            result.append(
                {
                    "service": service_name,
                    "status": status,
                    "active": active,
                    "enabled": service_name in enabled_services,
                    "description": unit_info.get(
                        "description"
                    ),
                    "available": True,
                }
            )

        result.sort(
            key=lambda item: str(
                item.get("service", "")
            ).lower()
        )

        return result

    def get_service_count(self) -> int:
        """
        Return the number of installed systemd service units.

        This intentionally does not call get_services(), avoiding
        unnecessary status and description processing.
        """

        return len(self._list_service_units())

    def get_active_services(self) -> list[dict[str, Any]]:
        """Return currently active services."""

        return [
            service
            for service in self.get_services()
            if service.get("active") is True
        ]

    def get_failed_services(self) -> list[dict[str, Any]]:
        """Return services currently in a failed state."""

        return [
            service
            for service in self.get_services()
            if service.get("status") == "failed"
        ]

    def _list_service_units(self) -> list[str]:
        """Return installed systemd service unit names."""

        if not self.is_available():
            return []

        try:
            result = subprocess.run(
                [
                    self._systemctl,
                    "list-unit-files",
                    "--type=service",
                    "--no-legend",
                    "--no-pager",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (
            OSError,
            subprocess.SubprocessError,
        ):
            return []

        if result.returncode != 0:
            return []

        services: list[str] = []

        for line in result.stdout.splitlines():
            parts = line.strip().split()

            if parts and parts[0].endswith(".service"):
                services.append(parts[0])

        return sorted(set(services))

    def _list_enabled_services(self) -> set[str]:
        """Return enabled systemd service unit names."""

        if not self.is_available():
            return set()

        try:
            result = subprocess.run(
                [
                    self._systemctl,
                    "list-unit-files",
                    "--type=service",
                    "--state=enabled",
                    "--no-legend",
                    "--no-pager",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (
            OSError,
            subprocess.SubprocessError,
        ):
            return set()

        if result.returncode != 0:
            return set()

        services: set[str] = set()

        for line in result.stdout.splitlines():
            parts = line.strip().split()

            if parts and parts[0].endswith(".service"):
                services.add(parts[0])

        return services

    def _list_active_services(self) -> dict[str, dict[str, str]]:
        """
        Return bulk runtime information for systemd services.

        Uses one list-units call instead of one systemctl call per
        service.
        """

        if not self.is_available():
            return {}

        try:
            result = subprocess.run(
                [
                    self._systemctl,
                    "list-units",
                    "--all",
                    "--type=service",
                    "--no-legend",
                    "--no-pager",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (
            OSError,
            subprocess.SubprocessError,
        ):
            return {}

        if result.returncode != 0:
            return {}

        services: dict[str, dict[str, str]] = {}

        for line in result.stdout.splitlines():
            line = line.strip()

            if not line:
                continue

            parts = line.split(None, 4)

            if len(parts) < 4:
                continue

            service_name = parts[0]

            if not service_name.endswith(".service"):
                continue

            load_state = parts[1]
            active_state = parts[2]
            sub_state = parts[3]

            description = (
                parts[4]
                if len(parts) >= 5
                else None
            )

            if load_state == "not-found":
                continue

            status = active_state

            if active_state == "failed":
                status = "failed"
            elif sub_state == "running":
                status = "active"
            elif active_state == "inactive":
                status = "inactive"
            elif active_state == "activating":
                status = "activating"
            elif active_state == "deactivating":
                status = "deactivating"

            services[service_name] = {
                "status": status,
                "description": description or "",
            }

        return services

    def _run_systemctl(
        self,
        action: str,
        service_name: str,
    ) -> str:
        """Run a read-only systemctl query."""

        if not self.is_available():
            return ""

        try:
            result = subprocess.run(
                [
                    self._systemctl,
                    action,
                    service_name,
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (
            OSError,
            subprocess.SubprocessError,
        ):
            return ""

        return result.stdout.strip()

    def _get_description(
        self,
        service_name: str,
    ) -> str | None:
        """Return the systemd service description."""

        if not self.is_available():
            return None

        try:
            result = subprocess.run(
                [
                    self._systemctl,
                    "show",
                    service_name,
                    "--property=Description",
                    "--value",
                    "--no-pager",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (
            OSError,
            subprocess.SubprocessError,
        ):
            return None

        if result.returncode != 0:
            return None

        return result.stdout.strip() or None


system_services = SystemService()


def check_systemd_available() -> bool:
    """Backward-compatible systemd availability check."""
    return system_services.is_available()


def get_service_status(
    service_name: str,
) -> dict[str, Any]:
    """Backward-compatible service status wrapper."""
    return system_services.get_service_status(
        service_name
    )


def list_common_services() -> list[dict[str, Any]]:
    """Backward-compatible dynamic service inventory."""
    return system_services.get_services()


__all__ = [
    "SystemService",
    "system_services",
    "check_systemd_available",
    "get_service_status",
    "list_common_services",
]
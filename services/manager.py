"""
VELES OS Service Manager.

Provides controlled lifecycle management for local Linux systemd
services while reusing the existing SystemService discovery layer.
"""

from __future__ import annotations

import subprocess
from typing import Any

from .service import SystemService


class ServiceManager:
    """Manage the lifecycle of local systemd services."""

    def __init__(
        self,
        system_service: SystemService | None = None,
    ) -> None:
        self.system = system_service or SystemService()
        self.ready = False

    def start(self) -> "ServiceManager":
        """Initialize the Service Manager."""
        self.ready = self.system.is_available()
        return self

    def stop(self) -> None:
        """Stop the Service Manager."""
        self.ready = False

    def is_available(self) -> bool:
        """Return whether systemd management is available."""
        return self.system.is_available()

    def get_service_status(
        self,
        service_name: str,
    ) -> dict[str, Any]:
        """Return the current status of a service."""
        return self.system.get_service_status(service_name)

    def get_services(self) -> list[dict[str, Any]]:
        """Return all installed systemd services."""
        return self.system.get_services()

    def get_active_services(self) -> list[dict[str, Any]]:
        """Return currently active services."""
        return self.system.get_active_services()

    def get_failed_services(self) -> list[dict[str, Any]]:
        """Return currently failed services."""
        return self.system.get_failed_services()

    def get_service_count(self) -> int:
        """Return the number of installed service units."""
        return self.system.get_service_count()

    def start_service(
        self,
        service_name: str,
    ) -> dict[str, Any]:
        """Start a systemd service."""
        return self._run_action(
            "start",
            service_name,
        )

    def stop_service(
        self,
        service_name: str,
    ) -> dict[str, Any]:
        """Stop a systemd service."""
        return self._run_action(
            "stop",
            service_name,
        )

    def restart_service(
        self,
        service_name: str,
    ) -> dict[str, Any]:
        """Restart a systemd service."""
        return self._run_action(
            "restart",
            service_name,
        )

    def reload_service(
        self,
        service_name: str,
    ) -> dict[str, Any]:
        """Reload a systemd service."""
        return self._run_action(
            "reload",
            service_name,
        )

    def enable_service(
        self,
        service_name: str,
    ) -> dict[str, Any]:
        """Enable a systemd service."""
        return self._run_action(
            "enable",
            service_name,
        )

    def disable_service(
        self,
        service_name: str,
    ) -> dict[str, Any]:
        """Disable a systemd service."""
        return self._run_action(
            "disable",
            service_name,
        )

    def _run_action(
        self,
        action: str,
        service_name: str,
    ) -> dict[str, Any]:
        """Execute a controlled systemctl lifecycle action."""

        service_name = service_name.strip()

        if not service_name:
            return {
                "success": False,
                "service": service_name,
                "action": action,
                "message": "Service name is required.",
            }

        if not self.is_available():
            return {
                "success": False,
                "service": service_name,
                "action": action,
                "message": "systemd is not available.",
            }

        try:
            result = subprocess.run(
                [
                    self.system._systemctl,
                    action,
                    service_name,
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (
            OSError,
            subprocess.SubprocessError,
        ) as exc:
            return {
                "success": False,
                "service": service_name,
                "action": action,
                "message": str(exc),
            }

        if result.returncode == 0:
            return {
                "success": True,
                "service": service_name,
                "action": action,
                "message": (
                    result.stdout.strip()
                    or f"Service {action} completed successfully."
                ),
            }

        return {
            "success": False,
            "service": service_name,
            "action": action,
            "message": (
                result.stderr.strip()
                or result.stdout.strip()
                or f"Service {action} failed."
            ),
            "returncode": result.returncode,
        }


__all__ = [
    "ServiceManager",
]
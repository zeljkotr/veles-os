"""
VELES OS Network System Service.

Read-only discovery of the local Linux network state.

Provides:
- network interfaces
- interface addresses
- interface state
- MTU
- link speed
- network I/O counters
- hostname
- default gateway
- DNS configuration

No network configuration or destructive operations are performed.
"""

from __future__ import annotations

import os
import socket
import subprocess
from pathlib import Path
from typing import Any

import psutil


class NetworkService:
    """Read-only local network information service."""

    def get_network_info(self) -> dict[str, Any]:
        """Return a complete snapshot of the local network state."""
        return {
            "hostname": self.get_hostname(),
            "interfaces": self.get_interfaces(),
            "network_io": self.get_network_io(),
            "default_gateway": self.get_default_gateway(),
            "dns": self.get_dns(),
        }

    def get_hostname(self) -> str:
        """Return the local system hostname."""
        try:
            return socket.gethostname()
        except Exception:
            return ""

    def get_interfaces(self) -> list[dict[str, Any]]:
        """Return network interface information."""
        interfaces: list[dict[str, Any]] = []

        addresses = psutil.net_if_addrs()
        stats = psutil.net_if_stats()

        family_names = {
            socket.AF_INET: "IPv4",
            socket.AF_INET6: "IPv6",
        }

        for name in sorted(addresses):
            stat = stats.get(name)

            interface: dict[str, Any] = {
                "name": name,
                "is_up": bool(stat.isup) if stat else False,
                "mtu": stat.mtu if stat else None,
                "speed_mbps": stat.speed if stat else None,
                "addresses": [],
            }

            for address in addresses.get(name, []):
                family = family_names.get(
                    address.family,
                    self._get_family_name(address.family),
                )

                interface["addresses"].append(
                    {
                        "family": family,
                        "address": address.address,
                        "netmask": address.netmask,
                        "broadcast": address.broadcast,
                    }
                )

            interfaces.append(interface)

        return interfaces

    def get_network_io(self) -> dict[str, dict[str, int]]:
        """Return network I/O counters for all interfaces."""
        counters = psutil.net_io_counters(pernic=True)

        result: dict[str, dict[str, int]] = {}

        for name, counter in counters.items():
            result[name] = {
                "bytes_received": counter.bytes_recv,
                "bytes_sent": counter.bytes_sent,
                "packets_received": counter.packets_recv,
                "packets_sent": counter.packets_sent,
                "errors_in": counter.errin,
                "errors_out": counter.errout,
                "drops_in": counter.dropin,
                "drops_out": counter.dropout,
            }

        return result

    def get_default_gateway(self) -> dict[str, Any] | None:
        """
        Return the default IPv4 gateway when available.

        Uses the Linux `ip` command when present.
        """
        ip_command = self._find_command("ip")

        if ip_command is None:
            return None

        try:
            result = subprocess.run(
                [
                    ip_command,
                    "-4",
                    "route",
                    "show",
                    "default",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            if result.returncode != 0:
                return None

            lines = result.stdout.strip().splitlines()

            if not lines:
                return None

            parts = lines[0].split()

            gateway = None
            interface = None

            if "via" in parts:
                index = parts.index("via")

                if index + 1 < len(parts):
                    gateway = parts[index + 1]

            if "dev" in parts:
                index = parts.index("dev")

                if index + 1 < len(parts):
                    interface = parts[index + 1]

            if gateway is None and interface is None:
                return None

            return {
                "gateway": gateway,
                "interface": interface,
            }

        except Exception:
            return None

    def get_dns(self) -> list[str]:
        """
        Return configured DNS servers.

        Reads `/etc/resolv.conf` when available.
        """
        path = Path("/etc/resolv.conf")

        if not path.exists():
            return []

        servers: list[str] = []

        try:
            for line in path.read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines():
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                parts = line.split()

                if len(parts) >= 2 and parts[0] == "nameserver":
                    server = parts[1]

                    if server not in servers:
                        servers.append(server)

        except Exception:
            return []

        return servers

    @staticmethod
    def _find_command(command: str) -> str | None:
        """Return an executable path if a command is available."""
        for directory in os.environ.get("PATH", "").split(os.pathsep):
            if not directory:
                continue

            candidate = Path(directory) / command

            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)

        return None

    @staticmethod
    def _get_family_name(family: Any) -> str:
        """Return a readable socket family name."""
        try:
            return str(family.name)
        except AttributeError:
            return str(family)

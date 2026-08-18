"""
VELES OS Storage Service

Read-only storage discovery and filesystem information.

Responsibilities:
- Block devices
- Partitions
- Filesystems
- Mount points
- Disk usage
- UUID
- Storage metadata

No destructive storage operations are performed.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import psutil


class StorageService:
    """
    Read-only storage information provider.
    """

    def get_devices(self) -> list[dict[str, Any]]:
        """
        Return physical block devices.
        """

        devices: list[dict[str, Any]] = []

        block_root = Path("/sys/class/block")

        if not block_root.exists():
            return devices

        for device_path in sorted(block_root.iterdir()):
            name = device_path.name

            if name.startswith(
                (
                    "loop",
                    "ram",
                    "dm-",
                )
            ):
                continue

            device = device_path / "device"

            if not device.exists():
                continue

            devices.append(
                {
                    "name": name,
                    "path": str(device_path.resolve()),
                    "size_bytes": self._get_size(
                        device_path
                    ),
                    "model": self._read(
                        device / "model"
                    ),
                    "vendor": self._read(
                        device / "vendor"
                    ),
                    "serial": self._read(
                        device / "serial"
                    ),
                    "removable": self._read_bool(
                        device_path / "removable"
                    ),
                    "type": self._get_device_type(
                        device_path
                    ),
                    "partitions": self._get_partitions(
                        name
                    ),
                }
            )

        return devices

    def get_partitions(self) -> list[dict[str, Any]]:
        """
        Return all detected partitions.
        """

        partitions: list[dict[str, Any]] = []

        for device in self.get_devices():
            partitions.extend(
                device["partitions"]
            )

        return partitions

    def get_mounts(self) -> list[dict[str, Any]]:
        """
        Return mounted filesystems.
        """

        mounts: list[dict[str, Any]] = []

        for partition in psutil.disk_partitions(
            all=True
        ):
            mountpoint = partition.mountpoint

            usage = None

            try:
                usage = psutil.disk_usage(
                    mountpoint
                )
            except OSError:
                pass

            mounts.append(
                {
                    "device": partition.device,
                    "mountpoint": mountpoint,
                    "filesystem": partition.fstype,
                    "options": partition.opts,
                    "total_bytes": (
                        usage.total
                        if usage
                        else None
                    ),
                    "used_bytes": (
                        usage.used
                        if usage
                        else None
                    ),
                    "free_bytes": (
                        usage.free
                        if usage
                        else None
                    ),
                    "usage_percent": (
                        usage.percent
                        if usage
                        else None
                    ),
                }
            )

        return mounts

    def get_usage(self) -> list[dict[str, Any]]:
        """
        Return filesystem usage.
        """

        result: list[dict[str, Any]] = []

        for mount in self.get_mounts():
            if mount["total_bytes"] is None:
                continue

            result.append(
                {
                    "device": mount["device"],
                    "mountpoint": mount[
                        "mountpoint"
                    ],
                    "filesystem": mount[
                        "filesystem"
                    ],
                    "total_bytes": mount[
                        "total_bytes"
                    ],
                    "used_bytes": mount[
                        "used_bytes"
                    ],
                    "free_bytes": mount[
                        "free_bytes"
                    ],
                    "usage_percent": mount[
                        "usage_percent"
                    ],
                }
            )

        return result

    def get_storage_info(self) -> dict[str, Any]:
        """
        Return complete storage information.
        """

        return {
            "devices": self.get_devices(),
            "partitions": self.get_partitions(),
            "mounts": self.get_mounts(),
            "usage": self.get_usage(),
        }

    @staticmethod
    def _get_size(
        device_path: Path,
    ) -> int | None:
        """
        Return device size in bytes.
        """

        size_path = device_path / "size"

        try:
            sectors = int(
                size_path.read_text().strip()
            )

        except (
            OSError,
            ValueError,
        ):
            return None

        return sectors * 512

    @staticmethod
    def _read(
        path: Path,
    ) -> str | None:
        """
        Safely read a sysfs value.
        """

        try:
            value = path.read_text().strip()

        except OSError:
            return None

        return value or None

    @staticmethod
    def _read_bool(
        path: Path,
    ) -> bool | None:
        """
        Read a sysfs boolean.
        """

        value = StorageService._read(
            path
        )

        if value is None:
            return None

        return value == "1"

    @staticmethod
    def _get_device_type(
        device_path: Path,
    ) -> str | None:
        """
        Determine storage device type.
        """

        rotational = StorageService._read(
            device_path
            / "queue"
            / "rotational"
        )

        if rotational == "0":
            return "solid_state"

        if rotational == "1":
            return "rotational"

        return None

    @staticmethod
    def _get_partitions(
        device_name: str,
    ) -> list[dict[str, Any]]:
        """
        Return partitions belonging to a device.
        """

        partitions: list[dict[str, Any]] = []

        device_path = (
            Path("/sys/class/block")
            / device_name
        )

        if not device_path.exists():
            return partitions

        for partition in sorted(
            device_path.iterdir()
        ):
            name = partition.name

            if not name.startswith(
                device_name
            ):
                continue

            if not (
                partition / "partition"
            ).exists():
                continue

            partitions.append(
                {
                    "name": name,
                    "device": device_name,
                    "path": str(
                        partition.resolve()
                    ),
                    "size_bytes": StorageService._get_size(
                        partition
                    ),
                    "uuid": StorageService._get_uuid(
                        name
                    ),
                    "filesystem": StorageService._get_filesystem(
                        name
                    ),
                }
            )

        return partitions

    @staticmethod
    def _get_uuid(
        device_name: str,
    ) -> str | None:
        """
        Return filesystem UUID.
        """

        return StorageService._blkid(
            device_name,
            "UUID",
        )

    @staticmethod
    def _get_filesystem(
        device_name: str,
    ) -> str | None:
        """
        Return filesystem type.
        """

        return StorageService._blkid(
            device_name,
            "TYPE",
        )

    @staticmethod
    def _blkid(
        device_name: str,
        field: str,
    ) -> str | None:
        """
        Read a property from blkid.
        """

        try:
            result = subprocess.run(
                [
                    "blkid",
                    "-s",
                    field,
                    "-o",
                    "value",
                    f"/dev/{device_name}",
                ],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )

        except (
            OSError,
            subprocess.SubprocessError,
        ):
            return None

        if result.returncode != 0:
            return None

        value = result.stdout.strip()

        return value or None
"""
VELES OS Hardware Service

Read-only hardware and system information provider.

Responsibilities:
- CPU
- Memory
- GPU
- Storage devices
- Network interfaces
- Temperatures
- Fans
- Battery
- Platform information
- Network I/O
- Disk usage

No hardware-specific values are hardcoded.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

import psutil


class HardwareService:
    """
    Read-only hardware information service.
    """

    def get_cpu(self) -> dict[str, Any]:
        """
        Return CPU information.
        """

        frequency = psutil.cpu_freq()

        return {
            "model": self._get_cpu_model(),
            "architecture": platform.machine(),
            "physical_cores": psutil.cpu_count(
                logical=False
            ),
            "logical_cores": psutil.cpu_count(
                logical=True
            ),
            "frequency": {
                "current_mhz": (
                    round(frequency.current, 2)
                    if frequency
                    else None
                ),
                "min_mhz": (
                    round(frequency.min, 2)
                    if frequency
                    else None
                ),
                "max_mhz": (
                    round(frequency.max, 2)
                    if frequency
                    else None
                ),
            },
            "usage_percent": psutil.cpu_percent(
                interval=None
            ),
            "per_core_usage_percent": psutil.cpu_percent(
                interval=None,
                percpu=True,
            ),
        }

    def get_memory(self) -> dict[str, Any]:
        """
        Return system memory information.
        """

        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            "total_bytes": memory.total,
            "available_bytes": memory.available,
            "used_bytes": memory.used,
            "free_bytes": memory.free,
            "cached_bytes": getattr(
                memory,
                "cached",
                None,
            ),
            "buffers_bytes": getattr(
                memory,
                "buffers",
                None,
            ),
            "usage_percent": memory.percent,
            "swap": {
                "total_bytes": swap.total,
                "used_bytes": swap.used,
                "free_bytes": swap.free,
                "usage_percent": swap.percent,
            },
        }

    def get_gpu(self) -> list[dict[str, Any]]:
        """
        Return detected GPU information.

        NVIDIA detection is supported when nvidia-smi
        is available. Other GPU backends can be added
        without changing the public API.
        """

        gpus: list[dict[str, Any]] = []

        nvidia_smi = shutil.which("nvidia-smi")

        if nvidia_smi:
            gpus.extend(
                self._get_nvidia_gpus(
                    nvidia_smi
                )
            )

        return gpus

    def get_storage(self) -> list[dict[str, Any]]:
        """
        Return physical block-device information.
        """

        devices: list[dict[str, Any]] = []

        block_path = Path(
            "/sys/class/block"
        )

        if not block_path.exists():
            return devices

        for device_path in sorted(
            block_path.iterdir()
        ):
            name = device_path.name

            if name.startswith(
                (
                    "loop",
                    "ram",
                    "dm-",
                )
            ):
                continue

            device_path_real = (
                device_path.resolve()
            )

            device = device_path / "device"

            if not device.exists():
                continue

            size_bytes = None

            size_path = (
                device_path / "size"
            )

            try:
                if size_path.exists():
                    sectors = int(
                        size_path.read_text().strip()
                    )

                    size_bytes = (
                        sectors * 512
                    )

            except (
                OSError,
                ValueError,
            ):
                pass

            devices.append(
                {
                    "name": name,
                    "path": str(
                        device_path_real
                    ),
                    "size_bytes": size_bytes,
                    "removable": (
                        self._read_sysfs_bool(
                            device_path
                            / "removable"
                        )
                    ),
                    "model": self._read_sysfs_value(
                        device / "model"
                    ),
                    "vendor": self._read_sysfs_value(
                        device / "vendor"
                    ),
                    "serial": self._read_sysfs_value(
                        device / "serial"
                    ),
                    "device_type": self._get_block_device_type(
                        device_path
                    ),
                }
            )

        return devices

    def get_disk_usage(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return mounted filesystem usage.
        """

        result: list[dict[str, Any]] = []

        seen: set[str] = set()

        for partition in psutil.disk_partitions(
            all=False
        ):
            mountpoint = partition.mountpoint

            if mountpoint in seen:
                continue

            seen.add(mountpoint)

            try:
                usage = psutil.disk_usage(
                    mountpoint
                )

            except OSError:
                continue

            result.append(
                {
                    "device": partition.device,
                    "mountpoint": mountpoint,
                    "filesystem": partition.fstype,
                    "total_bytes": usage.total,
                    "used_bytes": usage.used,
                    "free_bytes": usage.free,
                    "usage_percent": usage.percent,
                }
            )

        return result

    def get_network_interfaces(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return network interface information.
        """

        interfaces: list[dict[str, Any]] = []

        addresses = psutil.net_if_addrs()
        statistics = psutil.net_if_stats()

        for name in sorted(addresses):
            stats = statistics.get(name)

            interface = {
                "name": name,
                "is_up": (
                    stats.isup
                    if stats
                    else None
                ),
                "speed_mbps": (
                    stats.speed
                    if stats
                    else None
                ),
                "mtu": (
                    stats.mtu
                    if stats
                    else None
                ),
                "addresses": [],
            }

            for address in addresses[name]:
                family = self._normalize_address_family(
                    address.family
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

    def get_network_io(
        self,
    ) -> dict[str, dict[str, int]]:
        """
        Return network I/O counters per interface.
        """

        counters = psutil.net_io_counters(
            pernic=True
        )

        result: dict[
            str,
            dict[str, int],
        ] = {}

        for name, counter in counters.items():
            result[name] = {
                "bytes_sent": counter.bytes_sent,
                "bytes_received": counter.bytes_recv,
                "packets_sent": counter.packets_sent,
                "packets_received": counter.packets_recv,
                "errors_in": counter.errin,
                "errors_out": counter.errout,
                "drops_in": counter.dropin,
                "drops_out": counter.dropout,
            }

        return result

    def get_temperatures(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return valid hardware temperature sensors.
        """

        temperatures: list[dict[str, Any]] = []

        try:
            sensors = psutil.sensors_temperatures(
                fahrenheit=False
            )

        except (
            AttributeError,
            OSError,
        ):
            return temperatures

        for sensor_name, entries in sensors.items():
            for entry in entries:
                current = self._valid_temperature(
                    entry.current
                )

                high = self._valid_temperature(
                    entry.high
                )

                critical = self._valid_temperature(
                    entry.critical
                )

                if current is None:
                    continue

                temperatures.append(
                    {
                        "sensor": sensor_name,
                        "label": entry.label,
                        "current_celsius": current,
                        "high_celsius": high,
                        "critical_celsius": critical,
                    }
                )

        return temperatures

    def get_fans(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return available fan sensor information.
        """

        fans: list[dict[str, Any]] = []

        try:
            sensors = psutil.sensors_fans()

        except (
            AttributeError,
            OSError,
        ):
            return fans

        for sensor_name, entries in sensors.items():
            for entry in entries:
                fans.append(
                    {
                        "sensor": sensor_name,
                        "label": entry.label,
                        "current_rpm": entry.current,
                    }
                )

        return fans

    def get_battery(
        self,
    ) -> dict[str, Any] | None:
        """
        Return battery information when available.
        """

        try:
            battery = psutil.sensors_battery()

        except (
            AttributeError,
            OSError,
        ):
            return None

        if battery is None:
            return None

        seconds_left = None

        if battery.secsleft >= 0:
            seconds_left = battery.secsleft

        return {
            "percent": battery.percent,
            "power_plugged": battery.power_plugged,
            "seconds_left": seconds_left,
        }

    def get_platform(
        self,
    ) -> dict[str, Any]:
        """
        Return operating system and platform information.
        """

        processor = (
            self._get_cpu_model()
            or platform.processor()
            or None
        )

        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "architecture": platform.architecture()[0],
            "hostname": platform.node(),
            "processor": processor,
            "python_version": platform.python_version(),
        }

    def get_hardware_info(
        self,
    ) -> dict[str, Any]:
        """
        Return a complete hardware snapshot.
        """

        return {
            "cpu": self.get_cpu(),
            "memory": self.get_memory(),
            "gpu": self.get_gpu(),
            "storage": self.get_storage(),
            "disk_usage": self.get_disk_usage(),
            "network": self.get_network_interfaces(),
            "network_io": self.get_network_io(),
            "temperatures": self.get_temperatures(),
            "fans": self.get_fans(),
            "battery": self.get_battery(),
            "platform": self.get_platform(),
        }

    @staticmethod
    def _get_cpu_model() -> str | None:
        """
        Read CPU model from Linux /proc/cpuinfo.
        """

        cpuinfo = Path(
            "/proc/cpuinfo"
        )

        if not cpuinfo.exists():
            return None

        try:
            for line in cpuinfo.read_text(
                errors="replace"
            ).splitlines():

                if line.lower().startswith(
                    "model name"
                ):
                    _, value = line.split(
                        ":",
                        1,
                    )

                    return value.strip()

        except OSError:
            return None

        return None

    @staticmethod
    def _read_sysfs_value(
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
    def _read_sysfs_bool(
        path: Path,
    ) -> bool | None:
        """
        Read a boolean sysfs value.
        """

        value = HardwareService._read_sysfs_value(
            path
        )

        if value is None:
            return None

        return value == "1"

    @staticmethod
    def _get_block_device_type(
        device_path: Path,
    ) -> str | None:
        """
        Determine block-device type from sysfs.
        """

        rotational = HardwareService._read_sysfs_value(
            device_path / "queue" / "rotational"
        )

        if rotational == "0":
            return "solid_state"

        if rotational == "1":
            return "rotational"

        return None

    @staticmethod
    def _normalize_address_family(
        family: Any,
    ) -> str:
        """
        Normalize socket address family.
        """

        family_name = getattr(
            family,
            "name",
            None,
        )

        if family_name == "AF_INET":
            return "IPv4"

        if family_name == "AF_INET6":
            return "IPv6"

        if family_name == "AF_PACKET":
            return "MAC"

        return str(family)

    @staticmethod
    def _valid_temperature(
        value: Any,
    ) -> float | None:
        """
        Return a sane Celsius temperature.

        Invalid kernel sentinel values are discarded.
        """

        if value is None:
            return None

        try:
            temperature = float(value)

        except (
            TypeError,
            ValueError,
        ):
            return None

        if temperature < -100:
            return None

        if temperature > 150:
            return None

        return round(
            temperature,
            2,
        )

    @staticmethod
    def _to_float(
        value: str,
    ) -> float | None:
        """
        Safely convert a numeric value.
        """

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            return None

    @classmethod
    def _get_nvidia_gpus(
        cls,
        nvidia_smi: str,
    ) -> list[dict[str, Any]]:
        """
        Query NVIDIA GPUs through nvidia-smi.
        """

        command = [
            nvidia_smi,
            "--query-gpu="
            "name,"
            "memory.total,"
            "memory.used,"
            "utilization.gpu,"
            "temperature.gpu",
            "--format=csv,noheader,nounits",
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

        except (
            OSError,
            subprocess.SubprocessError,
        ):
            return []

        if result.returncode != 0:
            return []

        gpus: list[dict[str, Any]] = []

        for line in result.stdout.splitlines():
            values = [
                value.strip()
                for value in line.split(",")
            ]

            if len(values) != 5:
                continue

            (
                name,
                memory_total,
                memory_used,
                utilization,
                temperature,
            ) = values

            gpus.append(
                {
                    "vendor": "NVIDIA",
                    "model": name,
                    "memory_total_mb": cls._to_float(
                        memory_total
                    ),
                    "memory_used_mb": cls._to_float(
                        memory_used
                    ),
                    "utilization_percent": cls._to_float(
                        utilization
                    ),
                    "temperature_celsius": cls._to_float(
                        temperature
                    ),
                }
            )

        return gpus
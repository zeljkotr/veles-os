"""
VELES OS Hardware Models

Canonical data models for the VELES System Hardware Layer.

These models describe hardware and system information collected
by HardwareService.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CPUFrequency:
    current_mhz: Optional[float] = None
    min_mhz: Optional[float] = None
    max_mhz: Optional[float] = None


@dataclass
class CPUInfo:
    model: Optional[str]
    architecture: Optional[str]
    physical_cores: Optional[int]
    logical_cores: Optional[int]
    usage_percent: float
    per_core_usage_percent: list[float] = field(
        default_factory=list
    )
    frequency: CPUFrequency = field(
        default_factory=CPUFrequency
    )


@dataclass
class MemoryInfo:
    total_bytes: int
    available_bytes: int
    used_bytes: int
    free_bytes: int
    cached_bytes: Optional[int] = None
    buffers_bytes: Optional[int] = None
    usage_percent: float = 0.0


@dataclass
class SwapInfo:
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float = 0.0


@dataclass
class MemorySnapshot:
    total_bytes: int
    available_bytes: int
    used_bytes: int
    free_bytes: int
    cached_bytes: Optional[int]
    buffers_bytes: Optional[int]
    usage_percent: float
    swap: SwapInfo


@dataclass
class GPUInfo:
    vendor: Optional[str]
    model: Optional[str]
    memory_total_mb: Optional[float] = None
    memory_used_mb: Optional[float] = None
    utilization_percent: Optional[float] = None
    temperature_celsius: Optional[float] = None


@dataclass
class StorageDevice:
    name: str
    path: Optional[str]
    size_bytes: Optional[int]
    model: Optional[str] = None
    vendor: Optional[str] = None
    serial: Optional[str] = None
    removable: Optional[bool] = None
    device_type: Optional[str] = None


@dataclass
class StorageInfo:
    device: str
    mountpoint: str
    filesystem: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float


@dataclass
class NetworkAddress:
    family: str
    address: str
    netmask: Optional[str] = None
    broadcast: Optional[str] = None


@dataclass
class NetworkInterface:
    name: str
    is_up: Optional[bool]
    speed_mbps: Optional[int]
    mtu: Optional[int]
    addresses: list[NetworkAddress] = field(
        default_factory=list
    )


@dataclass
class NetworkIO:
    bytes_sent: int
    bytes_received: int
    packets_sent: int
    packets_received: int
    errors_in: int
    errors_out: int
    drops_in: int
    drops_out: int


@dataclass
class TemperatureInfo:
    sensor: str
    label: str
    current_celsius: float
    high_celsius: Optional[float] = None
    critical_celsius: Optional[float] = None


@dataclass
class FanInfo:
    sensor: str
    label: str
    current_rpm: Optional[int] = None


@dataclass
class BatteryInfo:
    percent: float
    power_plugged: Optional[bool]
    seconds_left: Optional[int]


@dataclass
class DiskUsage:
    device: str
    mountpoint: str
    filesystem: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float


@dataclass
class PlatformInfo:
    system: str
    release: str
    version: str
    machine: str
    architecture: str
    hostname: str
    processor: Optional[str]
    python_version: str


@dataclass
class HardwareInfo:
    cpu: CPUInfo
    memory: MemorySnapshot
    gpu: list[GPUInfo] = field(
        default_factory=list
    )
    storage: list[StorageDevice] = field(
        default_factory=list
    )
    disk_usage: list[DiskUsage] = field(
        default_factory=list
    )
    network: list[NetworkInterface] = field(
        default_factory=list
    )
    network_io: dict[str, NetworkIO] = field(
        default_factory=dict
    )
    temperatures: list[TemperatureInfo] = field(
        default_factory=list
    )
    fans: list[FanInfo] = field(
        default_factory=list
    )
    battery: Optional[BatteryInfo] = None
    platform: Optional[PlatformInfo] = None
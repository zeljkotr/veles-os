"""
VELES OS Hardware Service.

Provides hardware and operating-system information.
"""

import os
import platform

import psutil


class HardwareService:
    """Collect hardware and operating-system information."""

    @staticmethod
    def get_system_info() -> dict:
        disk = psutil.disk_usage("/")

        return {
            "hostname": platform.node(),
            "os": platform.system(),
            "os_release": platform.release(),
            "kernel": platform.version(),
            "architecture": platform.machine(),
            "cpu": {
                "model": platform.processor(),
                "cores": os.cpu_count(),
                "usage_percent": psutil.cpu_percent(interval=0.2),
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "used": psutil.virtual_memory().used,
                "usage_percent": psutil.virtual_memory().percent,
            },
            "storage": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "usage_percent": disk.percent,
            },
        }

"""
VELES System Information Module.

Collects core operating system information.
"""

import platform
import shutil
import socket
import time

import psutil


def get_cpu_model():

    """
    Read the processor model from the operating system.
    """

    try:

        cpuinfo_path = "/proc/cpuinfo"

        with open(
            cpuinfo_path,
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                if "model name" in line:

                    return (
                        line
                        .split(":", 1)[1]
                        .strip()
                    )

    except Exception:

        pass

    return platform.processor()


def get_uptime():

    """
    Return system uptime in seconds.
    """

    boot_time = psutil.boot_time()

    return int(
        time.time() - boot_time
    )


def get_disk_info(path):

    """
    Return filesystem information for the requested path.
    """

    disk = shutil.disk_usage(path)

    total = disk.total / (
        1024 ** 3
    )

    used = disk.used / (
        1024 ** 3
    )

    free = disk.free / (
        1024 ** 3
    )

    percent = (
        disk.used / disk.total
    ) * 100

    return {

        "path": str(path),

        "total_gb": round(
            total,
            2
        ),

        "used_gb": round(
            used,
            2
        ),

        "free_gb": round(
            free,
            2
        ),

        "percent": round(
            percent,
            1
        )
    }


def get_memory_info():

    memory = psutil.virtual_memory()

    return {

        "total_gb": round(
            memory.total / (1024 ** 3),
            2
        ),

        "used_gb": round(
            memory.used / (1024 ** 3),
            2
        ),

        "available_gb": round(
            memory.available / (1024 ** 3),
            2
        ),

        "percent": memory.percent
    }


def get_cpu_info():

    return {

        "model": get_cpu_model(),

        "cores": psutil.cpu_count(
            logical=False
        ),

        "threads": psutil.cpu_count(
            logical=True
        ),

        "usage": psutil.cpu_percent(
            interval=1
        )
    }


def get_system_info(
    filesystem_path
):

    return {

        "hostname": socket.gethostname(),

        "os": (
            platform.system()
            + " "
            + platform.release()
        ),

        "kernel": platform.release(),

        "architecture": platform.machine(),

        "cpu": get_cpu_info(),

        "memory": get_memory_info(),

        "disk": get_disk_info(
            filesystem_path
        ),

        "uptime_seconds": get_uptime()
    }
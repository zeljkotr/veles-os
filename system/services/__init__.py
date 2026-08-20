"""
VELES OS System Services package.
"""

from .manager import ServiceManager
from .service import (
    SystemService,
    system_services,
    check_systemd_available,
    get_service_status,
    list_common_services,
)

__all__ = [
    "ServiceManager",
    "SystemService",
    "system_services",
    "check_systemd_available",
    "get_service_status",
    "list_common_services",
]

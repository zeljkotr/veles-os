"""
VELES OS Services Runtime

Coordinates the existing VELES Services layer.
"""

from services.infrastructure.service import InfrastructureService
from services.monitoring.service import MonitoringService
from services.security.service import SecurityService
from services.network.service import NetworkService
from services.delivery.service import DeliveryService
from services.package.manager import PackageManager


class ServicesRuntime:
    """Runtime coordinator for the VELES Services layer."""

    def __init__(self):
        self.infrastructure = None
        self.monitoring = None
        self.security = None
        self.network = None
        self.delivery = None
        self.package = None
        self.ready = False

    def start(self):
        """Initialize VELES Services."""

        print("[SERVICES] Initializing VELES Services...")

        self.infrastructure = InfrastructureService()
        print("[SERVICES] Infrastructure: READY")

        self.monitoring = MonitoringService()
        print("[SERVICES] Monitoring: READY")

        self.security = SecurityService()
        print("[SERVICES] Security: READY")

        self.network = NetworkService()
        print("[SERVICES] Network: READY")

        self.delivery = DeliveryService()
        print("[SERVICES] Delivery: READY")

        self.package = PackageManager()
        self.package.start()
        print("[SERVICES] Package Manager: READY")

        self.ready = True

        print("[SERVICES] VELES Services: READY")

        return self

    def stop(self):
        """Stop VELES Services."""

        if not self.ready:
            return

        print("[SERVICES] Stopping VELES Services...")

        if self.package:
            self.package.stop()

        self.package = None
        self.infrastructure = None
        self.monitoring = None
        self.security = None
        self.network = None
        self.delivery = None

        self.ready = False

        print("[SERVICES] VELES Services: OFFLINE")
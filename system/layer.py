"""
VELES OS System Layer

Provides access to the underlying operating system
through the VELES system services and Service Manager.
"""

from system.hardware.service import HardwareService
from system.storage.service import StorageService
from system.filesystem.service import FilesystemService
from system.network.service import NetworkService
from system.users.service import UserService
from system.processes.service import ProcessService
from system.services.service import SystemService
from system.services.manager import ServiceManager
from system.session import SessionManager


class SystemLayer:

    def __init__(self):
        self.hardware = HardwareService()
        self.storage = StorageService()
        self.filesystem = FilesystemService()
        self.network = NetworkService()
        self.users = UserService()
        self.processes = ProcessService()

        # Existing system service discovery/status layer.
        self.services = SystemService()

        # Service lifecycle management layer built on top
        # of the existing SystemService implementation.
        self.service_manager = ServiceManager(
            system_service=self.services
        )

        self.session = SessionManager(
            users=self.users,
            processes=self.processes,
        )

        self.ready = False

    def start(self):
        print("[SYSTEM] Initializing System Layer...")

        # --------------------------------------
        # SYSTEM COMPONENTS
        # --------------------------------------

        self.hardware
        self.storage
        self.filesystem
        self.network
        self.users
        self.processes
        self.services

        # --------------------------------------
        # SERVICE MANAGER
        # --------------------------------------

        self.service_manager.start()

        # --------------------------------------
        # SESSION
        # --------------------------------------

        self.session.start()

        self.ready = True

        print("[SYSTEM] Hardware: READY")
        print("[SYSTEM] Storage: READY")
        print("[SYSTEM] Filesystem: READY")
        print("[SYSTEM] Network: READY")
        print("[SYSTEM] Users: READY")
        print("[SYSTEM] Processes: READY")
        print("[SYSTEM] Services: READY")
        print("[SYSTEM] Service Manager: READY")
        print("[SYSTEM] Session: READY")
        print("[SYSTEM] System Layer: READY")

        return self

    def stop(self):
        if not self.ready:
            return

        print("[SYSTEM] Stopping System Layer...")

        # --------------------------------------
        # SESSION
        # --------------------------------------

        self.session.stop()

        # --------------------------------------
        # SERVICE MANAGER
        # --------------------------------------

        self.service_manager.stop()

        self.ready = False

        print("[SYSTEM] System Layer: OFFLINE")
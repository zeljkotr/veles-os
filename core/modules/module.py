"""
VELES OS Module Foundation

Defines the base contract for every modular VELES component.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class VelesModule:
    """
    Base module definition for VELES OS.

    Every VELES module has a stable identity,
    lifecycle state and health state.
    """

    name: str
    version: str = "1.0.0"
    description: str = ""
    enabled: bool = True

    running: bool = field(
        default=False,
        init=False,
    )

    healthy: bool = field(
        default=False,
        init=False,
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict,
        init=False,
    )

    # --------------------------------------------------
    # LIFECYCLE
    # --------------------------------------------------

    def start(self) -> bool:
        """Start the module."""

        if not self.enabled:
            return False

        if self.running:
            return True

        self.running = True
        self.healthy = True

        return True

    def stop(self) -> bool:
        """Stop the module."""

        if not self.running:
            return True

        self.running = False
        self.healthy = False

        return True

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    def status(self) -> Dict[str, Any]:
        """Return the current module status."""

        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "enabled": self.enabled,
            "running": self.running,
            "healthy": self.healthy,
            "metadata": dict(self.metadata),
        }

    # --------------------------------------------------
    # HEALTH
    # --------------------------------------------------

    def health(self) -> Dict[str, Any]:
        """Return the current module health."""

        return {
            "name": self.name,
            "healthy": self.healthy,
            "running": self.running,
            "enabled": self.enabled,
        }

    # --------------------------------------------------
    # CONFIGURATION
    # --------------------------------------------------

    def configure(
        self,
        configuration: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Apply runtime module configuration."""

        if configuration:
            self.metadata.update(configuration)

        return True

    # --------------------------------------------------
    # IDENTIFICATION
    # --------------------------------------------------

    def identity(self) -> Dict[str, str]:
        """Return stable module identity."""

        return {
            "name": self.name,
            "version": self.version,
        }

    def __repr__(self) -> str:
        return (
            f"<VelesModule "
            f"name={self.name!r} "
            f"version={self.version!r} "
            f"running={self.running}>"
        )
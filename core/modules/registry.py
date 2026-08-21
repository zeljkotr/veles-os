"""
VELES OS Module Registry

Central registry for VELES OS modules.
"""

from __future__ import annotations

from typing import Dict, Optional

from .module import VelesModule


class ModuleRegistry:
    """Central registry for VELES OS modules."""

    def __init__(self) -> None:
        self._modules: Dict[str, VelesModule] = {}

    def register(self, module: VelesModule) -> bool:
        """Register a VELES module."""

        if not module.name:
            return False

        self._modules[module.name] = module
        return True

    def unregister(self, name: str) -> bool:
        """Remove a module from the registry."""

        if name not in self._modules:
            return False

        del self._modules[name]
        return True

    def get(self, name: str) -> Optional[VelesModule]:
        """Return a registered module by name."""

        return self._modules.get(name)

    def get_all(self) -> Dict[str, VelesModule]:
        """Return all registered modules."""

        return dict(self._modules)

    def start_all(self) -> None:
        """Start all enabled registered modules."""

        for module in self._modules.values():
            module.start()

    def stop_all(self) -> None:
        """Stop all registered modules."""

        for module in reversed(
            list(self._modules.values())
        ):
            module.stop()

    def status(self) -> dict:
        """Return registry status."""

        return {
            "count": len(self._modules),
            "modules": {
                name: module.status()
                for name, module in self._modules.items()
            },
        }


__all__ = [
    "ModuleRegistry",
]

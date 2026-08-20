"""
VELES OS Image Layout

Defines and validates the filesystem structure required
for a VELES OS root filesystem.

The actual Linux filesystem is built by RootFSBuilder.
VELES runtime code lives under /opt/veles.
"""

from __future__ import annotations

import json
from pathlib import Path


class ImageLayout:
    """Validates the VELES OS root filesystem layout."""

    REQUIRED_DIRECTORIES = (
        "boot",
        "etc",
        "etc/veles",
        "opt",
        "opt/veles",
        "sbin",
        "usr",
        "var",
    )

    VELES_RUNTIME_DIRECTORIES = (
        "opt/veles/boot",
        "opt/veles/system",
        "opt/veles/core",
        "opt/veles/services",
        "opt/veles/desktop",
        "opt/veles/kernel",
    )

    VERSION_RELATIVE_PATH = Path(
        "etc/veles/version.json"
    )

    DEFAULT_VERSION = "0.1.0"

    def __init__(self, image_root):
        self.image_root = (
            Path(image_root)
            .expanduser()
            .resolve()
        )

    # --------------------------------------------------
    # LAYOUT
    # --------------------------------------------------

    def create(self):
        """Create only safe VELES image directories."""

        self.image_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        for relative in self.REQUIRED_DIRECTORIES:
            (
                self.image_root / relative
            ).mkdir(
                parents=True,
                exist_ok=True,
            )

        self.ensure_version()

        return self.image_root

    # --------------------------------------------------
    # VERSION
    # --------------------------------------------------

    def version_path(self):
        """Return the image version metadata path."""

        return (
            self.image_root
            / self.VERSION_RELATIVE_PATH
        )

    def ensure_version(self):
        """Create VELES version metadata when absent."""

        path = self.version_path()

        if path.exists():
            return path

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "name": "VELES OS",
            "version": self.DEFAULT_VERSION,
        }

        path.write_text(
            json.dumps(
                data,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        return path

    def read_version(self):
        """Read the VELES OS image version."""

        path = self.version_path()

        if not path.exists():
            raise FileNotFoundError(
                f"VELES image version file not found: {path}"
            )

        try:
            data = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Invalid VELES image version metadata: {path}"
            ) from exc

        version = data.get("version")

        if not version:
            raise RuntimeError(
                "VELES image version metadata has no version."
            )

        return version

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    def validate(self):
        """Validate the VELES OS root filesystem layout."""

        if not self.image_root.exists():
            raise FileNotFoundError(
                f"VELES image root does not exist: {self.image_root}"
            )

        if not self.image_root.is_dir():
            raise NotADirectoryError(
                f"VELES image root is not a directory: {self.image_root}"
            )

        missing = [
            relative
            for relative in self.REQUIRED_DIRECTORIES
            if not (
                self.image_root / relative
            ).is_dir()
        ]

        if missing:
            raise RuntimeError(
                "Invalid VELES OS image layout. "
                f"Missing directories: {', '.join(missing)}"
            )

        missing_runtime = [
            relative
            for relative in self.VELES_RUNTIME_DIRECTORIES
            if not (
                self.image_root / relative
            ).is_dir()
        ]

        if missing_runtime:
            raise RuntimeError(
                "Invalid VELES OS runtime layout. "
                f"Missing directories: {', '.join(missing_runtime)}"
            )

        version = self.read_version()

        return {
            "valid": True,
            "root": str(self.image_root),
            "version": version,
            "directories": len(
                self.REQUIRED_DIRECTORIES
            ),
            "runtime_directories": len(
                self.VELES_RUNTIME_DIRECTORIES
            ),
        }
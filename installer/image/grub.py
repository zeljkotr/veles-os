"""
VELES OS GRUB ISO Builder

Builds a bootable VELES OS ISO image from a prepared
ISO staging tree.

This module does not install VELES OS and does not modify
the host boot configuration.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class GRUBISOBuilder:
    """Builds a bootable VELES OS ISO using grub-mkrescue."""

    def __init__(
        self,
        staging_root,
        output_iso,
    ):
        self.staging_root = (
            Path(staging_root)
            .expanduser()
            .resolve()
        )

        self.output_iso = (
            Path(output_iso)
            .expanduser()
            .resolve()
        )

        self.grub_mkrescue = None
        self.built = False

    # --------------------------------------------------
    # TOOL DISCOVERY
    # --------------------------------------------------

    def discover_tool(self):
        """Discover grub-mkrescue on the host."""

        self.grub_mkrescue = shutil.which(
            "grub-mkrescue"
        )

        if self.grub_mkrescue is None:
            raise RuntimeError(
                "grub-mkrescue was not found."
            )

        return self.grub_mkrescue

    # --------------------------------------------------
    # STAGING VALIDATION
    # --------------------------------------------------

    def validate_staging(self):
        """Validate the ISO staging tree."""

        if not self.staging_root.exists():
            raise FileNotFoundError(
                f"ISO staging root does not exist: "
                f"{self.staging_root}"
            )

        if not self.staging_root.is_dir():
            raise NotADirectoryError(
                f"ISO staging root is not a directory: "
                f"{self.staging_root}"
            )

        required = (
            self.staging_root / "boot" / "vmlinuz",
            self.staging_root / "boot" / "veles-initramfs.img",
            self.staging_root
            / "boot"
            / "grub"
            / "grub.cfg",
        )

        missing = [
            str(path)
            for path in required
            if not path.is_file()
        ]

        if missing:
            raise RuntimeError(
                "Invalid ISO staging tree. "
                f"Missing: {', '.join(missing)}"
            )

        return True

    # --------------------------------------------------
    # BUILD
    # --------------------------------------------------

    def build(self):
        """Build a bootable VELES OS ISO."""

        self.validate_staging()
        self.discover_tool()

        self.output_iso.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if self.output_iso.exists():
            self.output_iso.unlink()

        command = [
            self.grub_mkrescue,
            "-o",
            str(self.output_iso),

            # ISO Level 3 is required because the VELES
            # rootfs.squashfs can exceed the ISO Level 1/2
            # single-file 4 GiB limit.
            "-iso-level",
            "3",

            str(self.staging_root),
        ]

        print(
            "[GRUB] Building VELES OS bootable ISO..."
        )

        print(
            "[GRUB] ISO filesystem level: 3"
        )

        subprocess.run(
            command,
            check=True,
        )

        if not self.output_iso.exists():
            raise RuntimeError(
                "grub-mkrescue completed but ISO was not created."
            )

        if not self.output_iso.is_file():
            raise RuntimeError(
                "VELES OS ISO output is not a regular file."
            )

        if self.output_iso.stat().st_size == 0:
            raise RuntimeError(
                "VELES OS ISO output is empty."
            )

        self.built = True

        print(
            f"[GRUB] Bootable ISO ready: "
            f"{self.output_iso}"
        )

        return self.output_iso

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    def validate(self):
        """Validate the generated bootable ISO."""

        if not self.built:
            raise RuntimeError(
                "Bootable ISO has not been built."
            )

        if not self.output_iso.exists():
            raise RuntimeError(
                "Bootable ISO does not exist."
            )

        if not self.output_iso.is_file():
            raise RuntimeError(
                "Bootable ISO is not a regular file."
            )

        size = self.output_iso.stat().st_size

        if size <= 0:
            raise RuntimeError(
                "Bootable ISO is empty."
            )

        return {
            "valid": True,
            "iso": str(self.output_iso),
            "size": size,
        }
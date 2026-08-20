"""
VELES OS SquashFS Builder

Creates the compressed VELES OS root filesystem used
by the bootable VELES OS image.

This module does not modify the host filesystem.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


class SquashFSBuilder:
    """Builds a compressed VELES OS root filesystem."""

    def __init__(
        self,
        rootfs_root,
        output_path,
    ):
        self.rootfs_root = (
            Path(rootfs_root)
            .expanduser()
            .resolve()
        )

        self.output_path = (
            Path(output_path)
            .expanduser()
            .resolve()
        )

        self.built = False

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    def validate_rootfs(self):
        """Validate the source root filesystem."""

        if not self.rootfs_root.exists():
            raise FileNotFoundError(
                f"VELES rootfs does not exist: "
                f"{self.rootfs_root}"
            )

        if not self.rootfs_root.is_dir():
            raise NotADirectoryError(
                f"VELES rootfs is not a directory: "
                f"{self.rootfs_root}"
            )

        required = (
            "sbin",
            "etc",
            "usr",
            "opt",
        )

        missing = [
            relative
            for relative in required
            if not (
                self.rootfs_root / relative
            ).is_dir()
        ]

        if missing:
            raise RuntimeError(
                "Invalid VELES rootfs. "
                f"Missing directories: {', '.join(missing)}"
            )

        init = (
            self.rootfs_root
            / "sbin"
            / "veles-init"
        )

        if not init.is_file():
            raise RuntimeError(
                f"VELES init not found: {init}"
            )

        return True

    def validate_environment(self):
        """Validate SquashFS build requirements."""

        if shutil.which("mksquashfs") is None:
            raise RuntimeError(
                "mksquashfs was not found."
            )

        return True

    # --------------------------------------------------
    # BUILD
    # --------------------------------------------------

    def build(self):
        """Create the compressed VELES root filesystem."""

        print(
            "[SQUASHFS] Building VELES root filesystem..."
        )

        self.validate_rootfs()
        self.validate_environment()

        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if self.output_path.exists():
            self.output_path.unlink()

        command = [
            "mksquashfs",
            str(self.rootfs_root),
            str(self.output_path),
            "-noappend",
            "-comp",
            "xz",
        ]

        subprocess.run(
            command,
            check=True,
        )

        self.built = True

        print(
            f"[SQUASHFS] Root filesystem ready: "
            f"{self.output_path}"
        )

        return self.output_path

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    def validate(self):
        """Validate the generated SquashFS image."""

        if not self.built:
            raise RuntimeError(
                "VELES SquashFS has not been built."
            )

        if not self.output_path.exists():
            raise RuntimeError(
                "VELES SquashFS output does not exist."
            )

        if not self.output_path.is_file():
            raise RuntimeError(
                "VELES SquashFS output is not a file."
            )

        size = self.output_path.stat().st_size

        if size <= 0:
            raise RuntimeError(
                "VELES SquashFS image is empty."
            )

        return {
            "valid": True,
            "rootfs": str(
                self.rootfs_root
            ),
            "squashfs": str(
                self.output_path
            ),
            "size": size,
        }

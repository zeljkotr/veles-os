"""
VELES OS ISO Foundation

Prepares an isolated ISO staging tree for VELES OS.

The Linux root filesystem is packaged separately as SquashFS.
The ISO staging tree contains only the files required by the
boot layout and ISO builder.

This module does not install VELES OS and does not modify
the host system.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from installer.image.layout import ImageLayout


class ISOBuilder:
    """Prepares a VELES OS ISO staging tree."""

    def __init__(
        self,
        image_root,
        staging_root,
    ):
        self.image_root = (
            Path(image_root)
            .expanduser()
            .resolve()
        )

        self.staging_root = (
            Path(staging_root)
            .expanduser()
            .resolve()
        )

        self.layout = ImageLayout(
            self.image_root
        )

        self.prepared = False

    # --------------------------------------------------
    # IMAGE
    # --------------------------------------------------

    def validate_image(self):
        """Validate the source VELES OS image."""

        result = self.layout.validate()

        if not result["valid"]:
            raise RuntimeError(
                "VELES OS image validation failed."
            )

        return result

    # --------------------------------------------------
    # STAGING
    # --------------------------------------------------

    def prepare(self):
        """Prepare an isolated ISO staging tree."""

        self.validate_image()

        if self.staging_root.exists():
            shutil.rmtree(
                self.staging_root
            )

        self.staging_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        (
            self.staging_root / "boot"
        ).mkdir(
            parents=True,
            exist_ok=True,
        )

        (
            self.staging_root / "veles"
        ).mkdir(
            parents=True,
            exist_ok=True,
        )

        self.prepared = True

        print(
            f"[ISO] ISO staging prepared: "
            f"{self.staging_root}"
        )

        return self.staging_root

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    def validate(self):
        """Validate the prepared ISO staging tree."""

        if not self.prepared:
            raise RuntimeError(
                "ISO staging has not been prepared."
            )

        if not self.staging_root.exists():
            raise RuntimeError(
                "ISO staging root does not exist."
            )

        if not self.staging_root.is_dir():
            raise NotADirectoryError(
                f"ISO staging root is not a directory: "
                f"{self.staging_root}"
            )

        boot = (
            self.staging_root / "boot"
        )

        veles = (
            self.staging_root / "veles"
        )

        if not boot.is_dir():
            raise RuntimeError(
                "ISO staging is missing boot directory."
            )

        if not veles.is_dir():
            raise RuntimeError(
                "ISO staging is missing veles directory."
            )

        return {
            "valid": True,
            "root": str(
                self.staging_root
            ),
        }
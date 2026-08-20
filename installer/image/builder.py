"""
VELES OS Image Builder

ImagePipeline-facing adapter for RootFSBuilder.

RootFSBuilder is the authoritative builder for the actual
Linux root filesystem. ImageBuilder only coordinates that
builder and provides the ImagePipeline-compatible validation
and manifest interface.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from installer.image.layout import ImageLayout
from installer.image.rootfs import RootFSBuilder


class ImageBuilder:
    """Builds a validated VELES OS root filesystem."""

    def __init__(
        self,
        source_root,
        image_root,
    ):
        self.source_root = (
            Path(source_root)
            .expanduser()
            .resolve()
        )

        self.image_root = (
            Path(image_root)
            .expanduser()
            .resolve()
        )

        self.layout = ImageLayout(
            self.image_root
        )

        self.rootfs_builder = RootFSBuilder(
            source_root=self.source_root,
            rootfs_root=self.image_root,
            distribution="ubuntu",
            codename=self._detect_codename(),
        )

        self.manifest = None
        self.built = False

    # --------------------------------------------------
    # DISTRIBUTION
    # --------------------------------------------------

    @staticmethod
    def _detect_codename():
        """Detect the host Linux distribution codename."""

        path = Path("/etc/os-release")

        if not path.is_file():
            raise RuntimeError(
                "Unable to determine Linux distribution: "
                "/etc/os-release was not found."
            )

        values = {}

        for line in path.read_text(
            encoding="utf-8"
        ).splitlines():

            if "=" not in line:
                continue

            key, value = line.split(
                "=",
                1,
            )

            values[key] = (
                value.strip()
                .strip('"')
            )

        codename = (
            values.get("VERSION_CODENAME")
            or values.get("UBUNTU_CODENAME")
        )

        if not codename:
            raise RuntimeError(
                "Unable to determine Linux distribution "
                "codename from /etc/os-release."
            )

        return codename

    # --------------------------------------------------
    # SOURCE
    # --------------------------------------------------

    def validate_source(self):
        """Validate the VELES OS source tree."""

        return self.rootfs_builder.validate_source()

    # --------------------------------------------------
    # BUILD
    # --------------------------------------------------

    def build(self):
        """Build the complete VELES Linux root filesystem."""

        print(
            "[IMAGE] Building VELES OS root filesystem..."
        )

        self.validate_source()

        # RootFSBuilder is authoritative for the complete
        # filesystem. Do not recreate or rebuild the layout
        # after it has completed.
        self.rootfs_builder.build()

        # ImageLayout is used only to ensure VELES metadata
        # exists. It must not rebuild the filesystem.
        self.layout.ensure_version()

        self.generate_manifest()

        self.built = True

        print(
            "[IMAGE] VELES OS root filesystem ready: "
            f"{self.image_root}"
        )

        return self.image_root

    # --------------------------------------------------
    # HASHING
    # --------------------------------------------------

    def _hash_file(self, path):
        """Calculate SHA-256 for a file."""

        digest = hashlib.sha256()

        with path.open("rb") as handle:
            while True:
                chunk = handle.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                digest.update(chunk)

        return digest.hexdigest()

    # --------------------------------------------------
    # MANIFEST
    # --------------------------------------------------

    def generate_manifest(self):
        """Generate a manifest for the built root filesystem."""

        if not self.image_root.exists():
            raise RuntimeError(
                "Image has not been built."
            )

        files = {}

        for path in sorted(
            self.image_root.rglob("*")
        ):
            if not path.is_file():
                continue

            relative = path.relative_to(
                self.image_root
            )

            files[str(relative)] = {
                "sha256": self._hash_file(path),
                "size": path.stat().st_size,
            }

        self.manifest = {
            "version": self.layout.read_version(),
            "files": files,
        }

        return self.manifest

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    def validate(self):
        """Validate the completed root filesystem."""

        if not self.built:
            raise RuntimeError(
                "VELES OS image has not been built."
            )

        rootfs_result = (
            self.rootfs_builder.validate()
        )

        layout = self.layout.validate()

        manifest = (
            self.manifest
            if self.manifest is not None
            else self.generate_manifest()
        )

        return {
            "valid": True,
            "root": layout["root"],
            "version": layout["version"],
            "directories": layout["directories"],
            "files": len(
                manifest["files"]
            ),
            "rootfs": rootfs_result["rootfs"],
            "python": rootfs_result["python"],
        }

    # --------------------------------------------------
    # MANIFEST PERSISTENCE
    # --------------------------------------------------

    def save_manifest(self, path):
        """Save the image manifest."""

        if self.manifest is None:
            self.generate_manifest()

        path = (
            Path(path)
            .expanduser()
            .resolve()
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            json.dumps(
                self.manifest,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        return path
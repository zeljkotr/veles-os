"""
VELES OS Image Build Pipeline

Coordinates the complete VELES OS image build:

    ImageBuilder
        ↓
    build/rootfs
        ↓
    SquashFSBuilder
        ↓
    build/rootfs.squashfs
        ↓
    Linux kernel resolution
        ↓
    InitramfsBuilder
        ↓
    build/veles-initramfs.img
        ↓
    ISOBuilder
        ↓
    BootLayout
        ↓
    GRUBISOBuilder
        ↓
    build/VELES-OS-test.iso

This module does not install VELES OS and does not modify
the host boot configuration.
"""

from __future__ import annotations

from pathlib import Path

from installer.image.builder import ImageBuilder
from installer.image.boot import BootLayout
from installer.image.grub import GRUBISOBuilder
from installer.image.initramfs import InitramfsBuilder
from installer.image.iso import ISOBuilder
from installer.image.squashfs import SquashFSBuilder


class ImagePipeline:
    """Builds a complete bootable VELES OS ISO."""

    def __init__(
        self,
        image_root,
        staging_root,
        output_iso,
        source_root=None,
        kernel_path=None,
        squashfs_path=None,
        initramfs_path=None,
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

        self.output_iso = (
            Path(output_iso)
            .expanduser()
            .resolve()
        )

        if source_root is None:
            source_root = (
                Path(__file__)
                .resolve()
                .parents[2]
            )

        self.source_root = (
            Path(source_root)
            .expanduser()
            .resolve()
        )

        self.kernel_path = (
            Path(kernel_path)
            .expanduser()
            .resolve()
            if kernel_path is not None
            else None
        )

        self.squashfs_path = (
            Path(squashfs_path)
            .expanduser()
            .resolve()
            if squashfs_path is not None
            else (
                self.output_iso.parent
                / "rootfs.squashfs"
            )
        )

        self.initramfs_path = (
            Path(initramfs_path)
            .expanduser()
            .resolve()
            if initramfs_path is not None
            else (
                self.output_iso.parent
                / "veles-initramfs.img"
            )
        )

        self.image_builder = ImageBuilder(
            source_root=self.source_root,
            image_root=self.image_root,
        )

        self.iso_builder = ISOBuilder(
            image_root=self.image_root,
            staging_root=self.staging_root,
        )

        self.squashfs_builder = None
        self.initramfs_builder = None
        self.boot_layout = None
        self.grub_builder = None

        self.prepared = False
        self.built = False

    # --------------------------------------------------
    # KERNEL
    # --------------------------------------------------

    @staticmethod
    def discover_kernel():
        """Discover the newest usable Linux kernel from /boot."""

        boot = Path("/boot")

        candidates = [
            path
            for path in boot.glob("vmlinuz-*")
            if path.is_file()
        ]

        if not candidates:
            raise FileNotFoundError(
                "No Linux kernel was found in /boot."
            )

        candidates.sort(
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

        return candidates[0].resolve()

    def resolve_kernel(self):
        """Resolve the Linux kernel used by the VELES image."""

        if self.kernel_path is None:
            self.kernel_path = self.discover_kernel()

        if not self.kernel_path.is_file():
            raise FileNotFoundError(
                f"Linux kernel not found: {self.kernel_path}"
            )

        return self.kernel_path

    # --------------------------------------------------
    # PREPARE
    # --------------------------------------------------

    def prepare(self):
        """Build all image components and prepare ISO staging."""

        print(
            "[PIPELINE] Starting VELES OS image pipeline..."
        )

        # --------------------------------------------------
        # 1. ROOTFS
        # --------------------------------------------------

        print(
            "[PIPELINE] Step 1/5: Building VELES root filesystem..."
        )

        self.image_builder.build()
        image_result = self.image_builder.validate()

        print(
            "[PIPELINE] Root filesystem ready: "
            f"{image_result['root']}"
        )

        # --------------------------------------------------
        # 2. SQUASHFS
        # --------------------------------------------------

        print(
            "[PIPELINE] Step 2/5: Building VELES SquashFS..."
        )

        self.squashfs_builder = SquashFSBuilder(
            rootfs_root=self.image_root,
            output_path=self.squashfs_path,
        )

        self.squashfs_builder.build()
        squashfs_result = self.squashfs_builder.validate()

        print(
            "[PIPELINE] SquashFS ready: "
            f"{squashfs_result['squashfs']}"
        )

        # --------------------------------------------------
        # 3. KERNEL + INITRAMFS
        # --------------------------------------------------

        print(
            "[PIPELINE] Step 3/5: Preparing Linux kernel..."
        )

        self.kernel_path = self.resolve_kernel()

        print(
            "[PIPELINE] Kernel ready: "
            f"{self.kernel_path}"
        )

        print(
            "[PIPELINE] Step 3/5: Building VELES initramfs..."
        )

        self.initramfs_builder = InitramfsBuilder(
            squashfs_path=self.squashfs_path,
            output_path=self.initramfs_path,
            kernel_path=self.kernel_path,
        )

        self.initramfs_builder.build()
        initramfs_result = self.initramfs_builder.validate()

        print(
            "[PIPELINE] Initramfs ready: "
            f"{initramfs_result['initramfs']}"
        )

        # --------------------------------------------------
        # 4. ISO STAGING
        # --------------------------------------------------

        print(
            "[PIPELINE] Step 4/5: Preparing ISO staging..."
        )

        self.iso_builder.prepare()
        self.iso_builder.validate()

        self.boot_layout = BootLayout(
            iso_root=self.staging_root,
            kernel_path=self.kernel_path,
            initrd_path=self.initramfs_path,
            squashfs_path=self.squashfs_path,
        )

        self.boot_layout.prepare()
        boot_result = self.boot_layout.validate()

        print(
            "[PIPELINE] Boot layout ready: "
            f"{self.staging_root}"
        )

        # --------------------------------------------------
        # 5. GRUB
        # --------------------------------------------------

        print(
            "[PIPELINE] Step 5/5: Preparing GRUB ISO builder..."
        )

        self.grub_builder = GRUBISOBuilder(
            staging_root=self.staging_root,
            output_iso=self.output_iso,
        )

        self.grub_builder.validate_staging()

        self.prepared = True

        return {
            "source_root": str(self.source_root),
            "image_root": str(self.image_root),
            "squashfs": str(self.squashfs_path),
            "initramfs": str(self.initramfs_path),
            "staging": str(self.staging_root),
            "kernel": str(self.kernel_path),
            "boot_layout": boot_result,
        }

    # --------------------------------------------------
    # BUILD
    # --------------------------------------------------

    def build(self):
        """Build the complete bootable VELES OS ISO."""

        if not self.prepared:
            self.prepare()

        print(
            "[PIPELINE] Building VELES OS bootable ISO..."
        )

        self.grub_builder.build()

        result = self.grub_builder.validate()

        if not result["valid"]:
            raise RuntimeError(
                "Bootable VELES OS ISO validation failed."
            )

        self.built = True

        print(
            "[PIPELINE] VELES OS ISO ready: "
            f"{self.output_iso}"
        )

        return result

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    def validate(self):
        """Validate the complete VELES OS image pipeline."""

        if not self.built:
            raise RuntimeError(
                "VELES OS ISO has not been built."
            )

        image_result = self.image_builder.validate()
        squashfs_result = self.squashfs_builder.validate()
        initramfs_result = self.initramfs_builder.validate()
        boot_result = self.boot_layout.validate()
        iso_result = self.iso_builder.validate()
        grub_result = self.grub_builder.validate()

        return {
            "valid": True,
            "source_root": str(self.source_root),
            "image_root": image_result["root"],
            "staging_root": iso_result["root"],
            "kernel": boot_result["kernel"],
            "initramfs": initramfs_result["initramfs"],
            "rootfs": image_result["root"],
            "squashfs": squashfs_result["squashfs"],
            "grub_config": boot_result["grub_config"],
            "iso": grub_result["iso"],
            "size": grub_result["size"],
        }
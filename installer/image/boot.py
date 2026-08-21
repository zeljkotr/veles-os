"""
VELES OS Boot Layout

Prepares the bootable VELES OS filesystem structure required by
the VELES OS ISO builder.

Boot structure:

    /boot/vmlinuz
    /boot/veles-initramfs.img
    /veles/rootfs.squashfs
    /boot/grub/grub.cfg

This module does not modify the host boot configuration.
"""

from __future__ import annotations

import shutil
from pathlib import Path


class BootLayout:
    """Prepares a portable VELES OS boot layout."""

    def __init__(
        self,
        iso_root,
        kernel_path,
        initrd_path,
        squashfs_path,
    ):
        self.iso_root = (
            Path(iso_root)
            .expanduser()
            .resolve()
        )

        self.kernel_path = (
            Path(kernel_path)
            .expanduser()
            .resolve()
        )

        self.initrd_path = (
            Path(initrd_path)
            .expanduser()
            .resolve()
        )

        self.squashfs_path = (
            Path(squashfs_path)
            .expanduser()
            .resolve()
        )

        self.grub_directory = (
            self.iso_root
            / "boot"
            / "grub"
        )

        self.prepared = False

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    def validate_kernel(self):
        """Validate kernel, VELES initramfs and root filesystem."""

        if not self.kernel_path.exists():
            raise FileNotFoundError(
                f"Linux kernel not found: "
                f"{self.kernel_path}"
            )

        if not self.kernel_path.is_file():
            raise RuntimeError(
                f"Linux kernel is not a file: "
                f"{self.kernel_path}"
            )

        if not self.initrd_path.exists():
            raise FileNotFoundError(
                f"VELES initramfs not found: "
                f"{self.initrd_path}"
            )

        if not self.initrd_path.is_file():
            raise RuntimeError(
                f"VELES initramfs is not a file: "
                f"{self.initrd_path}"
            )

        if not self.squashfs_path.exists():
            raise FileNotFoundError(
                f"VELES SquashFS not found: "
                f"{self.squashfs_path}"
            )

        if not self.squashfs_path.is_file():
            raise RuntimeError(
                f"VELES SquashFS is not a file: "
                f"{self.squashfs_path}"
            )

        if self.kernel_path.stat().st_size <= 0:
            raise RuntimeError(
                "Linux kernel is empty."
            )

        if self.initrd_path.stat().st_size <= 0:
            raise RuntimeError(
                "VELES initramfs is empty."
            )

        if self.squashfs_path.stat().st_size <= 0:
            raise RuntimeError(
                "VELES SquashFS is empty."
            )

        return True

    # --------------------------------------------------
    # PREPARE
    # --------------------------------------------------

    def prepare(self):
        """Prepare the complete VELES boot filesystem."""

        self.validate_kernel()

        self.grub_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        boot_directory = (
            self.iso_root
            / "boot"
        )

        veles_directory = (
            self.iso_root
            / "veles"
        )

        boot_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        veles_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        kernel_destination = (
            boot_directory
            / "vmlinuz"
        )

        initramfs_destination = (
            boot_directory
            / "veles-initramfs.img"
        )

        rootfs_destination = (
            veles_directory
            / "rootfs.squashfs"
        )

        shutil.copy2(
            self.kernel_path,
            kernel_destination,
        )

        shutil.copy2(
            self.initrd_path,
            initramfs_destination,
        )

        shutil.copy2(
            self.squashfs_path,
            rootfs_destination,
        )

        grub_cfg = (
            self.grub_directory
            / "grub.cfg"
        )

        grub_cfg.write_text(
            """set timeout=5
set default=0

menuentry "VELES OS" {
    linux /boot/vmlinuz console=tty0 console=ttyS0,115200
    initrd /boot/veles-initramfs.img
}

menuentry "Install VELES OS" {
    linux /boot/vmlinuz console=tty0 console=ttyS0,115200 init=/installer/install.sh
    initrd /boot/veles-initramfs.img
}
""",
            encoding="utf-8",
        )

        self.prepared = True

        print(
            f"[BOOT] VELES boot layout prepared: "
            f"{self.iso_root}"
        )

        return self.iso_root

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    def validate(self):
        """Validate the prepared VELES boot layout."""

        if not self.prepared:
            raise RuntimeError(
                "Boot layout has not been prepared."
            )

        kernel = (
            self.iso_root
            / "boot"
            / "vmlinuz"
        )

        initramfs = (
            self.iso_root
            / "boot"
            / "veles-initramfs.img"
        )

        rootfs = (
            self.iso_root
            / "veles"
            / "rootfs.squashfs"
        )

        grub_cfg = (
            self.grub_directory
            / "grub.cfg"
        )

        required = (
            kernel,
            initramfs,
            rootfs,
            grub_cfg,
        )

        missing = [
            str(path)
            for path in required
            if not path.is_file()
        ]

        if missing:
            raise RuntimeError(
                "Invalid VELES boot layout. "
                f"Missing: {', '.join(missing)}"
            )

        return {
            "valid": True,
            "kernel": str(kernel),
            "initramfs": str(initramfs),
            "rootfs": str(rootfs),
            "grub_config": str(grub_cfg),
        }
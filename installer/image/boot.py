"""
VELES OS Boot Layout
"""

from __future__ import annotations

import shutil
from pathlib import Path


class BootLayout:
    def __init__(self, iso_root, kernel_path, initrd_path, squashfs_path):
        self.iso_root = Path(iso_root).expanduser().resolve()
        self.kernel_path = Path(kernel_path).expanduser().resolve()
        self.initrd_path = Path(initrd_path).expanduser().resolve()
        self.squashfs_path = Path(squashfs_path).expanduser().resolve()
        self.grub_directory = self.iso_root / "boot" / "grub"
        self.prepared = False

    def validate_kernel(self):
        if not self.kernel_path.exists():
            raise FileNotFoundError(
                f"Linux kernel not found: {self.kernel_path}"
            )

        if not self.kernel_path.is_file():
            raise RuntimeError(
                f"Linux kernel is not a file: {self.kernel_path}"
            )

        if not self.initrd_path.exists():
            raise FileNotFoundError(
                f"VELES initramfs not found: {self.initrd_path}"
            )

        if not self.initrd_path.is_file():
            raise RuntimeError(
                f"VELES initramfs is not a file: {self.initrd_path}"
            )

        if not self.squashfs_path.exists():
            raise FileNotFoundError(
                f"VELES SquashFS not found: {self.squashfs_path}"
            )

        if not self.squashfs_path.is_file():
            raise RuntimeError(
                f"VELES SquashFS is not a file: {self.squashfs_path}"
            )

        if (
            self.kernel_path.stat().st_size <= 0
            or self.initrd_path.stat().st_size <= 0
            or self.squashfs_path.stat().st_size <= 0
        ):
            raise RuntimeError("One or more boot files are empty.")

        return True

    def prepare(self):
        self.validate_kernel()

        self.grub_directory.mkdir(parents=True, exist_ok=True)

        boot_dir = self.iso_root / "boot"
        veles_dir = self.iso_root / "veles"

        boot_dir.mkdir(parents=True, exist_ok=True)
        veles_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy2(
            self.kernel_path,
            boot_dir / "vmlinuz",
        )

        shutil.copy2(
            self.initrd_path,
            boot_dir / "veles-initramfs.img",
        )

        shutil.copy2(
            self.squashfs_path,
            veles_dir / "rootfs.squashfs",
        )

        grub_cfg = self.grub_directory / "grub.cfg"

        grub_cfg.write_text(
            """set timeout=5
set default=0

menuentry "VELES OS" {
    linux /boot/vmlinuz console=tty0 console=ttyS0,115200
    initrd /boot/veles-initramfs.img
}

menuentry "Install VELES OS" {
    linux /boot/vmlinuz console=tty0 console=ttyS0,115200 veles.mode=installer
    initrd /boot/veles-initramfs.img
}
""",
            encoding="utf-8",
        )

        self.prepared = True

        print(
            f"[BOOT] VELES boot layout prepared: {self.iso_root}"
        )

        return self.iso_root

    def validate(self):
        if not self.prepared:
            raise RuntimeError(
                "Boot layout has not been prepared."
            )

        required = (
            self.iso_root / "boot" / "vmlinuz",
            self.iso_root / "boot" / "veles-initramfs.img",
            self.iso_root / "veles" / "rootfs.squashfs",
            self.grub_directory / "grub.cfg",
        )

        missing = [
            str(path)
            for path in required
            if not path.is_file()
        ]

        if missing:
            raise RuntimeError(
                "Invalid VELES boot layout. Missing: "
                + ", ".join(missing)
            )

        return {
            "valid": True,
            "kernel": str(required[0]),
            "initramfs": str(required[1]),
            "rootfs": str(required[2]),
            "grub_config": str(required[3]),
        }
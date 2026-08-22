"""
VELES OS Installer

Installs the running VELES OS image onto a selected disk.

The installer never automatically selects a disk.

Runtime configuration is created on the installed system and
is never embedded with host-specific credentials into the ISO.
"""

from __future__ import annotations

import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path


SOURCE_ROOT = Path("/")
TARGET_ROOT = Path("/mnt/veles-root")


def run(command, **kwargs):
    print("[INSTALL]", " ".join(str(x) for x in command))
    return subprocess.run(
        command,
        check=True,
        **kwargs,
    )


def detect_disks():
    result = subprocess.run(
        [
            "lsblk",
            "-d",
            "-o",
            "NAME,SIZE,TYPE",
            "-n",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    disks = []

    for line in result.stdout.splitlines():

        parts = line.split()

        if len(parts) < 3:
            continue

        name, size, device_type = parts[:3]

        if device_type != "disk":
            continue

        disks.append(
            {
                "name": name,
                "size": size,
                "path": f"/dev/{name}",
            }
        )

    return disks


def choose_disk(disks):
    print()
    print("Available disks:")
    print()

    for index, disk in enumerate(disks, start=1):
        print(
            f"  {index}. "
            f"{disk['path']} "
            f"({disk['size']})"
        )

    print()

    while True:

        answer = input(
            "Select disk number for VELES installation: "
        ).strip()

        try:
            index = int(answer)
        except ValueError:
            print("Invalid selection.")
            continue

        if 1 <= index <= len(disks):
            selected = disks[index - 1]
            break

        print("Invalid disk number.")

    print()
    print(
        "WARNING: ALL DATA ON THE SELECTED DISK WILL BE ERASED."
    )
    print()
    print(
        f"Selected disk: {selected['path']} "
        f"({selected['size']})"
    )
    print()

    confirmation = input(
        "Type INSTALL to continue: "
    ).strip()

    if confirmation != "INSTALL":
        raise RuntimeError(
            "Installation cancelled."
        )

    return selected


def partition_device(device):
    print()
    print("[1/6] Partitioning disk...")

    run(
        [
            "parted",
            "-s",
            device,
            "mklabel",
            "gpt",
        ]
    )

    run(
        [
            "parted",
            "-s",
            device,
            "mkpart",
            "EFI",
            "fat32",
            "1MiB",
            "513MiB",
        ]
    )

    run(
        [
            "parted",
            "-s",
            device,
            "set",
            "1",
            "esp",
            "on",
        ]
    )

    run(
        [
            "parted",
            "-s",
            device,
            "mkpart",
            "root",
            "ext4",
            "513MiB",
            "100%",
        ]
    )

    run(["partprobe", device])


def partition_paths(device):
    if "nvme" in device or "mmcblk" in device:
        return (
            f"{device}p1",
            f"{device}p2",
        )

    return (
        f"{device}1",
        f"{device}2",
    )


def format_partitions(efi_part, root_part):
    print()
    print("[2/6] Formatting partitions...")

    run(
        [
            "mkfs.fat",
            "-F32",
            "-n",
            "VELES_EFI",
            efi_part,
        ]
    )

    run(
        [
            "mkfs.ext4",
            "-F",
            "-L",
            "VELES_ROOT",
            root_part,
        ]
    )


def copy_system():
    print()
    print("[3/6] Copying VELES OS...")

    if not SOURCE_ROOT.is_dir():
        raise RuntimeError(
            f"VELES source root does not exist: {SOURCE_ROOT}"
        )

    TARGET_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    excludes = [
        "/dev/*",
        "/proc/*",
        "/sys/*",
        "/run/*",
        "/tmp/*",
        "/mnt/*",
    ]

    command = [
        "rsync",
        "-aHAX",
        "--numeric-ids",
        "--delete",
    ]

    for exclude in excludes:
        command.extend(
            [
                "--exclude",
                exclude,
            ]
        )

    command.extend(
        [
            f"{SOURCE_ROOT}/",
            f"{TARGET_ROOT}/",
        ]
    )

    run(command)

    for directory in (
        "dev",
        "proc",
        "sys",
        "run",
        "tmp",
    ):
        (
            TARGET_ROOT / directory
        ).mkdir(
            parents=True,
            exist_ok=True,
        )


def install_kernel():
    print()
    print("[4/6] Installing boot files...")

    target_boot = TARGET_ROOT / "boot"

    target_boot.mkdir(
        parents=True,
        exist_ok=True,
    )

    candidates = (
        Path("/boot/vmlinuz"),
        Path("/boot/vmlinuz-veles"),
    )

    kernel = None

    for candidate in candidates:
        if candidate.is_file():
            kernel = candidate
            break

    if kernel is None:
        kernels = sorted(
            Path("/boot").glob("vmlinuz-*")
        )

        if kernels:
            kernel = kernels[-1]

    if kernel is None:
        raise RuntimeError(
            "No Linux kernel was found in the installation environment."
        )

    shutil.copy2(
        kernel,
        target_boot / "vmlinuz",
    )

    initramfs_candidates = (
        Path("/boot/veles-initramfs.img"),
        Path("/boot/initramfs.img"),
    )

    initramfs = None

    for candidate in initramfs_candidates:
        if candidate.is_file():
            initramfs = candidate
            break

    if initramfs is None:
        initramfs_images = sorted(
            Path("/boot").glob(
                "*initramfs*.img"
            )
        )

        if initramfs_images:
            initramfs = initramfs_images[-1]

    if initramfs is None:
        raise RuntimeError(
            "No VELES initramfs was found in the installation environment."
        )

    shutil.copy2(
        initramfs,
        target_boot / "veles-initramfs.img",
    )

    return True


def configure_runtime():
    print()
    print("[5/6] Configuring installed VELES OS...")

    configuration = TARGET_ROOT / "etc" / "veles" / "veles.env"

    configuration.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("VELES database configuration")
    print("--------------------------------")

    database_url = input(
        "VELES_DATABASE_URL: "
    ).strip()

    if not database_url:
        raise RuntimeError(
            "VELES_DATABASE_URL is required."
        )

    database_password = getpass.getpass(
        "VELES database password: "
    )

    ollama_host = input(
        "VELES_OLLAMA_HOST "
        "[http://127.0.0.1:11434]: "
    ).strip()

    if not ollama_host:
        ollama_host = (
            "http://127.0.0.1:11434"
        )

    ollama_model = input(
        "VELES_OLLAMA_MODEL [qwen2.5:7b]: "
    ).strip()

    if not ollama_model:
        ollama_model = "qwen2.5:7b"

    configuration.write_text(
        "export VELES_DATABASE_URL="
        + repr(database_url)
        + "\n"
        + "export PGPASSWORD="
        + repr(database_password)
        + "\n"
        + "export VELES_OLLAMA_HOST="
        + repr(ollama_host)
        + "\n"
        + "export VELES_OLLAMA_MODEL="
        + repr(ollama_model)
        + "\n",
        encoding="utf-8",
    )

    configuration.chmod(0o600)

    return configuration


def install_grub(efi_part):
    print()
    print("[6/6] Installing VELES bootloader...")

    efi_mount = TARGET_ROOT / "boot" / "efi"

    efi_mount.mkdir(
        parents=True,
        exist_ok=True,
    )

    run(
        [
            "mount",
            efi_part,
            str(efi_mount),
        ]
    )

    for directory in (
        "dev",
        "proc",
        "sys",
    ):
        target = TARGET_ROOT / directory

        target.mkdir(
            parents=True,
            exist_ok=True,
        )

        run(
            [
                "mount",
                "--rbind",
                f"/{directory}",
                str(target),
            ]
        )

        run(
            [
                "mount",
                "--make-rslave",
                str(target),
            ]
        )

    run(
        [
            "chroot",
            str(TARGET_ROOT),
            "grub-install",
            "--target=x86_64-efi",
            "--efi-directory=/boot/efi",
            "--bootloader-id=VELES",
            "--recheck",
        ]
    )

    grub_cfg = TARGET_ROOT / "boot" / "grub"

    grub_cfg.mkdir(
        parents=True,
        exist_ok=True,
    )

    (grub_cfg / "grub.cfg").write_text(
        """set timeout=3
set default=0

menuentry "VELES OS" {
    linux /boot/vmlinuz
    initrd /boot/veles-initramfs.img
}
""",
        encoding="utf-8",
    )


def write_fstab(root_part, efi_part):
    fstab = TARGET_ROOT / "etc" / "fstab"

    fstab.write_text(
        f"{root_part} / ext4 defaults 0 1\n"
        f"{efi_part} /boot/efi vfat defaults 0 2\n",
        encoding="utf-8",
    )


def cleanup():
    subprocess.run(
        [
            "umount",
            "-R",
            str(TARGET_ROOT),
        ],
        check=False,
    )


def main():
    if os.geteuid() != 0:
        print(
            "ERROR: VELES installer must run as root."
        )
        return 1

    print()
    print("=" * 60)
    print("           VELES OS INSTALLER")
    print("=" * 60)
    print()

    if not SOURCE_ROOT.is_dir():
        print(
            f"ERROR: VELES installation source not found: "
            f"{SOURCE_ROOT}"
        )
        return 1

    if not (
        SOURCE_ROOT / "opt/veles/main.py"
    ).is_file():
        print(
            "ERROR: Installation source does not contain a VELES OS."
        )
        return 1

    disks = detect_disks()

    if not disks:
        print("ERROR: No disks found.")
        return 1

    try:
        selected = choose_disk(disks)

        device = selected["path"]

        partition_device(device)

        efi_part, root_part = partition_paths(
            device
        )

        format_partitions(
            efi_part,
            root_part,
        )

        run(
            [
                "mount",
                root_part,
                str(TARGET_ROOT),
            ]
        )

        copy_system()
        install_kernel()
        configure_runtime()
        install_grub(efi_part)
        write_fstab(
            root_part,
            efi_part,
        )

        run(["sync"])

        cleanup()

        print()
        print("=" * 60)
        print("       VELES OS INSTALLATION COMPLETE")
        print("=" * 60)
        print()
        print(
            f"Installed on: {device}"
        )
        print()
        print(
            "Remove the installation media and reboot."
        )
        print()

        return 0

    except KeyboardInterrupt:
        print()
        print("Installation cancelled.")
        cleanup()
        return 1

    except Exception as exc:
        print()
        print(
            "VELES installation FAILED:"
        )
        print(exc)
        cleanup()
        return 1


if __name__ == "__main__":
    sys.exit(main())
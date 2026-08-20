"""
VELES OS Initramfs Builder

Builds the early userspace required to boot the
VELES OS SquashFS root filesystem.

Boot flow:

    Linux kernel
        ↓
    VELES initramfs
        ↓
    initialize device filesystem
        ↓
    initialize network
        ↓
    load ISO/CD-ROM filesystem modules
        ↓
    locate VELES ISO
        ↓
    mount ISO filesystem
        ↓
    mount VELES SquashFS
        ↓
    switch_root
        ↓
    /sbin/veles-init

Network initialization is hardware-independent.
The initramfs discovers available PCI devices,
loads matching kernel modules through their aliases,
and obtains an address through DHCP.

This module does not modify the host boot configuration.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


class InitramfsBuilder:
    """Builds the VELES OS early userspace."""

    ROOT_LABEL = "VELES_ROOT"

    def __init__(
        self,
        squashfs_path,
        output_path,
        kernel_path=None,
    ):
        self.squashfs_path = (
            Path(squashfs_path)
            .expanduser()
            .resolve()
        )

        self.output_path = (
            Path(output_path)
            .expanduser()
            .resolve()
        )

        self.kernel_path = (
            Path(kernel_path)
            .expanduser()
            .resolve()
            if kernel_path is not None
            else self.discover_kernel()
        )

        self.kernel_release = self.kernel_path.name.removeprefix(
            "vmlinuz-"
        )

        self.modules_root = (
            Path("/lib/modules")
            / self.kernel_release
        )

        self.work_root = (
            self.output_path.parent
            / "initramfs"
        )

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

    def validate_kernel(self):
        """Validate the selected kernel and module tree."""

        if not self.kernel_path.exists():
            raise FileNotFoundError(
                f"Linux kernel does not exist: "
                f"{self.kernel_path}"
            )

        if not self.kernel_path.is_file():
            raise RuntimeError(
                f"Linux kernel is not a file: "
                f"{self.kernel_path}"
            )

        if not self.modules_root.exists():
            raise FileNotFoundError(
                f"Kernel modules do not exist: "
                f"{self.modules_root}"
            )

        modules_dep = (
            self.modules_root
            / "modules.dep"
        )

        if not modules_dep.exists():
            raise FileNotFoundError(
                f"Kernel module dependency database not found: "
                f"{modules_dep}"
            )

        return True

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    def validate_rootfs(self):
        """Validate the VELES SquashFS root filesystem."""

        if not self.squashfs_path.exists():
            raise FileNotFoundError(
                f"VELES SquashFS does not exist: "
                f"{self.squashfs_path}"
            )

        if not self.squashfs_path.is_file():
            raise RuntimeError(
                f"VELES SquashFS is not a file: "
                f"{self.squashfs_path}"
            )

        if self.squashfs_path.stat().st_size <= 0:
            raise RuntimeError(
                "VELES SquashFS is empty."
            )

        return True

    def validate_environment(self):
        """Validate tools required for initramfs creation."""

        if os.geteuid() != 0:
            raise PermissionError(
                "Initramfs building requires root privileges."
            )

        required_tools = (
            "cpio",
            "gzip",
            "busybox",
            "depmod",
        )

        for tool in required_tools:
            if shutil.which(tool) is None:
                raise RuntimeError(
                    f"{tool} was not found."
                )

        return True

    # --------------------------------------------------
    # WORKSPACE
    # --------------------------------------------------

    def prepare_workspace(self):
        """Prepare an isolated initramfs workspace."""

        if self.work_root.exists():
            shutil.rmtree(
                self.work_root
            )

        self.work_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        directories = (
            "bin",
            "dev",
            "proc",
            "sys",
            "run",
            "mnt",
            "mnt/boot",
            "mnt/test",
            "newroot",
            "lib",
            "lib/modules",
            "etc",
        )

        for relative in directories:
            (
                self.work_root / relative
            ).mkdir(
                parents=True,
                exist_ok=True,
            )

        return self.work_root

    # --------------------------------------------------
    # BUSYBOX
    # --------------------------------------------------

    def install_busybox(self):
        """Install the static BusyBox runtime."""

        busybox = shutil.which("busybox")

        if busybox is None:
            raise FileNotFoundError(
                "BusyBox was not found."
            )

        busybox = Path(
            busybox
        ).resolve()

        destination = (
            self.work_root
            / "bin"
            / "busybox"
        )

        shutil.copy2(
            busybox,
            destination,
        )

        destination.chmod(0o755)

        return destination

    # --------------------------------------------------
    # BUSYBOX LINKS
    # --------------------------------------------------

    def create_busybox_links(self):
        """Create BusyBox applet links used by init."""

        bin_directory = (
            self.work_root
            / "bin"
        )

        applets = (
            "mount",
            "umount",
            "mkdir",
            "sleep",
            "switch_root",
            "find",
            "echo",
            "cat",
            "sh",
            "modprobe",
            "ls",
            "blkid",
            "mknod",
            "test",
            "ip",
            "ifconfig",
            "route",
            "udhcpc",
            "grep",
            "cut",
        )

        for applet in applets:
            link = (
                bin_directory
                / applet
            )

            if link.exists() or link.is_symlink():
                link.unlink()

            link.symlink_to(
                "busybox"
            )

        return True

    # --------------------------------------------------
    # DHCP SCRIPT
    # --------------------------------------------------

    def create_dhcp_script(self):
        """
        Create a minimal hardware-independent BusyBox
        udhcpc script.

        The script configures the interface using the
        address, subnet and gateway supplied by DHCP.
        """

        script = (
            self.work_root
            / "bin"
            / "udhcpc.script"
        )

        script.write_text(
            """#!/bin/sh

case "$1" in

    deconfig)
        ifconfig "$interface" 0.0.0.0
        ;;

    bound|renew)

        ifconfig "$interface" "$ip" netmask "$subnet" up

        if [ -n "${router:-}" ]; then
            route del default 2>/dev/null || true
            route add default gw "$router" "$interface"
        fi

        if [ -n "${dns:-}" ]; then
            : > /etc/resolv.conf

            for server in $dns; do
                echo "nameserver $server" >> /etc/resolv.conf
            done
        fi

        ;;

esac

exit 0
""",
            encoding="utf-8",
        )

        script.chmod(0o755)

        return script

    # --------------------------------------------------
    # KERNEL MODULES
    # --------------------------------------------------

    def install_kernel_modules(self):
        """
        Install the selected kernel's module tree into
        the initramfs.

        The source tree may contain compressed .ko.zst,
        .ko.xz or .ko.gz modules. They are copied unchanged.
        """

        destination = (
            self.work_root
            / "lib"
            / "modules"
            / self.kernel_release
        )

        destination.mkdir(
            parents=True,
            exist_ok=True,
        )

        modules = list(
            self.modules_root.rglob("*.ko")
        )

        modules.extend(
            self.modules_root.rglob("*.ko.zst")
        )

        modules.extend(
            self.modules_root.rglob("*.ko.xz")
        )

        modules.extend(
            self.modules_root.rglob("*.ko.gz")
        )

        if not modules:
            raise RuntimeError(
                f"No kernel modules found for "
                f"{self.kernel_release}."
            )

        required_names = (
            "isofs",
        )

        found_required = {
            name: False
            for name in required_names
        }

        for module in modules:
            relative = module.relative_to(
                self.modules_root
            )

            target = destination / relative

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.copy2(
                module,
                target,
            )

            module_path = str(module)

            for required in required_names:
                if (
                    f"/{required}.ko" in module_path
                    or f"/{required}.ko." in module_path
                ):
                    found_required[required] = True

        missing = [
            name
            for name, found in found_required.items()
            if not found
        ]

        if missing:
            raise RuntimeError(
                "Required kernel modules were not found "
                f"for {self.kernel_release}: "
                + ", ".join(missing)
            )

        return destination

    def generate_module_dependencies(self):
        """Generate module dependency metadata inside initramfs."""

        modules_directory = (
            self.work_root
            / "lib"
            / "modules"
            / self.kernel_release
        )

        subprocess.run(
            [
                "depmod",
                "-b",
                str(self.work_root),
                self.kernel_release,
            ],
            check=True,
        )

        required_metadata = (
            "modules.dep",
            "modules.alias",
            "modules.symbols",
        )

        for filename in required_metadata:
            path = modules_directory / filename

            if not path.exists():
                raise RuntimeError(
                    f"Failed to generate kernel module metadata: "
                    f"{path}"
                )

        return modules_directory

    # --------------------------------------------------
    # INIT
    # --------------------------------------------------

    def create_init(self):
        """Create the initramfs PID 1 entrypoint."""

        init = (
            self.work_root
            / "init"
        )

        init.write_text(
            f"""#!/bin/sh

set -eu

export PATH=/bin:/sbin:/usr/bin:/usr/sbin

echo
echo "========================================"
echo "           VELES OS INITRAMFS"
echo "========================================"
echo

echo "[INITRAMFS] Starting early userspace..."
echo "[INITRAMFS] Kernel: {self.kernel_release}"

mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
mount -t tmpfs tmpfs /run

exec >/dev/console 2>&1

set -x

mkdir -p /mnt
mkdir -p /mnt/boot
mkdir -p /mnt/test
mkdir -p /newroot

# --------------------------------------------------
# NETWORK
# --------------------------------------------------

echo "[INITRAMFS] Initializing network..."

echo "[INITRAMFS] Discovering PCI devices..."

for device in /sys/bus/pci/devices/*; do

    if [ ! -f "$device/modalias" ]; then
        continue
    fi

    alias="$(cat "$device/modalias" 2>/dev/null || true)"

    if [ -n "$alias" ]; then
        modprobe "$alias" 2>/dev/null || true
    fi

done

sleep 1

NETWORK_READY=""

for interface_path in /sys/class/net/*; do

    interface="$(basename "$interface_path")"

    if [ "$interface" = "lo" ]; then
        continue
    fi

    echo "[INITRAMFS] Trying network interface: $interface"

    ifconfig "$interface" up 2>/dev/null || true

    if udhcpc \
        -i "$interface" \
        -n \
        -q \
        -t 5 \
        -T 3 \
        -s /bin/udhcpc.script
    then
        echo "[INITRAMFS] Network ready: $interface"
        NETWORK_READY="$interface"
        break
    fi

done

if [ -z "$NETWORK_READY" ]; then
    echo "[INITRAMFS] WARNING: DHCP network unavailable."
    echo "[INITRAMFS] Continuing boot without network."
else
    echo "[INITRAMFS] Network configuration:"
    ifconfig "$NETWORK_READY" || true
    route -n || true
fi

# --------------------------------------------------
# STORAGE
# --------------------------------------------------

echo "[INITRAMFS] Loading storage modules..."

modprobe cdrom 2>/dev/null || true
modprobe sr_mod 2>/dev/null || true
modprobe isofs 2>/dev/null || true

echo "[INITRAMFS] Waiting for boot device..."

ROOT_DEVICE=""

attempt=0

while [ "$attempt" -lt 20 ]; do

    for device in /dev/sr*; do

        if [ ! -b "$device" ]; then
            continue
        fi

        echo "[INITRAMFS] Checking $device"

        if mount -t iso9660 -o ro "$device" /mnt/test 2>/dev/null; then

            echo "[INITRAMFS] Mounted $device"

            if [ -f /mnt/test/veles/rootfs.squashfs ]; then
                echo "[INITRAMFS] Found VELES root filesystem"
                ROOT_DEVICE="$device"
                umount /mnt/test
                break 2
            fi

            umount /mnt/test
        fi
    done

    attempt=$((attempt + 1))

    sleep 1
done

if [ -z "$ROOT_DEVICE" ]; then

    echo "[INITRAMFS] ERROR: VELES root filesystem not found."
    echo
    echo "[INITRAMFS] Available block devices:"
    ls -la /dev/sr* /dev/sd* /dev/vd* /dev/xvd* /dev/nvme* 2>/dev/null || true
    echo
    echo "[INITRAMFS] Expected:"
    echo "  /veles/rootfs.squashfs"
    echo
    exec /bin/sh
fi

echo "[INITRAMFS] Root device: $ROOT_DEVICE"

mount -t iso9660 -o ro "$ROOT_DEVICE" /mnt/boot

echo "[INITRAMFS] Mounting VELES SquashFS..."

mount -t squashfs -o ro \\
    /mnt/boot/veles/rootfs.squashfs \\
    /newroot

if [ ! -x /newroot/sbin/veles-init ]; then
    echo "[INITRAMFS] ERROR: VELES init not found."
    echo
    echo "[INITRAMFS] Expected:"
    echo "  /newroot/sbin/veles-init"
    echo
    exec /bin/sh
fi

mkdir -p /newroot/proc
mkdir -p /newroot/sys
mkdir -p /newroot/dev
mkdir -p /newroot/run

mount --move /proc /newroot/proc
mount --move /sys /newroot/sys
mount --move /dev /newroot/dev
mount --move /run /newroot/run

echo "[INITRAMFS] VELES root filesystem ready."
echo "[INITRAMFS] Starting VELES OS..."

exec /bin/switch_root \\
    /newroot \\
    /sbin/veles-init
""",
            encoding="utf-8",
        )

        init.chmod(0o755)

        return init

    # --------------------------------------------------
    # BUILD
    # --------------------------------------------------

    def build(self):
        """Build the VELES initramfs."""

        print(
            "[INITRAMFS] Building VELES initramfs..."
        )

        self.validate_rootfs()
        self.validate_kernel()
        self.validate_environment()

        print(
            "[INITRAMFS] Kernel: "
            f"{self.kernel_path}"
        )

        print(
            "[INITRAMFS] Kernel release: "
            f"{self.kernel_release}"
        )

        print(
            "[INITRAMFS] Modules: "
            f"{self.modules_root}"
        )

        self.prepare_workspace()
        self.install_busybox()
        self.create_busybox_links()
        self.create_dhcp_script()
        self.install_kernel_modules()
        self.generate_module_dependencies()
        self.create_init()

        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if self.output_path.exists():
            self.output_path.unlink()

        print(
            "[INITRAMFS] Creating compressed initramfs..."
        )

        command = (
            "cd "
            + str(self.work_root)
            + " && "
            "find . -print0 | "
            "cpio --null -o -H newc | "
            "gzip -9 > "
            + str(self.output_path)
        )

        subprocess.run(
            [
                "sh",
                "-c",
                command,
            ],
            check=True,
        )

        self.built = True

        print(
            f"[INITRAMFS] VELES initramfs ready: "
            f"{self.output_path}"
        )

        return self.output_path

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    def validate(self):
        """Validate the generated initramfs."""

        if not self.built:
            raise RuntimeError(
                "VELES initramfs has not been built."
            )

        if not self.output_path.exists():
            raise RuntimeError(
                "VELES initramfs output does not exist."
            )

        if not self.output_path.is_file():
            raise RuntimeError(
                "VELES initramfs output is not a file."
            )

        size = self.output_path.stat().st_size

        if size <= 0:
            raise RuntimeError(
                "VELES initramfs is empty."
            )

        return {
            "valid": True,
            "initramfs": str(
                self.output_path
            ),
            "size": size,
            "kernel": str(
                self.kernel_path
            ),
            "kernel_release": self.kernel_release,
            "modules": str(
                self.modules_root
            ),
        }
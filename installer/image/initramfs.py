"""VELES OS Initramfs - DIREKTNO KOPIRANJE"""

from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path

class InitramfsBuilder:
    ROOT_LABEL = "VELES_ROOT"
    def __init__(self, squashfs_path, output_path, kernel_path=None):
        self.squashfs_path = Path(squashfs_path).expanduser().resolve()
        self.output_path = Path(output_path).expanduser().resolve()
        self.kernel_path = Path(kernel_path).expanduser().resolve() if kernel_path is not None else self.discover_kernel()
        self.kernel_release = self.kernel_path.name.removeprefix("vmlinuz-")
        self.modules_root = Path("/lib/modules") / self.kernel_release
        self.work_root = self.output_path.parent / "initramfs"
        self.built = False

    @staticmethod
    def discover_kernel():
        boot = Path("/boot")
        candidates = [p for p in boot.glob("vmlinuz-*") if p.is_file()]
        if not candidates:
            raise FileNotFoundError("No Linux kernel found.")
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0].resolve()

    def validate_kernel(self):
        if not self.kernel_path.exists():
            raise FileNotFoundError(f"Kernel missing: {self.kernel_path}")
        if not self.kernel_path.is_file():
            raise RuntimeError(f"Not a file: {self.kernel_path}")
        if not self.modules_root.exists():
            raise FileNotFoundError(f"Modules missing: {self.modules_root}")
        return True

    def validate_rootfs(self):
        if not self.squashfs_path.exists():
            raise FileNotFoundError(f"SquashFS missing: {self.squashfs_path}")
        if not self.squashfs_path.is_file():
            raise RuntimeError(f"Not a file: {self.squashfs_path}")
        if self.squashfs_path.stat().st_size <= 0:
            raise RuntimeError("SquashFS empty.")
        return True

    def validate_environment(self):
        if os.geteuid() != 0:
            raise PermissionError("Root required.")
        for tool in ("cpio", "gzip", "busybox", "depmod"):
            if shutil.which(tool) is None:
                raise RuntimeError(f"{tool} not found.")
        return True

    def prepare_workspace(self):
        if self.work_root.exists():
            shutil.rmtree(self.work_root)
        self.work_root.mkdir(parents=True, exist_ok=True)
        for d in ("bin","dev","proc","sys","run","mnt","mnt/boot","mnt/test","newroot","lib","lib/modules","etc"):
            (self.work_root / d).mkdir(parents=True, exist_ok=True)
        return self.work_root

    def install_busybox(self):
        busybox = shutil.which("busybox")
        if busybox is None:
            raise FileNotFoundError("BusyBox not found.")
        dst = self.work_root / "bin" / "busybox"
        shutil.copy2(Path(busybox).resolve(), dst)
        dst.chmod(0o755)
        return dst

    def create_busybox_links(self):
        bin_dir = self.work_root / "bin"
        for applet in ("mount","umount","mkdir","sleep","switch_root","find","echo","cat","sh","modprobe","ls","blkid","mknod","test","ip","ifconfig","route","udhcpc","grep","cut"):
            link = bin_dir / applet
            if link.exists() or link.is_symlink():
                link.unlink()
            link.symlink_to("busybox")
        return True

    def create_dhcp_script(self):
        script = self.work_root / "bin" / "udhcpc.script"
        script.write_text("""#!/bin/sh
case "$1" in
    deconfig) ifconfig "$interface" 0.0.0.0 ;;
    bound|renew)
        ifconfig "$interface" "$ip" netmask "$subnet" up
        [ -n "${router:-}" ] && { route del default 2>/dev/null || true; route add default gw "$router" "$interface"; }
        [ -n "${dns:-}" ] && { : > /etc/resolv.conf; for s in $dns; do echo "nameserver $s" >> /etc/resolv.conf; done; }
        ;;
esac
exit 0
""", encoding="utf-8")
        script.chmod(0o755)
        return script

    @staticmethod
    def _module_key(path):
        name = path.name
        for suffix in (".ko.zst",".ko.xz",".ko.gz",".ko"):
            if name.endswith(suffix):
                return name[:-len(suffix)]
        return None

    def _build_module_index(self):
        index = {}
        for pat in ("*.ko","*.ko.zst","*.ko.xz","*.ko.gz"):
            for m in self.modules_root.rglob(pat):
                key = self._module_key(m)
                if key:
                    index[key] = m
        return index

    def install_kernel_modules(self):
        dst = self.work_root / "lib" / "modules" / self.kernel_release
        dst.mkdir(parents=True, exist_ok=True)
        
        # DIREKTNO KOPIRANJE FAT MODULA - KLJUČNO!
        fat_src = self.modules_root / "kernel/fs/fat"
        if fat_src.exists():
            print("[INITRAMFS] Copying FAT module directly...")
            fat_dst = dst / "kernel/fs/fat"
            fat_dst.mkdir(parents=True, exist_ok=True)
            for f in fat_src.glob("*.ko*"):
                shutil.copy2(f, fat_dst / f.name)
                print(f"[INITRAMFS] Copied: {f.name}")
        
        # KOPIRAJ SVE MODULE
        print("[INITRAMFS] Copying all modules...")
        copied = 0
        for m in self.modules_root.rglob("*.ko*"):
            rel = m.relative_to(self.modules_root)
            tgt = dst / rel
            tgt.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(m, tgt)
            copied += 1
            if copied % 50 == 0:
                print(f"[INITRAMFS] Copied {copied} modules...")
        
        print(f"[INITRAMFS] Total modules copied: {copied}")
        if copied == 0:
            raise RuntimeError("No kernel modules were copied!")
        return dst

    def generate_module_dependencies(self):
        subprocess.run(["depmod", "-b", str(self.work_root), self.kernel_release], check=True)
        return self.work_root / "lib" / "modules" / self.kernel_release

    def create_init(self):
        init = self.work_root / "init"
        init.write_text(f"""#!/bin/sh
set -eu
export PATH=/bin:/sbin:/usr/bin:/usr/sbin
echo "========================================"
echo "           VELES OS INITRAMFS"
echo "========================================"
echo "[INITRAMFS] Starting early userspace..."
echo "[INITRAMFS] Kernel: {self.kernel_release}"
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
mount -t tmpfs tmpfs /run
exec >/dev/console 2>&1
set -x
mkdir -p /mnt /mnt/boot /mnt/test /newroot
echo "[INITRAMFS] Initializing network..."
for dev in /sys/bus/pci/devices/*; do
    [ -f "$dev/modalias" ] && modprobe "$(cat "$dev/modalias")" 2>/dev/null || true
done
sleep 1
for iface in /sys/class/net/*; do
    i=$(basename "$iface")
    [ "$i" = "lo" ] && continue
    echo "[INITRAMFS] Trying: $i"
    ifconfig "$i" up 2>/dev/null || true
    if udhcpc -i "$i" -n -q -t 5 -T 3 -s /bin/udhcpc.script; then
        echo "[INITRAMFS] Network ready: $i"
        break
    fi
done
echo "[INITRAMFS] Loading FAT module directly..."
if [ -d /lib/modules/{self.kernel_release}/kernel/fs/fat ]; then
    for m in /lib/modules/{self.kernel_release}/kernel/fs/fat/*.ko*; do
        [ -f "$m" ] && insmod "$m" 2>/dev/null && echo "[INITRAMFS] Loaded: $m"
    done
fi
modprobe fat 2>/dev/null || true
modprobe vfat 2>/dev/null || true
modprobe nls_utf8 2>/dev/null || true
modprobe nls_iso8859_1 2>/dev/null || true
modprobe nls_cp437 2>/dev/null || true
modprobe cdrom 2>/dev/null || true
modprobe sr_mod 2>/dev/null || true
modprobe isofs 2>/dev/null || true
modprobe squashfs 2>/dev/null || true
modprobe loop 2>/dev/null || true
modprobe ext4 2>/dev/null || true
modprobe nvme 2>/dev/null || true
modprobe ahci 2>/dev/null || true
modprobe virtio_blk 2>/dev/null || true
modprobe sd_mod 2>/dev/null || true
echo "[INITRAMFS] Waiting for boot device..."
ROOT_DEVICE=""
for attempt in $(seq 1 30); do
    for dev in /dev/sr* /dev/vd* /dev/nvme* /dev/sd* /dev/hd*; do
        [ ! -b "$dev" ] && continue
        echo "[INITRAMFS] Checking $dev"
        if mount -t iso9660 -o ro "$dev" /mnt/test 2>/dev/null; then
            if [ -f /mnt/test/veles/rootfs.squashfs ]; then
                echo "[INITRAMFS] Found VELES root filesystem on $dev"
                ROOT_DEVICE="$dev"
                umount /mnt/test
                break 2
            fi
            umount /mnt/test
        fi
    done
    sleep 1
done
if [ -z "$ROOT_DEVICE" ]; then
    echo "[INITRAMFS] ERROR: VELES root not found."
    exec /bin/sh
fi
echo "[INITRAMFS] Root device: $ROOT_DEVICE"
mount -t iso9660 -o ro "$ROOT_DEVICE" /mnt/boot
echo "[INITRAMFS] Mounting VELES SquashFS..."
mount -t squashfs -o ro /mnt/boot/veles/rootfs.squashfs /newroot
if [ ! -x /newroot/sbin/veles-init ]; then
    echo "[INITRAMFS] ERROR: VELES init not found."
    exec /bin/sh
fi
mkdir -p /newroot/proc /newroot/sys /newroot/dev /newroot/run
mount --move /proc /newroot/proc
mount --move /sys /newroot/sys
mount --move /dev /newroot/dev
mount --move /run /newroot/run
echo "[INITRAMFS] VELES root ready."
if [ -x /newroot/opt/veles/.venv/bin/python ] && [ -f /newroot/installer/image/installer.py ]; then
    echo "[INITRAMFS] Running VELES installer..."
    exec chroot /newroot /opt/veles/.venv/bin/python /installer/image/installer.py
else
    echo "[INITRAMFS] Starting VELES OS..."
    exec /bin/switch_root /newroot /sbin/veles-init
fi
""", encoding="utf-8")
        init.chmod(0o755)
        return init

    def build(self):
        print("[INITRAMFS] Building VELES initramfs...")
        self.validate_rootfs()
        self.validate_kernel()
        self.validate_environment()
        print(f"[INITRAMFS] Kernel: {self.kernel_path}")
        print(f"[INITRAMFS] Kernel release: {self.kernel_release}")
        self.prepare_workspace()
        self.install_busybox()
        self.create_busybox_links()
        self.create_dhcp_script()
        self.install_kernel_modules()
        self.generate_module_dependencies()
        self.create_init()
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        if self.output_path.exists():
            self.output_path.unlink()
        print("[INITRAMFS] Creating compressed initramfs...")
        subprocess.run(["sh", "-c", f"cd {self.work_root} && find . -print0 | cpio --null -o -H newc | gzip -9 > {self.output_path}"], check=True)
        self.built = True
        print(f"[INITRAMFS] VELES initramfs ready: {self.output_path}")
        return self.output_path

    def validate(self):
        if not self.built:
            raise RuntimeError("Initramfs not built.")
        if not self.output_path.exists() or not self.output_path.is_file():
            raise RuntimeError("Initramfs missing.")
        if self.output_path.stat().st_size <= 0:
            raise RuntimeError("Initramfs empty.")
        return {"valid": True, "initramfs": str(self.output_path), "size": self.output_path.stat().st_size}

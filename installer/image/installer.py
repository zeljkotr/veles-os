"""
VELES OS Installer - AUTOMATSKI BOOT
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path

def main():
    print("=" * 60)
    print(" VELES OS INSTALLER")
    print("=" * 60)
    
    print("\nDetecting disks...")
    result = subprocess.run(["lsblk", "-d", "-o", "NAME,SIZE,TYPE", "-n"], 
                           capture_output=True, text=True)
    disks = []
    for line in result.stdout.splitlines():
        if "disk" in line:
            parts = line.split()
            disks.append({"name": parts[0], "size": parts[1]})
    
    if not disks:
        print("No disks found!")
        return 1
    
    print("\nAvailable disks:")
    for i, disk in enumerate(disks):
        print(f"  {i+1}. /dev/{disk['name']} ({disk['size']})")
    
    choice = input("\nSelect disk number for VELES installation: ")
    try:
        idx = int(choice) - 1
        disk_name = disks[idx]["name"]
    except:
        print("Invalid selection.")
        return 1
    
    print(f"\nWARNING: ALL DATA ON THE SELECTED DISK WILL BE ERASED.")
    print(f"\nSelected disk: /dev/{disk_name} ({disks[idx]['size']})")
    
    confirm = input("\nType INSTALL to continue: ").strip()
    if confirm != "INSTALL":
        print("Installation cancelled.")
        return 1
    
    print(f"\n[1/6] Partitioning disk...")
    subprocess.run(["parted", "-s", f"/dev/{disk_name}", "mklabel", "gpt"], check=True)
    subprocess.run(["parted", "-s", f"/dev/{disk_name}", "mkpart", "EFI", "fat32", "1MiB", "513MiB"], check=True)
    subprocess.run(["parted", "-s", f"/dev/{disk_name}", "set", "1", "esp", "on"], check=True)
    subprocess.run(["parted", "-s", f"/dev/{disk_name}", "mkpart", "root", "ext4", "513MiB", "100%"], check=True)
    subprocess.run(["partprobe", f"/dev/{disk_name}"], check=False)
    
    efi_part = f"/dev/{disk_name}1"
    root_part = f"/dev/{disk_name}2"
    
    print("\n[2/6] Formatting partitions...")
    subprocess.run(["mkfs.fat", "-F32", "-n", "VELES_EFI", efi_part], capture_output=True, check=True)
    subprocess.run(["mkfs.ext4", "-F", "-L", "VELES_ROOT", root_part], capture_output=True, check=True)
    
    print("\n[3/6] Mounting partitions...")
    subprocess.run(["mkdir", "-p", "/mnt"], check=True)
    subprocess.run(["mount", root_part, "/mnt"], check=True)
    
    efi_mount = "/mnt/boot/efi"
    subprocess.run(["mkdir", "-p", efi_mount], check=True)
    subprocess.run(["mount", efi_part, efi_mount], check=True)
    
    print("\n[4/6] Installing VELES OS...")
    subprocess.run(["rsync", "-a", "--progress", 
                   "--exclude=/proc", "--exclude=/sys", 
                   "--exclude=/dev", "--exclude=/run", "--exclude=/tmp",
                   "--exclude=/opt/veles/testdisk.img",
                   "--exclude=/opt/veles/build.log",
                   "--exclude=/opt/veles/build/",
                   "/", "/mnt/"], check=True)
    
    for d in ["proc", "sys", "dev", "run", "tmp"]:
        subprocess.run(["mkdir", "-p", f"/mnt/{d}"], check=False)
    
    print("\n[5/6] Installing bootloader...")
    for path in ["/dev", "/proc", "/sys"]:
        subprocess.run(["mkdir", "-p", f"/mnt{path}"], check=False)
        subprocess.run(["mount", "--bind", path, f"/mnt{path}"], check=True)
    
    # KOPIRAJ BOOT FAJLOVE IZ SOURCE-A
    print("[INSTALLER] Copying boot files...")
    src_boot = Path("/opt/veles/boot")
    dst_boot = Path("/mnt/boot")
    
    if src_boot.exists():
        for f in src_boot.glob("*"):
            if f.is_file():
                shutil.copy2(f, dst_boot / f.name)
                print(f"[INSTALLER] Copied: {f.name}")
    
    # KREIRAJ GRUB.CFG DIREKTNO - OVO JE KLJUČNO!
    print("[INSTALLER] Creating grub.cfg...")
    grub_cfg = dst_boot / "grub/grub.cfg"
    grub_cfg.parent.mkdir(parents=True, exist_ok=True)
    grub_cfg.write_text("""set timeout=3
set default=0

menuentry "VELES OS" {
    set root=(hd0,2)
    linux /boot/vmlinuz root=/dev/vda2 console=tty0 console=ttyS0,115200
    initrd /boot/initrd.img
}
""")
    
    print(f"[INSTALLER] grub.cfg created at: {grub_cfg}")
    print(f"[INSTALLER] grub.cfg contents:")
    print(grub_cfg.read_text())
    
    # INSTALIRAJ GRUB
    subprocess.run(["chroot", "/mnt", "grub-install", "--target=x86_64-efi", 
                   "--efi-directory=/boot/efi", "--bootloader-id=VELES", "--recheck"], check=True)
    subprocess.run(["chroot", "/mnt", "update-grub"], check=True)
    
    with open("/mnt/etc/fstab", "w") as f:
        f.write(f"{root_part}  /        ext4  defaults  0 1\n")
        f.write(f"{efi_part}   /boot/efi vfat  defaults  0 2\n")
    
    print("\n[6/6] Cleaning up...")
    subprocess.run(["sync"], check=True)
    time.sleep(3)
    subprocess.run(["umount", "-R", "/mnt"], check=False)
    
    print("\n" + "=" * 60)
    print(" ✅ VELES OS INSTALLATION COMPLETE!")
    print("=" * 60)
    print(f"\nInstalled on /dev/{disk_name}")
    print("\nReboot and remove installation media.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

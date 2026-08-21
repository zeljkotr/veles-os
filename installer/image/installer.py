"""
VELES OS Installer - UEFI
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def main():
    print("=" * 60)
    print(" VELES OS INSTALLER")
    print("=" * 60)
    
    source_rootfs = Path("/")
    if not source_rootfs.exists():
        print("ERROR: Root filesystem not found at /")
        return 1
    
    if not (source_rootfs / "opt/veles/main.py").exists():
        print("ERROR: This doesn't look like a VELES OS root filesystem.")
        return 1
    
    # Ucitaj FAT module
    for m in ["fat", "vfat", "nls_utf8", "nls_iso8859_1", "nls_cp437"]:
        subprocess.run(["modprobe", m], check=False, capture_output=True)
    
    subprocess.run(["mount", "-t", "tmpfs", "tmpfs", "/mnt"], check=False)
    
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
        print(f"  {i+1}. /dev/{disk['name']} - {disk['size']}")
    
    choice = input("\nSelect disk number (1-{}): ".format(len(disks)))
    try:
        idx = int(choice) - 1
        disk_name = disks[idx]["name"]
    except:
        print("Invalid selection.")
        return 1
    
    print(f"\nInstalling on /dev/{disk_name}...")
    confirm = input("This will DESTROY all data. Continue? (yes/no): ").strip().lower()
    if confirm not in ["yes", "y"]:
        print("Cancelled.")
        return 1
    
    print(f"\n[1/5] Partitioning /dev/{disk_name}...")
    subprocess.run(["parted", "-s", f"/dev/{disk_name}", "mklabel", "gpt"], check=True)
    subprocess.run(["parted", "-s", f"/dev/{disk_name}", "mkpart", "EFI", "fat32", "1MiB", "501MiB"], check=True)
    subprocess.run(["parted", "-s", f"/dev/{disk_name}", "set", "1", "esp", "on"], check=True)
    subprocess.run(["parted", "-s", f"/dev/{disk_name}", "mkpart", "root", "ext4", "501MiB", "100%"], check=True)
    
    efi_part = f"/dev/{disk_name}1"
    root_part = f"/dev/{disk_name}2"
    
    print("\n[2/5] Formatting partitions...")
    subprocess.run(["mkfs.fat", "-F32", efi_part], capture_output=True, check=True)
    subprocess.run(["mkfs.ext4", "-L", "VELES_ROOT", root_part], capture_output=True, check=True)
    
    print("\n[3/5] Copying VELES OS...")
    root_mount = "/mnt/veles-root"
    os.makedirs(root_mount, exist_ok=True)
    subprocess.run(["mount", root_part, root_mount], check=True)
    
    subprocess.run(["rsync", "-a", "--progress", 
                   "--exclude=/mnt", "--exclude=/proc", "--exclude=/sys", 
                   "--exclude=/dev", "--exclude=/run", "--exclude=/tmp",
                   "--exclude=/opt/veles/testdisk.img",
                   "--exclude=/opt/veles/build.log",
                   "--exclude=/opt/veles/build/",
                   "/", f"{root_mount}/"], check=True)
    
    for d in ["proc", "sys", "dev", "run", "tmp"]:
        os.makedirs(f"{root_mount}/{d}", exist_ok=True)
    
    print("\n[4/5] Installing bootloader...")
    efi_mount = f"{root_mount}/boot/efi"
    os.makedirs(efi_mount, exist_ok=True)
    
    # Mount EFI - sada bi trebalo da radi sa FAT modulom
    subprocess.run(["mount", "-t", "vfat", efi_part, efi_mount], check=True)
    
    for path in ["/dev", "/proc", "/sys"]:
        os.makedirs(f"{root_mount}{path}", exist_ok=True)
        subprocess.run(["mount", "--bind", path, f"{root_mount}{path}"], check=True)
    
    subprocess.run(["chroot", root_mount, "grub-install", "--target=x86_64-efi", 
                   "--efi-directory=/boot/efi", "--bootloader-id=VELES", "--recheck"], check=True)
    subprocess.run(["chroot", root_mount, "update-grub"], check=True)
    
    with open(f"{root_mount}/etc/fstab", "w") as f:
        f.write(f"{root_part}  /        ext4  defaults  0 1\n")
        f.write(f"{efi_part}   /boot/efi vfat  defaults  0 2\n")
    
    print("\n[5/5] Cleaning up...")
    subprocess.run(["umount", "-R", root_mount], check=False)
    
    print("\n" + "=" * 60)
    print(" ✅ VELES OS INSTALLATION COMPLETE!")
    print("=" * 60)
    print(f"\nInstalled on /dev/{disk_name}")
    print("\nReboot and remove installation media.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

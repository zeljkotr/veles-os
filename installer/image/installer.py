cat > ~/veles-os/installer/image/installer.py << 'EOF'
"""
VELES OS Installer

Installs VELES OS from the live ISO to a target disk.
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path

class VELESInstaller:
    def __init__(self):
        self.source_rootfs = Path("/run/rootfs")
        self.target_disk = None
        self.efi_partition = None
        self.root_partition = None
        self.root_mount = Path("/mnt/veles-root")
        
    def detect_disks(self):
        """Detect available disks for installation."""
        result = subprocess.run(
            ["lsblk", "-d", "-o", "NAME,SIZE,TYPE,MODEL", "-n"],
            capture_output=True,
            text=True
        )
        disks = []
        for line in result.stdout.splitlines():
            if "disk" in line:
                parts = line.split()
                disks.append({
                    "name": parts[0],
                    "size": parts[1],
                    "model": " ".join(parts[3:]) if len(parts) > 3 else "Unknown"
                })
        return disks
    
    def partition_disk(self, disk):
        """Create partitions: EFI (500MB) + root (rest)."""
        print(f"[INSTALLER] Partitioning /dev/{disk}...")
        
        # Clear existing partition table
        subprocess.run(["dd", "if=/dev/zero", f"of=/dev/{disk}", "bs=1M", "count=1"], 
                      capture_output=True, check=False)
        
        # Create GPT partition table
        subprocess.run(["parted", "-s", f"/dev/{disk}", "mklabel", "gpt"], check=True)
        
        # Create EFI partition (500MB)
        subprocess.run([
            "parted", "-s", f"/dev/{disk}",
            "mkpart", "EFI", "fat32", "1MiB", "501MiB"
        ], check=True)
        subprocess.run([
            "parted", "-s", f"/dev/{disk}", "set", "1", "esp", "on"
        ], check=True)
        
        # Create root partition (rest of disk)
        subprocess.run([
            "parted", "-s", f"/dev/{disk}",
            "mkpart", "root", "ext4", "501MiB", "100%"
        ], check=True)
        
        self.efi_partition = f"/dev/{disk}1"
        self.root_partition = f"/dev/{disk}2"
        
        print(f"[INSTALLER] EFI partition: {self.efi_partition}")
        print(f"[INSTALLER] Root partition: {self.root_partition}")
    
    def format_partitions(self):
        """Format EFI as FAT32, root as ext4."""
        print("[INSTALLER] Formatting partitions...")
        
        # Format EFI
        subprocess.run(["mkfs.fat", "-F32", self.efi_partition], 
                      capture_output=True, check=True)
        
        # Format root
        subprocess.run(["mkfs.ext4", "-L", "VELES_ROOT", self.root_partition], 
                      capture_output=True, check=True)
    
    def copy_rootfs(self):
        """Copy root filesystem to target disk."""
        print("[INSTALLER] Copying VELES OS to disk...")
        
        # Create mount point
        self.root_mount.mkdir(parents=True, exist_ok=True)
        
        # Mount root partition
        subprocess.run(["mount", self.root_partition, str(self.root_mount)], check=True)
        
        # Copy rootfs from SquashFS
        subprocess.run([
            "rsync", "-a", "--progress",
            "--exclude=/proc", "--exclude=/sys", "--exclude=/dev",
            "--exclude=/run", "--exclude=/tmp",
            str(self.source_rootfs) + "/",
            str(self.root_mount) + "/"
        ], check=True)
        
        # Create necessary directories in target
        for d in ["proc", "sys", "dev", "run", "tmp"]:
            (self.root_mount / d).mkdir(parents=True, exist_ok=True)
        
        return self.root_mount
    
    def install_grub(self):
        """Install GRUB bootloader to target disk."""
        print("[INSTALLER] Installing GRUB bootloader...")
        
        # Mount necessary filesystems
        for path in ["/dev", "/proc", "/sys", "/run"]:
            target_path = self.root_mount / path.lstrip("/")
            target_path.mkdir(parents=True, exist_ok=True)
            subprocess.run(["mount", "--bind", path, str(target_path)], check=True)
        
        # Mount EFI partition
        efi_mount = self.root_mount / "boot" / "efi"
        efi_mount.mkdir(parents=True, exist_ok=True)
        subprocess.run(["mount", self.efi_partition, str(efi_mount)], check=True)
        
        # Install GRUB (UEFI)
        subprocess.run([
            "chroot", str(self.root_mount),
            "grub-install", "--target=x86_64-efi",
            "--efi-directory=/boot/efi",
            "--bootloader-id=VELES",
            "--recheck"
        ], check=True)
        
        # Generate GRUB config
        subprocess.run([
            "chroot", str(self.root_mount),
            "update-grub"
        ], check=True)
    
    def configure_system(self):
        """Configure the installed system."""
        print("[INSTALLER] Configuring system...")
        
        # Create fstab
        fstab = f"""# /etc/fstab: static file system information.
# VELES OS

{self.root_partition}  /        ext4  defaults  0 1
{self.efi_partition}   /boot/efi vfat  defaults  0 2
proc                   /proc    proc  defaults  0 0
sysfs                  /sys     sysfs defaults  0 0
devtmpfs               /dev     devtmpfs defaults  0 0
"""
        with open(self.root_mount / "etc" / "fstab", "w") as f:
            f.write(fstab)
        
        # Set hostname
        with open(self.root_mount / "etc" / "hostname", "w") as f:
            f.write("veles-os\n")
        
        # Configure /etc/hosts
        hosts = """127.0.0.1 localhost
127.0.1.1 veles-os

::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
"""
        with open(self.root_mount / "etc" / "hosts", "w") as f:
            f.write(hosts)
    
    def cleanup(self):
        """Cleanup mount points."""
        print("[INSTALLER] Cleaning up...")
        
        # Unmount everything
        subprocess.run(["umount", "-R", str(self.root_mount)], check=False)
        
        print("[INSTALLER] Cleanup complete.")
    
    def install(self):
        """Run full installation."""
        print("=" * 70)
        print("                    VELES OS INSTALLER")
        print("=" * 70)
        print()
        
        # Check if running from live ISO
        if not self.source_rootfs.exists():
            print("[ERROR] Not running from VELES live ISO.")
            print("Please boot from VELES OS installation media.")
            return False
        
        # 1. Detect disks
        print("[1/6] Detecting available disks...")
        disks = self.detect_disks()
        
        if not disks:
            print("[ERROR] No disks found!")
            return False
        
        print("\nAvailable disks:")
        for i, disk in enumerate(disks):
            print(f"  {i+1}. /dev/{disk['name']} - {disk['size']} - {disk['model']}")
        print()
        
        # 2. Select disk
        try:
            choice = input("Select disk number (or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                print("Installation cancelled.")
                return False
            disk_num = int(choice) - 1
            if disk_num < 0 or disk_num >= len(disks):
                print("Invalid selection.")
                return False
            disk_name = disks[disk_num]["name"]
        except ValueError:
            print("Invalid selection.")
            return False
        
        self.target_disk = disk_name
        
        # 3. Confirm installation
        print(f"\n[2/6] Target disk: /dev/{self.target_disk}")
        print("WARNING: This will DESTROY all data on this disk!")
        confirm = input("Continue with installation? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Installation cancelled.")
            return False
        
        # 4. Partition and format
        print("\n[3/6] Partitioning and formatting disk...")
        self.partition_disk(self.target_disk)
        self.format_partitions()
        
        # 5. Copy system
        print("\n[4/6] Copying VELES OS to disk...")
        self.copy_rootfs()
        
        # 6. Install bootloader
        print("\n[5/6] Installing bootloader...")
        self.install_grub()
        
        # 7. Configure system
        print("\n[6/6] Configuring system...")
        self.configure_system()
        
        # Cleanup
        self.cleanup()
        
        print()
        print("=" * 70)
        print("             ✅ VELES OS INSTALLATION COMPLETE!")
        print("=" * 70)
        print()
        print(f"VELES OS has been installed on /dev/{self.target_disk}")
        print()
        print("You can now reboot and remove the installation media.")
        print()
        
        # Ask for reboot
        reboot = input("Reboot now? (y/n): ").strip().lower()
        if reboot == 'y':
            print("Rebooting in 5 seconds...")
            time.sleep(5)
            subprocess.run(["reboot"])
        
        return True

def main():
    """Main entry point for VELES installer."""
    installer = VELESInstaller()
    
    try:
        success = installer.install()
        if not success:
            print("\nInstallation failed or was cancelled.")
            print("You can restart the installer by running:")
            print("  python3 /installer/image/installer.py")
            return 1
        return 0
    except KeyboardInterrupt:
        print("\n\nInstallation interrupted by user.")
        installer.cleanup()
        return 1
    except Exception as e:
        print(f"\n[ERROR] Installation failed: {e}")
        import traceback
        traceback.print_exc()
        installer.cleanup()
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF
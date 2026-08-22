"""
VELES OS Root Filesystem Builder

Builds and validates the Linux userspace used by the VELES OS
bootable image and installer.

RootFSBuilder is the authoritative builder for the VELES root
filesystem. Higher-level image builders consume its structured
validation result.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


class RootFSBuilder:
    """Builds a self-contained VELES Linux root filesystem."""

    DEFAULT_ARCH = "amd64"

    DEFAULT_COMPONENTS = (
        "main",
        "universe",
    )

    DEFAULT_INCLUDE = (
        "python3",
        "python3-venv",
        "python3-pip",
        "ca-certificates",
        "iproute2",
        "procps",
        "util-linux",
        "kmod",
        "udev",
        "systemd-sysv",
        "mount",
        "wget",
        "rsync",
        "parted",
        "dosfstools",
    )

    # --------------------------------------------------
    # SOURCE EXCLUSIONS
    # --------------------------------------------------

    EXCLUDED_DIRECTORIES = {
        ".git",
        ".venv",
        "__pycache__",
        "build",
        "source",
    }

    EXCLUDED_FILES = {
        ".DS_Store",
        ".gitignore",
        "build_image.py",
        "build_veles_os.sh",
        "testdisk.img",
        "build.log",
        "build_output.log",
        "tree.txt",
        "struktura.txt",
    }

    EXCLUDED_FILE_PATTERNS = (
        "wget-log*",
        "*.backup*",
        "*.bak*",
        "*.save",
        "*.before-*",
    )

    def __init__(
        self,
        source_root,
        rootfs_root,
        distribution="ubuntu",
        codename="plucky",
        mirror=None,
        architecture=None,
        components=None,
    ):
        self.source_root = (
            Path(source_root)
            .expanduser()
            .resolve()
        )

        self.rootfs_root = (
            Path(rootfs_root)
            .expanduser()
            .resolve()
        )

        self.distribution = distribution
        self.codename = codename

        self.mirror = (
            mirror
            or "http://archive.ubuntu.com/ubuntu"
        )

        self.architecture = (
            architecture
            or self.DEFAULT_ARCH
        )

        self.components = tuple(
            components
            or self.DEFAULT_COMPONENTS
        )

        self.built = False

    # --------------------------------------------------
    # BUILD
    # --------------------------------------------------

    def build(self):
        """Build the complete VELES Linux root filesystem."""

        print(
            "[ROOTFS] Building VELES OS root filesystem..."
        )

        self.validate_source()
        self.validate_environment()

        if self.rootfs_root.exists():
            print(
                "[ROOTFS] Removing previous root filesystem..."
            )

            shutil.rmtree(
                self.rootfs_root
            )

        self.rootfs_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.build_base_system()
        self.prepare_directories()
        self.copy_veles_source()
        self.install_python_dependencies()
        self.create_runtime_configuration()
        self.create_runtime_entrypoint()
        self.validate_runtime()

        self.built = True

        print(
            "[ROOTFS] VELES root filesystem ready: "
            f"{self.rootfs_root}"
        )

        return self.rootfs_root

    # --------------------------------------------------
    # SOURCE
    # --------------------------------------------------

    def validate_source(self):
        """Validate the VELES OS source tree."""

        if not self.source_root.exists():
            raise FileNotFoundError(
                "VELES source root does not exist: "
                f"{self.source_root}"
            )

        if not self.source_root.is_dir():
            raise NotADirectoryError(
                "VELES source root is not a directory: "
                f"{self.source_root}"
            )

        required = (
            "boot",
            "kernel",
            "system",
            "core",
            "services",
            "desktop",
            "main.py",
            "requirements.txt",
        )

        missing = [
            name
            for name in required
            if not (self.source_root / name).exists()
        ]

        if missing:
            raise RuntimeError(
                "Invalid VELES OS source tree. "
                f"Missing: {', '.join(missing)}"
            )

        return True

    # --------------------------------------------------
    # ENVIRONMENT
    # --------------------------------------------------

    def validate_environment(self):
        """Validate host tools required to build the rootfs."""

        if os.geteuid() != 0:
            raise PermissionError(
                "Root filesystem building requires root privileges."
            )

        if shutil.which("debootstrap") is None:
            raise RuntimeError(
                "debootstrap was not found. "
                "Install: sudo apt install debootstrap"
            )

        return True

    # --------------------------------------------------
    # BASE SYSTEM
    # --------------------------------------------------

    def build_base_system(self):
        """Create the minimal Linux userspace using debootstrap."""

        print(
            "[ROOTFS] Building Linux base system..."
        )

        print(
            f"[ROOTFS] Distribution: {self.distribution}"
        )

        print(
            f"[ROOTFS] Codename: {self.codename}"
        )

        print(
            f"[ROOTFS] Architecture: {self.architecture}"
        )

        print(
            f"[ROOTFS] Mirror: {self.mirror}"
        )

        include_packages = ",".join(
            self.DEFAULT_INCLUDE
        )

        components = ",".join(
            self.components
        )

        command = [
            "debootstrap",
            "--variant=minbase",
            f"--arch={self.architecture}",
            f"--components={components}",
            f"--include={include_packages}",
            "--no-check-gpg",
            self.codename,
            str(self.rootfs_root),
            self.mirror,
        ]

        print(
            "[ROOTFS] Running: "
            f"{' '.join(command)}"
        )

        try:
            subprocess.run(
                command,
                check=True,
            )

        except subprocess.CalledProcessError as error:
            print(
                "[ROOTFS] Greška u debootstrap-u: "
                f"{error}"
            )

            print(
                "[ROOTFS] Pokušavam sa drugim mirror-om..."
            )

            fallback_command = command.copy()

            fallback_command[-1] = (
                "http://mirror.ubuntu.com/ubuntu"
            )

            subprocess.run(
                fallback_command,
                check=True,
            )

        print(
            "[ROOTFS] Base system installed successfully!"
        )

        return self.rootfs_root

    # --------------------------------------------------
    # DIRECTORIES
    # --------------------------------------------------

    def prepare_directories(self):
        """Create runtime directories."""

        directories = (
            "dev",
            "proc",
            "sys",
            "run",
            "tmp",
            "var",
            "var/log",
            "var/tmp",
            "var/lib",
            "var/lib/ollama",
            "var/lib/veles",
            "opt",
            "opt/veles",
            "etc/veles",
            "usr/local/bin",
            "sbin",
            "boot/efi",
            "usr/share/xsessions",
            "etc/lightdm",
            "etc/lightdm/lightdm.conf.d",
            "etc/xdg/openbox",
        )

        for relative in directories:
            (
                self.rootfs_root / relative
            ).mkdir(
                parents=True,
                exist_ok=True,
            )

        return True

    # --------------------------------------------------
    # SOURCE COPY
    # --------------------------------------------------

    def _excluded(self, relative):
        """Return True when a source path must be excluded."""

        if any(
            part in self.EXCLUDED_DIRECTORIES
            for part in relative.parts
        ):
            return True

        if relative.name in self.EXCLUDED_FILES:
            return True

        if any(
            relative.match(pattern)
            for pattern in self.EXCLUDED_FILE_PATTERNS
        ):
            return True

        return False

    def _copytree_ignore(self, directory, names):
        """
        Return names that must be excluded by copytree.

        copytree() does not pass through _excluded(), so installer
        and boot trees require an explicit ignore callback.
        """

        ignored = set()

        for name in names:
            relative = Path(name)

            if self._excluded(relative):
                ignored.add(name)

        return ignored

    def copy_veles_source(self):
        """Copy the VELES runtime into the Linux rootfs."""

        destination_root = (
            self.rootfs_root
            / "opt"
            / "veles"
        )

        print(
            "[ROOTFS] Copying VELES OS source tree..."
        )

        for source in self.source_root.rglob("*"):
            relative = source.relative_to(
                self.source_root
            )

            if self._excluded(relative):
                continue

            destination = (
                destination_root / relative
            )

            if source.is_dir():
                destination.mkdir(
                    parents=True,
                    exist_ok=True,
                )

            elif source.is_file():
                destination.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                shutil.copy2(
                    source,
                    destination,
                )

        installer_src = (
            self.source_root / "installer"
        )

        installer_dst = (
            self.rootfs_root / "installer"
        )

        if installer_src.exists():
            print(
                "[ROOTFS] Copying installer..."
            )

            if installer_dst.exists():
                shutil.rmtree(
                    installer_dst
                )

            shutil.copytree(
                installer_src,
                installer_dst,
                ignore=self._copytree_ignore,
            )

        boot_src = (
            self.source_root / "boot"
        )

        boot_dst = (
            self.rootfs_root / "boot"
        )

        if boot_src.exists():
            print(
                "[ROOTFS] Copying boot files..."
            )

            shutil.copytree(
                boot_src,
                boot_dst,
                dirs_exist_ok=True,
                ignore=self._copytree_ignore,
            )

        return destination_root

    # --------------------------------------------------
    # PYTHON DEPENDENCIES
    # --------------------------------------------------

    def install_python_dependencies(self):
        """Install VELES Python dependencies into the target rootfs."""

        requirements_path = (
            self.rootfs_root
            / "opt"
            / "veles"
            / "requirements.txt"
        )

        python_path = (
            self.rootfs_root
            / "usr"
            / "bin"
            / "python3"
        )

        if not requirements_path.is_file():
            raise RuntimeError(
                "VELES requirements.txt was not copied into "
                f"the root filesystem: {requirements_path}"
            )

        if not python_path.exists():
            raise RuntimeError(
                "Python runtime was not found in VELES root filesystem: "
                f"{python_path}"
            )

        print(
            "[ROOTFS] Installing VELES Python dependencies..."
        )

        command = [
            "chroot",
            str(self.rootfs_root),
            "/usr/bin/python3",
            "-m",
            "pip",
            "install",
            "--break-system-packages",
            "--no-cache-dir",
            "--disable-pip-version-check",
            "-r",
            "/opt/veles/requirements.txt",
        ]

        print(
            "[ROOTFS] Running: "
            f"{' '.join(command)}"
        )

        environment = os.environ.copy()

        environment.update(
            {
                "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )

        try:
            subprocess.run(
                command,
                check=True,
                env=environment,
            )

        except subprocess.CalledProcessError as error:
            raise RuntimeError(
                "Failed to install VELES Python dependencies "
                f"from {requirements_path}"
            ) from error

        print(
            "[ROOTFS] VELES Python dependencies installed successfully!"
        )

        return True

    # --------------------------------------------------
    # RUNTIME CONFIGURATION
    # --------------------------------------------------

    def create_runtime_configuration(self):
        """Create the VELES system runtime environment file."""

        config_path = (
            self.rootfs_root
            / "etc"
            / "veles"
            / "veles.env"
        )

        config_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        config = """export VELES_DATABASE_URL=postgresql://veles:veles@localhost/veles
export PGPASSWORD=veles
export VELES_OLLAMA_HOST=http://127.0.0.1:11434
export VELES_OLLAMA_MODEL=qwen2.5:7b
"""

        config_path.write_text(
            config,
            encoding="utf-8",
        )

        config_path.chmod(
            0o600
        )

        print(
            "[ROOTFS] Runtime configuration created."
        )

        return config_path

    # --------------------------------------------------
    # RUNTIME ENTRYPOINT
    # --------------------------------------------------

    def create_runtime_entrypoint(self):
        """Create the VELES root filesystem runtime entrypoint."""

        init_path = (
            self.rootfs_root
            / "sbin"
            / "veles-init"
        )

        init_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        init_path.write_text(
            """#!/bin/sh
set -eu

echo "========================================"
echo "           VELES OS INIT"
echo "========================================"

echo "[INIT] Starting VELES OS..."

mount -t proc proc /proc || true
mount -t sysfs sysfs /sys || true
mount -t devtmpfs devtmpfs /dev || true

mkdir -p /run /tmp

mount -t tmpfs -o mode=0755 tmpfs /run
mount -t tmpfs -o mode=1777 tmpfs /tmp

if [ -f /etc/veles/veles.env ]; then
    . /etc/veles/veles.env
fi

echo "[INIT] VELES OS ready."

cd /opt/veles
exec /usr/bin/python3 /opt/veles/main.py
""",
            encoding="utf-8",
        )

        init_path.chmod(
            0o755
        )

        print(
            "[ROOTFS] Runtime entrypoint created."
        )

        return init_path

    # --------------------------------------------------
    # RUNTIME VALIDATION
    # --------------------------------------------------

    def validate_runtime(self):
        """Validate that the runtime files are physically present."""

        required = (
            self.rootfs_root
            / "sbin"
            / "veles-init",
            self.rootfs_root
            / "etc"
            / "veles"
            / "veles.env",
        )

        missing = [
            str(path)
            for path in required
            if not path.exists()
        ]

        if missing:
            raise RuntimeError(
                "VELES runtime is incomplete. "
                f"Missing: {', '.join(missing)}"
            )

        return True

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    def validate(self):
        """Validate the completed VELES Linux root filesystem."""

        if not self.built:
            raise RuntimeError(
                "VELES OS root filesystem has not been built."
            )

        if not self.rootfs_root.exists():
            raise RuntimeError(
                "VELES OS root filesystem directory does not exist: "
                f"{self.rootfs_root}"
            )

        runtime_result = self.validate_runtime()

        if not runtime_result:
            raise RuntimeError(
                "VELES OS runtime validation failed."
            )

        python_path = (
            self.rootfs_root
            / "usr"
            / "bin"
            / "python3"
        )

        if not python_path.exists():
            raise RuntimeError(
                "Python runtime was not found in VELES root filesystem: "
                f"{python_path}"
            )

        return {
            "valid": True,
            "rootfs": str(
                self.rootfs_root
            ),
            "python": str(
                python_path
            ),
        }
"""
VELES OS Root Filesystem Builder

Builds a self-contained Linux root filesystem for VELES OS.

The resulting filesystem contains:
- a minimal Debian/Ubuntu userspace
- Python runtime
- VELES OS source/runtime tree
- VELES Python dependencies
- Ollama AI runtime
- a standalone VELES runtime entrypoint
- generic VELES runtime configuration

This module does not copy host-specific credentials into the
final VELES OS image.
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
        "iputils-ping",
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
        "grub-efi-amd64",
        "grub-efi-amd64-bin",
        "grub-efi-amd64-signed",
        "efibootmgr",
    )

    EXCLUDED_DIRECTORIES = {
        ".git",
        "__pycache__",
        "build",
    }

    EXCLUDED_FILES = {
        ".DS_Store",
    }

    HOST_OLLAMA_BINARY = Path(
        "/usr/local/bin/ollama"
    )

    def __init__(
        self,
        source_root,
        rootfs_root,
        distribution="ubuntu",
        codename=None,
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
        self.mirror = mirror
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
    # VALIDATION
    # --------------------------------------------------

    def validate_source(self):
        """Validate the VELES OS source tree."""

        if not self.source_root.exists():
            raise FileNotFoundError(
                f"VELES source root does not exist: "
                f"{self.source_root}"
            )

        if not self.source_root.is_dir():
            raise NotADirectoryError(
                f"VELES source root is not a directory: "
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
            if not (
                self.source_root / name
            ).exists()
        ]

        if missing:
            raise RuntimeError(
                "Invalid VELES OS source tree. "
                f"Missing: {', '.join(missing)}"
            )

        return True

    def validate_environment(self):
        """Validate host tools required to build the rootfs."""

        if os.geteuid() != 0:
            raise PermissionError(
                "Root filesystem building requires root privileges."
            )

        if shutil.which("debootstrap") is None:
            raise RuntimeError(
                "debootstrap was not found."
            )

        if not self.HOST_OLLAMA_BINARY.is_file():
            raise FileNotFoundError(
                "Ollama binary was not found at: "
                f"{self.HOST_OLLAMA_BINARY}"
            )

        return True

    # --------------------------------------------------
    # DEBOOTSTRAP
    # --------------------------------------------------

    def build_base_system(self):
        """Create the minimal Linux userspace."""

        if self.codename is None:
            raise ValueError(
                "A Linux distribution codename must be provided."
            )

        command = [
            "debootstrap",
            "--variant=minbase",
            f"--arch={self.architecture}",
            "--components=" + ",".join(
                self.components
            ),
            "--include=" + ",".join(
                self.DEFAULT_INCLUDE
            ),
            self.codename,
            str(self.rootfs_root),
        ]

        if self.mirror:
            command.append(self.mirror)

        print(
            "[ROOTFS] Building Linux base system..."
        )

        print(
            "[ROOTFS] Distribution: "
            f"{self.distribution}"
        )

        print(
            "[ROOTFS] Codename: "
            f"{self.codename}"
        )

        print(
            "[ROOTFS] Architecture: "
            f"{self.architecture}"
        )

        print(
            "[ROOTFS] Components: "
            + ", ".join(self.components)
        )

        subprocess.run(
            command,
            check=True,
        )

        return self.rootfs_root

    # --------------------------------------------------
    # FILESYSTEM
    # --------------------------------------------------

    def prepare_directories(self):
        """Create runtime directories required by Linux and VELES."""

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
            "installer",
        )

        for relative in directories:
            path = self.rootfs_root / relative

            path.mkdir(
                parents=True,
                exist_ok=True,
            )

        return True

    # --------------------------------------------------
    # VELES SOURCE
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

        return False

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

        installer_src = self.source_root / "installer"
        installer_dst = self.rootfs_root / "installer"

        if installer_src.exists():
            print(
                "[ROOTFS] Copying VELES installer to /installer..."
            )

            if installer_dst.exists():
                shutil.rmtree(installer_dst)

            shutil.copytree(
                installer_src,
                installer_dst,
            )

            install_sh = installer_dst / "install.sh"

            if install_sh.exists():
                install_sh.chmod(0o755)

        return destination_root

    # --------------------------------------------------
    # OLLAMA
    # --------------------------------------------------

    def install_ollama(self):
        """Install the Ollama runtime into the VELES rootfs."""

        source = self.HOST_OLLAMA_BINARY

        destination = (
            self.rootfs_root
            / "usr"
            / "local"
            / "bin"
            / "ollama"
        )

        if not source.is_file():
            raise FileNotFoundError(
                "Ollama binary was not found at: "
                f"{source}"
            )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(
            "[ROOTFS] Installing Ollama AI runtime..."
        )

        shutil.copy2(
            source,
            destination,
        )

        destination.chmod(0o755)

        return destination

    # --------------------------------------------------
    # RUNTIME CONFIGURATION
    # --------------------------------------------------

    def create_runtime_configuration(self):
        """
        Create a generic VELES runtime configuration.

        IMPORTANT:

        No database credentials, host addresses, passwords,
        usernames, or other build-host-specific values are
        copied into the final OS image.

        The installer writes the actual runtime configuration
        onto the installed system.
        """

        configuration = """# VELES OS runtime configuration
#
# This file is intentionally generic.
# The VELES installer configures the installed system.

export VELES_DATABASE_URL=""
export PGPASSWORD=""
export VELES_OLLAMA_HOST="http://127.0.0.1:11434"
export VELES_OLLAMA_MODEL="qwen2.5:7b"
"""

        configuration_path = (
            self.rootfs_root
            / "etc"
            / "veles"
            / "veles.env"
        )

        configuration_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        configuration_path.write_text(
            configuration,
            encoding="utf-8",
        )

        configuration_path.chmod(0o600)

        print(
            "[ROOTFS] Generic runtime configuration created."
        )

        return configuration_path

    # --------------------------------------------------
    # PYTHON ENVIRONMENT
    # --------------------------------------------------

    def _rootfs_python(self):
        """Return the Python interpreter inside the rootfs."""

        candidates = (
            self.rootfs_root / "usr" / "bin" / "python3",
            self.rootfs_root / "usr" / "bin" / "python3.14",
            self.rootfs_root / "usr" / "bin" / "python3.13",
            self.rootfs_root / "usr" / "bin" / "python3.12",
            self.rootfs_root / "usr" / "bin" / "python3.11",
        )

        for candidate in candidates:
            if candidate.exists():
                return candidate

        raise FileNotFoundError(
            "No Python 3 interpreter was installed "
            "inside the VELES rootfs."
        )

    def create_python_environment(self):
        """Create a standalone VELES Python environment."""

        python = self._rootfs_python()

        environment = (
            self.rootfs_root
            / "opt"
            / "veles"
            / ".venv"
        )

        if environment.exists():
            shutil.rmtree(environment)

        print(
            "[ROOTFS] Creating standalone VELES Python environment..."
        )

        subprocess.run(
            [
                str(python),
                "-m",
                "venv",
                "--copies",
                "--system-site-packages",
                str(environment),
            ],
            check=True,
        )

        return environment

    def install_python_dependencies(self):
        """Install VELES Python dependencies into the rootfs."""

        requirements = (
            self.rootfs_root
            / "opt"
            / "veles"
            / "requirements.txt"
        )

        if not requirements.is_file():
            raise FileNotFoundError(
                "VELES requirements.txt was not copied."
            )

        python = (
            self.rootfs_root
            / "opt"
            / "veles"
            / ".venv"
            / "bin"
            / "python"
        )

        if not python.exists():
            raise FileNotFoundError(
                "VELES Python environment was not created."
            )

        print(
            "[ROOTFS] Installing VELES Python dependencies..."
        )

        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-cache-dir",
                "-r",
                str(requirements),
            ],
            check=True,
        )

        return True

    # --------------------------------------------------
    # INIT
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

echo
echo "========================================"
echo "           VELES OS INIT"
echo "========================================"
echo

echo "[INIT] Starting VELES OS..."

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

echo "[INIT] Preparing loopback interface..."

if command -v ip >/dev/null 2>&1; then
    ip link set lo up || true
fi

echo "[INIT] Preparing writable /run..."

mkdir -p /run

if ! mountpoint -q /run 2>/dev/null; then
    mount -t tmpfs \\
        -o mode=0755,nosuid,nodev \\
        tmpfs /run
fi

mkdir -p /run/veles

echo "[INIT] Preparing writable /tmp..."

mkdir -p /tmp

if ! mountpoint -q /tmp 2>/dev/null; then
    mount -t tmpfs \\
        -o mode=1777,nosuid,nodev \\
        tmpfs /tmp
fi

chmod 1777 /tmp

echo "[INIT] Preparing kernel filesystems..."

mkdir -p /dev /proc /sys

if ! mountpoint -q /proc 2>/dev/null; then
    mount -t proc proc /proc || true
fi

if ! mountpoint -q /sys 2>/dev/null; then
    mount -t sysfs sysfs /sys || true
fi

if ! mountpoint -q /dev 2>/dev/null; then
    mount -t devtmpfs devtmpfs /dev || true
fi

echo "[INIT] Preparing writable Ollama storage..."

mkdir -p /var/lib/ollama

if ! mountpoint -q /var/lib/ollama 2>/dev/null; then
    mount -t tmpfs \\
        -o mode=0755,nosuid,nodev \\
        tmpfs /var/lib/ollama
fi

export HOME="/run/veles/ollama-home"
mkdir -p "${HOME}"

export OLLAMA_MODELS="/var/lib/ollama"

echo "[INIT] Ollama HOME: ${HOME}"
echo "[INIT] Ollama storage: ${OLLAMA_MODELS}"

if [ ! -f /etc/veles/veles.env ]; then
    echo "[INIT] ERROR: VELES runtime configuration not found."
    exec /bin/sh
fi

echo "[INIT] Loading VELES runtime configuration..."

set -a
. /etc/veles/veles.env
set +a

if [ -z "${VELES_DATABASE_URL:-}" ]; then
    echo "[INIT] ERROR: VELES_DATABASE_URL is not configured."
    echo "[INIT] Configure /etc/veles/veles.env before starting VELES."
    exec /bin/sh
fi

echo "[INIT] VELES runtime configuration loaded."

if [ -x /usr/local/bin/ollama ]; then

    echo "[INIT] Starting Ollama AI runtime..."

    /usr/local/bin/ollama serve \\
        >/run/veles/ollama.log 2>&1 &

    OLLAMA_PID=$!

    echo "[INIT] Ollama PID: ${OLLAMA_PID}"

    echo "[INIT] Waiting for Ollama API..."

    OLLAMA_READY=0

    for _ in $(seq 1 30); do

        if ! kill -0 "${OLLAMA_PID}" 2>/dev/null; then
            break
        fi

        if command -v wget >/dev/null 2>&1; then

            if wget -q -O /dev/null \\
                "${VELES_OLLAMA_HOST:-http://127.0.0.1:11434}/api/tags" \\
                >/dev/null 2>&1; then

                OLLAMA_READY=1
                break
            fi

        fi

        sleep 1
    done

    if [ "${OLLAMA_READY}" -eq 1 ]; then
        echo "[INIT] Ollama AI runtime: READY"
    else
        echo "[INIT] Ollama AI runtime: OFFLINE"
        echo "[INIT] VELES will continue without local AI."
    fi

else

    echo "[INIT] Ollama binary not found."
    echo "[INIT] VELES will continue without local AI."

fi

echo "[INIT] Starting VELES Python runtime..."

if [ ! -x /opt/veles/.venv/bin/python ]; then
    echo "[INIT] ERROR: VELES Python runtime is missing."
    exec /bin/sh
fi

exec /opt/veles/.venv/bin/python /opt/veles/main.py
""",
            encoding="utf-8",
        )

        init_path.chmod(0o755)

        return init_path

    # --------------------------------------------------
    # RUNTIME VALIDATION
    # --------------------------------------------------

    def validate_runtime(self):
        """Validate physical VELES runtime files."""

        python = (
            self.rootfs_root
            / "opt"
            / "veles"
            / ".venv"
            / "bin"
            / "python"
        )

        python3 = (
            self.rootfs_root
            / "opt"
            / "veles"
            / ".venv"
            / "bin"
            / "python3"
        )

        init = (
            self.rootfs_root
            / "sbin"
            / "veles-init"
        )

        environment = (
            self.rootfs_root
            / "etc"
            / "veles"
            / "veles.env"
        )

        ollama = (
            self.rootfs_root
            / "usr"
            / "local"
            / "bin"
            / "ollama"
        )

        required = (
            python,
            python3,
            init,
            environment,
            ollama,
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

        if not python.is_file():
            raise RuntimeError(
                f"VELES Python runtime is not a regular file: {python}"
            )

        if not environment.is_file():
            raise RuntimeError(
                f"VELES runtime configuration is not a regular file: "
                f"{environment}"
            )

        if not ollama.is_file():
            raise RuntimeError(
                f"Ollama runtime is not a regular file: {ollama}"
            )

        if not os.access(ollama, os.X_OK):
            raise RuntimeError(
                f"Ollama runtime is not executable: {ollama}"
            )

        if not init.is_file():
            raise RuntimeError(
                f"VELES init entrypoint is not a regular file: {init}"
            )

        if not os.access(init, os.X_OK):
            raise RuntimeError(
                f"VELES init entrypoint is not executable: {init}"
            )

        return True

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
        self.install_ollama()
        self.create_runtime_configuration()
        self.create_python_environment()
        self.install_python_dependencies()
        self.create_runtime_entrypoint()
        self.validate_runtime()

        self.built = True

        print(
            "[ROOTFS] VELES root filesystem ready: "
            f"{self.rootfs_root}"
        )

        return self.rootfs_root

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    def validate(self):
        """Validate the completed VELES Linux root filesystem."""

        if not self.built:
            raise RuntimeError(
                "VELES OS root filesystem has not been built."
            )

        required = (
            "sbin/veles-init",
            "usr/bin/python3",
            "usr/local/bin/ollama",
            "opt/veles/main.py",
            "opt/veles/boot/bootstrap.py",
            "opt/veles/kernel/runtime.py",
            "opt/veles/system",
            "opt/veles/core",
            "opt/veles/services",
            "opt/veles/desktop",
            "opt/veles/.venv/bin/python",
            "etc/veles/veles.env",
            "var/lib/ollama",
            "installer/image/installer.py",
            "installer/install.sh",
        )

        missing = [
            str(self.rootfs_root / relative)
            for relative in required
            if not (
                self.rootfs_root / relative
            ).exists()
        ]

        if missing:
            raise RuntimeError(
                "Invalid VELES OS root filesystem. "
                f"Missing: {', '.join(missing)}"
            )

        self.validate_runtime()

        return {
            "valid": True,
            "rootfs": str(self.rootfs_root),
            "entrypoint": str(
                self.rootfs_root
                / "sbin"
                / "veles-init"
            ),
            "python": str(
                self.rootfs_root
                / "opt"
                / "veles"
                / ".venv"
                / "bin"
                / "python"
            ),
            "ollama": str(
                self.rootfs_root
                / "usr"
                / "local"
                / "bin"
                / "ollama"
            ),
            "configuration": str(
                self.rootfs_root
                / "etc"
                / "veles"
                / "veles.env"
            ),
        }
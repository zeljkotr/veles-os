"""
VELES OS Root Filesystem Builder

Builds a self-contained Linux root filesystem for VELES OS.

The resulting filesystem contains:
- a minimal Debian/Ubuntu userspace
- Python runtime
- VELES OS source/runtime tree
- VELES Python dependencies
- a standalone VELES runtime entrypoint
- VELES runtime configuration

This module does not modify the installed host system.
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit


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
    )

    EXCLUDED_DIRECTORIES = {
        ".git",
        ".venv",
        "__pycache__",
        "build",
    }

    EXCLUDED_FILES = {
        ".DS_Store",
    }

    HOST_RUNTIME_CONFIGURATION = Path(
        "/etc/veles/veles.env"
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
            "opt",
            "opt/veles",
            "etc/veles",
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

        return destination_root

    # --------------------------------------------------
    # RUNTIME CONFIGURATION
    # --------------------------------------------------

    def _read_host_runtime_configuration(self):
        """
        Read VELES host runtime configuration.

        The canonical host configuration is:

            /etc/veles/veles.env

        The file contains shell-style exports such as:

            export VELES_DATABASE_URL=...
            export PGPASSWORD=...

        Only the required VELES database values are extracted.
        The file is never executed.
        """

        configuration_path = (
            self.HOST_RUNTIME_CONFIGURATION
        )

        if not configuration_path.is_file():
            return {}

        values = {}

        for raw_line in configuration_path.read_text(
            encoding="utf-8"
        ).splitlines():

            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            if line.startswith("export "):
                line = line[7:].strip()

            if "=" not in line:
                continue

            name, value = line.split(
                "=",
                1,
            )

            name = name.strip()
            value = value.strip()

            if name not in {
                "VELES_DATABASE_URL",
                "VELES_DATABASE_PASSWORD",
                "PGPASSWORD",
            }:
                continue

            try:
                parsed = shlex.split(
                    value,
                    comments=False,
                    posix=True,
                )

                if parsed:
                    value = parsed[0]
                else:
                    value = ""

            except ValueError as exc:
                raise RuntimeError(
                    f"Invalid value for {name} in "
                    f"{configuration_path}."
                ) from exc

            values[name] = value

        return values

    def _database_configuration(self):
        """
        Resolve VELES database configuration.

        Configuration precedence:

        1. VELES_DATABASE_URL environment variable
        2. /etc/veles/veles.env

        Password precedence:

        1. VELES_DATABASE_PASSWORD environment variable
        2. PGPASSWORD environment variable
        3. VELES_DATABASE_PASSWORD from /etc/veles/veles.env
        4. PGPASSWORD from /etc/veles/veles.env
        5. Password embedded in VELES_DATABASE_URL

        No database host, port, user, database name,
        or password is hardcoded.
        """

        host_configuration = (
            self._read_host_runtime_configuration()
        )

        database_url = os.environ.get(
            "VELES_DATABASE_URL"
        )

        if not database_url:
            database_url = host_configuration.get(
                "VELES_DATABASE_URL"
            )

        if not database_url:
            raise RuntimeError(
                "Required VELES database configuration is missing. "
                "VELES_DATABASE_URL was not found in the build "
                "environment or /etc/veles/veles.env."
            )

        database_password = os.environ.get(
            "VELES_DATABASE_PASSWORD"
        )

        if not database_password:
            database_password = os.environ.get(
                "PGPASSWORD"
            )

        if not database_password:
            database_password = host_configuration.get(
                "VELES_DATABASE_PASSWORD"
            )

        if not database_password:
            database_password = host_configuration.get(
                "PGPASSWORD"
            )

        if not database_password:
            try:
                parsed_url = urlsplit(
                    database_url
                )

                database_password = parsed_url.password

                if database_password:
                    database_password = unquote(
                        database_password
                    )

            except ValueError as exc:
                raise RuntimeError(
                    "VELES_DATABASE_URL is invalid."
                ) from exc

        if not database_password:
            raise RuntimeError(
                "VELES_DATABASE_PASSWORD is not configured "
                "and VELES_DATABASE_URL does not contain "
                "a database password."
            )

        return (
            database_url,
            database_password,
        )

    def create_runtime_configuration(self):
        """
        Create the VELES system runtime environment file.

        The host configuration in /etc/veles/veles.env is used
        as the canonical build configuration when explicit
        environment variables are not supplied.

        VELES_DATABASE_PASSWORD does not need to be exported
        separately when the password is present in the
        VELES_DATABASE_URL.
        """

        (
            database_url,
            database_password,
        ) = self._database_configuration()

        configuration = (
            "export VELES_DATABASE_URL="
            + shlex.quote(database_url)
            + "\n"
            + "export PGPASSWORD="
            + shlex.quote(database_password)
            + "\n"
        )

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

        return configuration_path

    # --------------------------------------------------
    # PYTHON ENVIRONMENT
    # --------------------------------------------------

    def _rootfs_python(self):
        """Return the Python interpreter inside the rootfs."""

        candidates = (
            self.rootfs_root
            / "usr"
            / "bin"
            / "python3",
            self.rootfs_root
            / "usr"
            / "bin"
            / "python3.14",
            self.rootfs_root
            / "usr"
            / "bin"
            / "python3.13",
            self.rootfs_root
            / "usr"
            / "bin"
            / "python3.12",
            self.rootfs_root
            / "usr"
            / "bin"
            / "python3.11",
        )

        for candidate in candidates:
            if candidate.exists():
                return candidate

        raise FileNotFoundError(
            "No Python 3 interpreter was installed "
            "inside the VELES rootfs."
        )

    def create_python_environment(self):
        """
        Create a standalone VELES Python environment.

        --copies is intentional.

        The final VELES OS must not depend on symlink chains
        created against the build host. Python and its launcher
        are copied into the target rootfs.
        """

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

if [ ! -f /etc/veles/veles.env ]; then
    echo "[INIT] ERROR: VELES runtime configuration not found."
    echo
    echo "[INIT] Expected:"
    echo "  /etc/veles/veles.env"
    echo
    exec /bin/sh
fi

echo "[INIT] Loading VELES runtime configuration..."

set -a
. /etc/veles/veles.env
set +a

if [ -z "${VELES_DATABASE_URL:-}" ]; then
    echo "[INIT] ERROR: VELES_DATABASE_URL is not configured."
    echo
    exec /bin/sh
fi

echo "[INIT] VELES runtime configuration loaded."
echo "[INIT] Starting VELES Python runtime..."

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
        """
        Validate that the runtime files are physically present.

        This deliberately checks the actual executable targets,
        not only the existence of symlinks.
        """

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

        required = (
            python,
            python3,
            init,
            environment,
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
                "VELES runtime configuration is not a regular file: "
                f"{environment}"
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
            "opt/veles/main.py",
            "opt/veles/boot/bootstrap.py",
            "opt/veles/kernel/runtime.py",
            "opt/veles/system",
            "opt/veles/core",
            "opt/veles/services",
            "opt/veles/desktop",
            "opt/veles/.venv/bin/python",
            "etc/veles/veles.env",
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
            "configuration": str(
                self.rootfs_root
                / "etc"
                / "veles"
                / "veles.env"
            ),
        }
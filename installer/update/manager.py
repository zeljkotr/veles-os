"""
VELES OS Update Manager

Provides a safe foundation for VELES OS updates.

The current implementation is non-destructive:
- detects VELES OS versions
- generates file manifests
- detects filesystem changes
- persists installed manifests
- tracks update transaction state
- prepares isolated update staging
- verifies staged updates

It does not modify an installed VELES OS.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from installer.update.manifest import ManifestStore
from installer.update.state import UpdateState


class UpdateManager:
    """Coordinates VELES OS update preparation and verification."""

    VERSION_RELATIVE_PATH = Path("etc/veles/version.json")

    DEFAULT_VERSION = "0.1.0"

    EXCLUDED_DIRECTORIES = {
        ".git",
        ".venv",
        "__pycache__",
    }

    EXCLUDED_FILES = {
        ".DS_Store",
    }

    def __init__(
        self,
        source_root=None,
        staging_root=None,
        manifest_path=None,
    ):
        self.source_root = (
            Path(source_root).expanduser().resolve()
            if source_root
            else Path.cwd().resolve()
        )

        self.staging_root = (
            Path(staging_root).expanduser().resolve()
            if staging_root
            else self.source_root / "build" / "update-staging"
        )

        self.manifest_path = (
            Path(manifest_path).expanduser().resolve()
            if manifest_path
            else (
                self.source_root
                / "build"
                / "update"
                / "installed-manifest.json"
            )
        )

        self.manifest_store = ManifestStore(
            self.manifest_path
        )

        self.update_state = UpdateState()

        self.ready = False
        self.state = "offline"

        self.manifest = {}
        self.staged = False

    # --------------------------------------------------
    # LIFECYCLE
    # --------------------------------------------------

    def start(self):
        """Start the Update Manager."""

        if self.ready:
            return self

        print(
            "[UPDATE] Initializing Update Manager..."
        )

        self.validate_source()
        self.ensure_version_file()

        self.ready = True
        self.state = "online"

        print(
            "[UPDATE] Update Manager: READY"
        )

        return self

    def stop(self):
        """Stop the Update Manager."""

        if not self.ready:
            return

        print(
            "[UPDATE] Stopping Update Manager..."
        )

        self.ready = False
        self.state = "offline"
        self.manifest = {}
        self.staged = False

        if self.update_state.state != UpdateState.IDLE:
            self.update_state.reset()

        print(
            "[UPDATE] Update Manager: OFFLINE"
        )

    # --------------------------------------------------
    # SOURCE
    # --------------------------------------------------

    def validate_source(self, root=None):
        """Validate a VELES OS source tree."""

        root = (
            Path(root).expanduser().resolve()
            if root
            else self.source_root
        )

        if not root.exists():
            raise FileNotFoundError(
                f"VELES source root does not exist: {root}"
            )

        if not root.is_dir():
            raise NotADirectoryError(
                f"VELES source root is not a directory: {root}"
            )

        required = (
            "boot",
            "system",
            "core",
            "services",
            "desktop",
            "kernel",
        )

        missing = [
            name
            for name in required
            if not (root / name).is_dir()
        ]

        if missing:
            raise RuntimeError(
                "Invalid VELES OS source tree. "
                f"Missing directories: {', '.join(missing)}"
            )

        return True

    # --------------------------------------------------
    # VERSION
    # --------------------------------------------------

    def version_path(self, root=None):
        """Return the VELES OS version metadata path."""

        root = (
            Path(root).expanduser().resolve()
            if root
            else self.source_root
        )

        return root / self.VERSION_RELATIVE_PATH

    def ensure_version_file(self, root=None):
        """Create version metadata if it does not exist."""

        path = self.version_path(root)

        if path.exists():
            return path

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "name": "VELES OS",
            "version": self.DEFAULT_VERSION,
        }

        path.write_text(
            json.dumps(
                data,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        return path

    def read_version(self, root=None):
        """Read the VELES OS version."""

        path = self.version_path(root)

        if not path.exists():
            raise FileNotFoundError(
                f"VELES version file not found: {path}"
            )

        try:
            data = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Invalid VELES version metadata: {path}"
            ) from exc

        version = data.get("version")

        if not version:
            raise RuntimeError(
                f"VELES version metadata has no version: {path}"
            )

        return version

    # --------------------------------------------------
    # MANIFEST
    # --------------------------------------------------

    def _excluded(self, path):
        """Return True when a path should be excluded."""

        if any(
            part in self.EXCLUDED_DIRECTORIES
            for part in path.parts
        ):
            return True

        if path.name in self.EXCLUDED_FILES:
            return True

        return False

    def _hash_file(self, path):
        """Calculate SHA-256 for a file."""

        digest = hashlib.sha256()

        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)

                if not chunk:
                    break

                digest.update(chunk)

        return digest.hexdigest()

    def generate_manifest(self, root=None):
        """Generate a filesystem manifest."""

        root = (
            Path(root).expanduser().resolve()
            if root
            else self.source_root
        )

        self.validate_source(root)

        manifest = {}

        for path in sorted(root.rglob("*")):

            if not path.is_file():
                continue

            relative = path.relative_to(root)

            if self._excluded(relative):
                continue

            manifest[str(relative)] = {
                "sha256": self._hash_file(path),
                "size": path.stat().st_size,
            }

        result = {
            "version": self.read_version(root),
            "files": manifest,
        }

        self.manifest = result

        return result

    def save_manifest(self, path, manifest=None):
        """Save a manifest to disk."""

        manifest = (
            manifest
            if manifest is not None
            else self.manifest
        )

        if not manifest:
            manifest = self.generate_manifest()

        path = Path(path).expanduser().resolve()

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            json.dumps(
                manifest,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        return path

    # --------------------------------------------------
    # PERSISTENT INSTALLED MANIFEST
    # --------------------------------------------------

    def set_installed_manifest(
        self,
        manifest=None,
    ):
        """Persist a manifest as installed VELES OS state."""

        manifest = (
            manifest
            if manifest is not None
            else self.manifest
        )

        if not manifest:
            manifest = self.generate_manifest()

        return self.manifest_store.save(
            manifest
        )

    def load_installed_manifest(self):
        """Load the persistent installed manifest."""

        return self.manifest_store.load()

    def has_installed_manifest(self):
        """Return True when an installed manifest exists."""

        return self.manifest_store.exists()

    def detect_changes(
        self,
        source_manifest=None,
    ):
        """Compare installed state with source state."""

        if not self.has_installed_manifest():
            raise RuntimeError(
                "No persistent installed manifest exists."
            )

        source_manifest = (
            source_manifest
            if source_manifest is not None
            else self.generate_manifest()
        )

        return self.manifest_store.compare_with(
            source_manifest
        )

    # --------------------------------------------------
    # CHANGE DETECTION
    # --------------------------------------------------

    def compare_manifests(
        self,
        current,
        target,
    ):
        """Compare two filesystem manifests."""

        current_files = current.get(
            "files",
            {},
        )

        target_files = target.get(
            "files",
            {},
        )

        current_paths = set(current_files)
        target_paths = set(target_files)

        added = sorted(
            target_paths - current_paths
        )

        removed = sorted(
            current_paths - target_paths
        )

        modified = sorted(
            path
            for path in current_paths & target_paths
            if current_files[path] != target_files[path]
        )

        return {
            "added": added,
            "modified": modified,
            "removed": removed,
        }

    # --------------------------------------------------
    # UPDATE STATE
    # --------------------------------------------------

    def update_state_value(self):
        """Return the current update transaction state."""

        return self.update_state.state

    def begin_check(self):
        """Begin update checking."""

        if self.update_state.state == UpdateState.IDLE:
            self.update_state.transition(
                UpdateState.CHECKING
            )

        return self.update_state.state

    def begin_staging(self):
        """Begin update staging."""

        self.update_state.transition(
            UpdateState.STAGING
        )

        return self.update_state.state

    def begin_verification(self):
        """Begin update verification."""

        self.update_state.transition(
            UpdateState.VERIFYING
        )

        return self.update_state.state

    def mark_ready(self):
        """Mark the prepared update as ready."""

        self.update_state.transition(
            UpdateState.READY
        )

        return self.update_state.state

    def mark_failed(self):
        """Mark the current update transaction as failed."""

        return self.update_state.fail()

    # --------------------------------------------------
    # STAGING
    # --------------------------------------------------

    def prepare(self):
        """Prepare a non-destructive update staging tree."""

        self.validate_source()

        self.begin_staging()

        try:
            if self.staging_root.exists():
                shutil.rmtree(
                    self.staging_root
                )

            self.staging_root.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.copytree(
                self.source_root,
                self.staging_root,
                ignore=shutil.ignore_patterns(
                    ".git",
                    ".venv",
                    "__pycache__",
                    "build",
                ),
            )

            self.staged = True

            print(
                f"[UPDATE] Staging prepared: "
                f"{self.staging_root}"
            )

            return self.staging_root

        except Exception:
            self.mark_failed()
            raise

    # --------------------------------------------------
    # VERIFICATION
    # --------------------------------------------------

    def verify(self):
        """Verify the prepared staging tree."""

        if not self.staged:
            raise RuntimeError(
                "No update staging tree is prepared."
            )

        self.begin_verification()

        try:
            self.validate_source(
                self.staging_root
            )

            version = self.read_version(
                self.staging_root
            )

            manifest = self.generate_manifest(
                self.staging_root
            )

            result = {
                "valid": True,
                "version": version,
                "files": len(
                    manifest["files"]
                ),
            }

            self.mark_ready()

            return result

        except Exception:
            self.mark_failed()
            raise

    # --------------------------------------------------
    # UPDATE CHECK
    # --------------------------------------------------

    def check(
        self,
        installed_root=None,
    ):
        """Check whether an update is available."""

        self.begin_check()

        try:
            current_root = (
                Path(installed_root)
                .expanduser()
                .resolve()
                if installed_root
                else None
            )

            available_version = self.read_version(
                self.source_root
            )

            if current_root is None:
                result = {
                    "available": True,
                    "current_version": None,
                    "available_version": available_version,
                    "reason": "no_installed_root",
                }

                self.mark_ready()

                return result

            current_version = self.read_version(
                current_root
            )

            if current_version == available_version:
                result = {
                    "available": False,
                    "current_version": current_version,
                    "available_version": available_version,
                    "reason": "up_to_date",
                }

                self.mark_ready()

                return result

            result = {
                "available": True,
                "current_version": current_version,
                "available_version": available_version,
                "reason": "version_changed",
            }

            self.mark_ready()

            return result

        except Exception:
            self.mark_failed()
            raise

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    def status(self):
        """Return Update Manager status."""

        return {
            "state": self.state,
            "ready": self.ready,
            "update_state": self.update_state.state,
            "source": str(
                self.source_root
            ),
            "staging": str(
                self.staging_root
            ),
            "manifest": str(
                self.manifest_path
            ),
            "installed_manifest": (
                self.has_installed_manifest()
            ),
            "version": (
                self.read_version()
                if self.source_root.exists()
                else None
            ),
            "staged": self.staged,
            "manifest_files": len(
                self.manifest.get(
                    "files",
                    {},
                )
            ),
        }
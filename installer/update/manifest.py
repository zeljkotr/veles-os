"""
VELES OS Persistent Update Manifest

Provides persistent storage and comparison for VELES OS
filesystem manifests.

This module is intentionally independent from the Update Manager
runtime so it can be isolated and tested before integration.
"""

from __future__ import annotations

import json
from pathlib import Path


class ManifestStore:
    """Persist and compare VELES OS filesystem manifests."""

    def __init__(self, path):
        self.path = (
            Path(path)
            .expanduser()
            .resolve()
        )

    # --------------------------------------------------
    # STORAGE
    # --------------------------------------------------

    def exists(self):
        """Return True when the persistent manifest exists."""

        return self.path.is_file()

    def save(self, manifest):
        """Persist a filesystem manifest."""

        if not isinstance(manifest, dict):
            raise TypeError(
                "Manifest must be a dictionary."
            )

        if "version" not in manifest:
            raise ValueError(
                "Manifest is missing version."
            )

        if "files" not in manifest:
            raise ValueError(
                "Manifest is missing files."
            )

        if not isinstance(
            manifest["files"],
            dict,
        ):
            raise ValueError(
                "Manifest files must be a dictionary."
            )

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.path.write_text(
            json.dumps(
                manifest,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        return self.path

    def load(self):
        """Load the persistent manifest."""

        if not self.path.exists():
            raise FileNotFoundError(
                f"Persistent manifest not found: {self.path}"
            )

        try:
            manifest = json.loads(
                self.path.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Invalid persistent manifest: {self.path}"
            ) from exc

        self._validate(manifest)

        return manifest

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    @staticmethod
    def _validate(manifest):
        """Validate the basic manifest structure."""

        if not isinstance(manifest, dict):
            raise ValueError(
                "Manifest must be a dictionary."
            )

        if not manifest.get("version"):
            raise ValueError(
                "Manifest has no version."
            )

        files = manifest.get("files")

        if not isinstance(files, dict):
            raise ValueError(
                "Manifest files must be a dictionary."
            )

        for relative_path, metadata in files.items():

            if not isinstance(
                relative_path,
                str,
            ):
                raise ValueError(
                    "Manifest file paths must be strings."
                )

            if not isinstance(
                metadata,
                dict,
            ):
                raise ValueError(
                    f"Invalid metadata for: {relative_path}"
                )

            if "sha256" not in metadata:
                raise ValueError(
                    f"Missing SHA-256 for: {relative_path}"
                )

            if "size" not in metadata:
                raise ValueError(
                    f"Missing size for: {relative_path}"
                )

        return True

    # --------------------------------------------------
    # COMPARISON
    # --------------------------------------------------

    @staticmethod
    def compare(
        installed,
        source,
    ):
        """
        Compare an installed manifest against a source manifest.

        Returns:
            added:
                Files present in source but not installed.

            modified:
                Files present in both but with different metadata.

            removed:
                Files present in installed but not source.

            unchanged:
                Files identical in both manifests.
        """

        ManifestStore._validate(installed)
        ManifestStore._validate(source)

        installed_files = installed["files"]
        source_files = source["files"]

        installed_paths = set(
            installed_files
        )

        source_paths = set(
            source_files
        )

        added = sorted(
            source_paths - installed_paths
        )

        removed = sorted(
            installed_paths - source_paths
        )

        common = (
            installed_paths
            & source_paths
        )

        modified = sorted(
            path
            for path in common
            if installed_files[path]
            != source_files[path]
        )

        unchanged = sorted(
            path
            for path in common
            if installed_files[path]
            == source_files[path]
        )

        return {
            "installed_version": installed["version"],
            "source_version": source["version"],
            "added": added,
            "modified": modified,
            "removed": removed,
            "unchanged": unchanged,
            "changed": bool(
                added
                or modified
                or removed
            ),
        }

    def compare_with(
        self,
        source_manifest,
    ):
        """Compare the stored installed manifest with a source manifest."""

        installed_manifest = self.load()

        return self.compare(
            installed_manifest,
            source_manifest,
        )
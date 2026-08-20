"""
VELES OS Filesystem Service

Provides safe, read-only filesystem access.

Responsibilities:
- Path inspection
- File and directory discovery
- Directory listing
- File metadata
- Filesystem statistics
- Safe path resolution

No destructive filesystem operations are performed.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any


class FilesystemService:
    """
    Read-only local filesystem information provider.
    """

    def __init__(self):
        self.root = Path("/")

    def exists(self, path: str | Path) -> bool:
        """
        Return whether a filesystem path exists.
        """

        try:
            return Path(path).exists()

        except (OSError, ValueError):
            return False

    def is_file(self, path: str | Path) -> bool:
        """
        Return whether a path is a regular file.
        """

        try:
            return Path(path).is_file()

        except (OSError, ValueError):
            return False

    def is_directory(self, path: str | Path) -> bool:
        """
        Return whether a path is a directory.
        """

        try:
            return Path(path).is_dir()

        except (OSError, ValueError):
            return False

    def resolve(self, path: str | Path) -> str | None:
        """
        Resolve a filesystem path safely.
        """

        try:
            return str(Path(path).expanduser().resolve())

        except (OSError, RuntimeError, ValueError):
            return None

    def get_info(
        self,
        path: str | Path,
    ) -> dict[str, Any] | None:
        """
        Return metadata for a filesystem path.
        """

        try:
            target = Path(path).expanduser()

            info = target.stat()

        except (
            OSError,
            ValueError,
        ):
            return None

        mode = info.st_mode

        if stat.S_ISREG(mode):
            path_type = "file"
        elif stat.S_ISDIR(mode):
            path_type = "directory"
        elif stat.S_ISLNK(mode):
            path_type = "symlink"
        elif stat.S_ISSOCK(mode):
            path_type = "socket"
        elif stat.S_ISCHR(mode):
            path_type = "character_device"
        elif stat.S_ISBLK(mode):
            path_type = "block_device"
        elif stat.S_ISFIFO(mode):
            path_type = "fifo"
        else:
            path_type = "other"

        return {
            "path": str(target),
            "resolved_path": self.resolve(target),
            "name": target.name,
            "type": path_type,
            "size_bytes": info.st_size,
            "mode": stat.filemode(mode),
            "uid": info.st_uid,
            "gid": info.st_gid,
            "inode": info.st_ino,
            "device": info.st_dev,
            "links": info.st_nlink,
            "created_at": info.st_ctime,
            "modified_at": info.st_mtime,
            "accessed_at": info.st_atime,
        }

    def list_directory(
        self,
        path: str | Path,
    ) -> list[dict[str, Any]]:
        """
        Return entries inside a directory.
        """

        try:
            directory = Path(path).expanduser()

            if not directory.is_dir():
                return []

            entries: list[dict[str, Any]] = []

            for entry in sorted(
                directory.iterdir(),
                key=lambda item: item.name.lower(),
            ):
                try:
                    info = self.get_info(entry)

                    if info is None:
                        continue

                    entries.append(info)

                except (
                    OSError,
                    ValueError,
                ):
                    continue

            return entries

        except (
            OSError,
            ValueError,
        ):
            return []

    def get_filesystem_stats(
        self,
        path: str | Path = "/",
    ) -> dict[str, Any] | None:
        """
        Return filesystem capacity statistics.
        """

        try:
            target = Path(path).expanduser()

            stats = os.statvfs(target)

            block_size = stats.f_frsize or stats.f_bsize

            total_bytes = (
                stats.f_blocks * block_size
            )

            free_bytes = (
                stats.f_bfree * block_size
            )

            available_bytes = (
                stats.f_bavail * block_size
            )

            used_bytes = (
                total_bytes - free_bytes
            )

            usage_percent = (
                (used_bytes / total_bytes) * 100
                if total_bytes
                else 0.0
            )

            return {
                "path": str(target),
                "total_bytes": total_bytes,
                "used_bytes": used_bytes,
                "free_bytes": free_bytes,
                "available_bytes": available_bytes,
                "usage_percent": usage_percent,
                "block_size": block_size,
                "total_blocks": stats.f_blocks,
                "free_blocks": stats.f_bfree,
                "available_blocks": stats.f_bavail,
            }

        except (
            OSError,
            ValueError,
        ):
            return None

    def get_root_info(self) -> dict[str, Any] | None:
        """
        Return information about the VELES OS root filesystem.
        """

        return self.get_filesystem_stats(self.root)


filesystem = FilesystemService()

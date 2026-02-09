"""
Enhanced File Operations
=========================
Extends beyond ~/.kai/data/ with configurable allowed paths.
Supports read, write, rename, move, delete, and directory listing.
"""

import shutil
from pathlib import Path

from kai.utils.logger import setup_logger

logger = setup_logger(__name__)


class EnhancedFileOps:
    """File operations with configurable path restrictions."""

    def __init__(self, allowed_paths: list[str | Path] | None = None):
        if allowed_paths:
            self._allowed = [Path(p).expanduser().resolve() for p in allowed_paths]
        else:
            self._allowed = [Path.home().resolve()]

    def _safe_path(self, path_str: str) -> Path:
        """Resolve path and verify it's within allowed directories."""
        resolved = Path(path_str).expanduser().resolve()
        for root in self._allowed:
            if str(resolved).startswith(str(root)):
                return resolved
        raise ValueError(
            f"Path '{path_str}' not within allowed directories: "
            f"{[str(p) for p in self._allowed]}"
        )

    def read_text(self, path: str) -> str:
        """Read a text file."""
        file_path = self._safe_path(path)
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        return file_path.read_text(encoding="utf-8")

    def read_bytes(self, path: str) -> bytes:
        """Read a binary file."""
        file_path = self._safe_path(path)
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        return file_path.read_bytes()

    def write_text(self, path: str, content: str) -> Path:
        """Write text to a file, creating parent dirs as needed."""
        file_path = self._safe_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        logger.debug(f"Written: {file_path}")
        return file_path

    def write_bytes(self, path: str, data: bytes) -> Path:
        """Write binary data to a file."""
        file_path = self._safe_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        logger.debug(f"Written (binary): {file_path}")
        return file_path

    def rename(self, old_path: str, new_path: str) -> Path:
        """Rename or move a file/directory."""
        old = self._safe_path(old_path)
        new = self._safe_path(new_path)

        if not old.exists():
            raise FileNotFoundError(f"Source not found: {old_path}")
        if new.exists():
            raise FileExistsError(f"Destination already exists: {new_path}")

        new.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old), str(new))
        logger.debug(f"Moved: {old} -> {new}")
        return new

    def delete(self, path: str) -> bool:
        """Delete a file. Returns True if deleted, False if not found."""
        file_path = self._safe_path(path)
        if file_path.is_file():
            file_path.unlink()
            logger.debug(f"Deleted: {file_path}")
            return True
        return False

    def list_dir(self, path: str = "~", pattern: str = "*") -> list[dict]:
        """List directory contents with metadata."""
        dir_path = self._safe_path(path)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")

        entries = []
        for item in sorted(dir_path.glob(pattern)):
            try:
                stat = item.stat()
                entries.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": stat.st_size if item.is_file() else None,
                    "modified": stat.st_mtime,
                })
            except PermissionError:
                continue
        return entries

    def exists(self, path: str) -> bool:
        """Check if a path exists."""
        return self._safe_path(path).exists()

    def mkdir(self, path: str) -> Path:
        """Create a directory (and parents)."""
        dir_path = self._safe_path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

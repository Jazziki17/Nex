"""
File Manager - Nex's Memory on Disk
======================================

LEARNING POINT: File System Operations
-----------------------------------------
Nex needs to read and write files for:
  - Storing user preferences
  - Saving notes (when user says "take a note")
  - Logging conversations
  - Persisting state between restarts

LEARNING POINT: pathlib.Path
-------------------------------
Python's `pathlib` module is the modern way to handle file paths.
Old way:  os.path.join(base, "data", "notes.json")
New way:  base / "data" / "notes.json"

pathlib is:
  - More readable (uses / operator)
  - Cross-platform (handles Windows \\ vs Unix / automatically)
  - Object-oriented (methods like .exists(), .read_text(), .mkdir())

LEARNING POINT: Security — Path Traversal Prevention
-------------------------------------------------------
NEVER trust user input for file paths. A malicious input like
"../../etc/passwd" could read sensitive system files. We ALWAYS
validate that the resolved path is within our allowed directory.

This is called "path traversal" or "directory traversal" and is
a top-10 web security vulnerability (OWASP).
"""

import json
from datetime import datetime
from pathlib import Path

from nex.core.engine import Module
from nex.core.event_bus import EventBus
from nex.utils.logger import setup_logger


logger = setup_logger(__name__)


class FileManager(Module):
    """
    Secure local file read/write manager.

    LEARNING POINT: Principle of Least Privilege
    -----------------------------------------------
    The FileManager only operates within a specific directory
    (the Nex data directory). It cannot read or write anywhere
    else on the system. This limits the damage if something
    goes wrong.
    """

    def __init__(self, event_bus: EventBus, base_dir: str | Path | None = None):
        super().__init__("FileManager", event_bus)

        # Default to ~/.nex/data for persistent storage
        self.base_dir = Path(base_dir) if base_dir else Path.home() / ".nex" / "data"

        # Subdirectories for organized storage
        self.notes_dir = self.base_dir / "notes"
        self.config_dir = self.base_dir / "config"
        self.logs_dir = self.base_dir / "logs"
        self.memory_dir = self.base_dir / "memory"

    async def start(self) -> None:
        """Initialize the file system structure."""
        self._running = True

        # Create all required directories
        for directory in [self.notes_dir, self.config_dir, self.logs_dir, self.memory_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Subscribe to file-related events
        self.event_bus.subscribe("intent.classified", self._on_intent)
        self.event_bus.subscribe("file.write_request", self._on_write_request)
        self.event_bus.subscribe("file.read_request", self._on_read_request)

        logger.info(f"File manager ready. Data directory: {self.base_dir}")

    async def stop(self) -> None:
        self._running = False

    # ─── Public API ──────────────────────────────────────────────

    def write_text(self, relative_path: str, content: str) -> Path:
        """
        Write text content to a file within the data directory.

        LEARNING POINT: Defensive Programming
        ----------------------------------------
        We validate the path BEFORE writing. The _safe_path() method
        ensures we can never write outside our base directory.
        Even if someone passes "../../../etc/evil", it gets caught.

        Args:
            relative_path: Path relative to base_dir (e.g., "notes/todo.txt")
            content: Text content to write

        Returns:
            The absolute path of the written file

        Raises:
            ValueError: If the path tries to escape the base directory
        """
        file_path = self._safe_path(relative_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        logger.debug(f"Written: {file_path}")
        return file_path

    def read_text(self, relative_path: str) -> str | None:
        """
        Read text content from a file within the data directory.

        Returns:
            File content as string, or None if file doesn't exist
        """
        file_path = self._safe_path(relative_path)
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None
        return file_path.read_text(encoding="utf-8")

    def write_json(self, relative_path: str, data: dict) -> Path:
        """
        Write a dictionary as a JSON file.

        LEARNING POINT: JSON Serialization
        -------------------------------------
        JSON (JavaScript Object Notation) is the standard format for
        structured data. Python dicts map directly to JSON objects.

        `json.dumps()` converts a Python dict to a JSON string.
        `indent=2` makes it human-readable (pretty-printed).
        `ensure_ascii=False` allows non-English characters.
        """
        content = json.dumps(data, indent=2, ensure_ascii=False)
        return self.write_text(relative_path, content)

    def read_json(self, relative_path: str) -> dict | None:
        """Read a JSON file and return it as a dictionary."""
        content = self.read_text(relative_path)
        if content is None:
            return None
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {relative_path}: {e}")
            return None

    def list_files(self, relative_dir: str = "", pattern: str = "*") -> list[Path]:
        """
        List files in a directory.

        LEARNING POINT: Glob Patterns
        --------------------------------
        `Path.glob(pattern)` finds files matching a pattern:
          - "*"       — all files in the directory
          - "*.txt"   — all .txt files
          - "**/*.md" — all .md files in all subdirectories

        The ** means "any depth of subdirectories" (recursive).
        """
        dir_path = self._safe_path(relative_dir) if relative_dir else self.base_dir
        if not dir_path.is_dir():
            return []
        return sorted(dir_path.glob(pattern))

    def delete(self, relative_path: str) -> bool:
        """Delete a file within the data directory."""
        file_path = self._safe_path(relative_path)
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            logger.debug(f"Deleted: {file_path}")
            return True
        return False

    # ─── Private Methods ─────────────────────────────────────────

    def _safe_path(self, relative_path: str) -> Path:
        """
        Resolve a relative path and ensure it's within our base directory.

        LEARNING POINT: Path Traversal Prevention
        --------------------------------------------
        This is a CRITICAL security method. Here's how it works:

        1. Resolve the full absolute path (resolves .., symlinks, etc.)
        2. Check that the resolved path STARTS WITH our base directory
        3. If it doesn't, someone is trying to escape — raise an error

        Example:
            base_dir = /home/user/.nex/data
            "notes/todo.txt"       → /home/user/.nex/data/notes/todo.txt  ✓
            "../../etc/passwd"     → /home/user/.nex/etc/passwd            ✗ BLOCKED
        """
        # Resolve to absolute path
        resolved = (self.base_dir / relative_path).resolve()

        # Security check: must be within base_dir
        base_resolved = self.base_dir.resolve()
        if not str(resolved).startswith(str(base_resolved)):
            raise ValueError(
                f"Path traversal blocked: '{relative_path}' resolves outside "
                f"the data directory ({base_resolved})"
            )

        return resolved

    async def _on_intent(self, data: dict) -> None:
        """Handle intents that involve file operations."""
        intent = data.get("intent")

        if intent == "take_note":
            content = data.get("entities", {}).get("content", "")
            if content:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.write_text(
                    f"notes/note_{timestamp}.txt",
                    f"Note taken at {datetime.now().isoformat()}\n\n{content}\n",
                )
                await self.event_bus.publish("speech.respond", {
                    "text": "Note saved.",
                })
            else:
                await self.event_bus.publish("speech.respond", {
                    "text": "What would you like me to note down?",
                })

    async def _on_write_request(self, data: dict) -> None:
        """Handle explicit file write requests from other modules."""
        path = data.get("path", "")
        content = data.get("content", "")
        if path and content:
            self.write_text(path, content)

    async def _on_read_request(self, data: dict) -> None:
        """Handle file read requests and publish the content."""
        path = data.get("path", "")
        if path:
            content = self.read_text(path)
            await self.event_bus.publish("file.read_response", {
                "path": path,
                "content": content,
                "found": content is not None,
            })

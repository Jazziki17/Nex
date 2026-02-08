"""
Tests for File Manager
========================

LEARNING POINT: Testing with Temporary Directories
-----------------------------------------------------
When testing file I/O, NEVER use real directories. Use `tmp_path`
(a pytest fixture) which creates a unique temporary directory for
each test. It's automatically cleaned up after the test finishes.

This ensures:
  - Tests don't interfere with each other
  - Tests don't pollute your real filesystem
  - Tests work on any machine (no hardcoded paths)
"""

import pytest

from kai.core.event_bus import EventBus
from kai.io.file_manager import FileManager


@pytest.fixture
def file_manager(tmp_path):
    """
    Create a FileManager that uses a temporary directory.

    LEARNING POINT: tmp_path Fixture
    -----------------------------------
    `tmp_path` is a built-in pytest fixture that provides a unique
    temporary directory (as a pathlib.Path) for each test.
    Example: /tmp/pytest-of-user/pytest-123/test_write_text0/
    """
    bus = EventBus()
    return FileManager(event_bus=bus, base_dir=tmp_path)


@pytest.mark.asyncio
async def test_start_creates_directories(file_manager):
    """Test that start() creates the required directory structure."""
    await file_manager.start()

    assert file_manager.notes_dir.exists()
    assert file_manager.config_dir.exists()
    assert file_manager.logs_dir.exists()
    assert file_manager.memory_dir.exists()


def test_write_and_read_text(file_manager):
    """Test basic write and read operations."""
    file_manager.base_dir.mkdir(parents=True, exist_ok=True)

    file_manager.write_text("test.txt", "Hello, Kai!")
    content = file_manager.read_text("test.txt")

    assert content == "Hello, Kai!"


def test_write_and_read_json(file_manager):
    """Test JSON write and read operations."""
    file_manager.base_dir.mkdir(parents=True, exist_ok=True)

    data = {"name": "Kai", "version": "0.1.0", "features": ["voice", "vision"]}
    file_manager.write_json("config.json", data)
    result = file_manager.read_json("config.json")

    assert result == data


def test_read_nonexistent_file(file_manager):
    """Test that reading a missing file returns None."""
    result = file_manager.read_text("does_not_exist.txt")
    assert result is None


def test_write_creates_subdirectories(file_manager):
    """Test that write creates parent directories automatically."""
    file_manager.base_dir.mkdir(parents=True, exist_ok=True)

    file_manager.write_text("deep/nested/dir/file.txt", "content")
    content = file_manager.read_text("deep/nested/dir/file.txt")

    assert content == "content"


def test_path_traversal_blocked(file_manager):
    """
    Test that path traversal attempts are blocked.

    LEARNING POINT: Security Testing
    -----------------------------------
    You MUST test security measures. If this test passes, it means
    an attacker cannot read files outside the data directory by
    using "../" in the path.
    """
    file_manager.base_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError, match="Path traversal blocked"):
        file_manager.read_text("../../etc/passwd")


def test_delete_file(file_manager):
    """Test file deletion."""
    file_manager.base_dir.mkdir(parents=True, exist_ok=True)

    file_manager.write_text("to_delete.txt", "temporary")
    assert file_manager.read_text("to_delete.txt") is not None

    result = file_manager.delete("to_delete.txt")
    assert result is True
    assert file_manager.read_text("to_delete.txt") is None


def test_delete_nonexistent_file(file_manager):
    """Test that deleting a missing file returns False."""
    result = file_manager.delete("ghost.txt")
    assert result is False


def test_list_files(file_manager):
    """Test listing files in a directory."""
    file_manager.base_dir.mkdir(parents=True, exist_ok=True)

    file_manager.write_text("notes/a.txt", "note a")
    file_manager.write_text("notes/b.txt", "note b")
    file_manager.write_text("notes/c.md", "note c")

    all_files = file_manager.list_files("notes")
    assert len(all_files) == 3

    txt_files = file_manager.list_files("notes", "*.txt")
    assert len(txt_files) == 2

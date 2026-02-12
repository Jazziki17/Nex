"""
Tests for Enhanced File Operations
=====================================
Tests the EnhancedFileOps class with configurable allowed paths.
"""

import pytest

from nex.io.enhanced_file_ops import EnhancedFileOps


@pytest.fixture
def file_ops(tmp_path):
    """Create an EnhancedFileOps restricted to a temp directory."""
    return EnhancedFileOps(allowed_paths=[str(tmp_path)])


def test_write_and_read_text(file_ops, tmp_path):
    """Test basic text write/read cycle."""
    path = str(tmp_path / "hello.txt")
    file_ops.write_text(path, "Hello, world!")
    content = file_ops.read_text(path)
    assert content == "Hello, world!"


def test_write_creates_directories(file_ops, tmp_path):
    """Test that write creates parent directories automatically."""
    path = str(tmp_path / "deep" / "nested" / "file.txt")
    file_ops.write_text(path, "nested content")
    content = file_ops.read_text(path)
    assert content == "nested content"


def test_read_nonexistent_raises(file_ops, tmp_path):
    """Test reading a nonexistent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        file_ops.read_text(str(tmp_path / "ghost.txt"))


def test_path_traversal_blocked(file_ops, tmp_path):
    """Test that path traversal outside allowed roots is blocked."""
    with pytest.raises(ValueError, match="not within allowed directories"):
        file_ops.read_text("/etc/passwd")


def test_rename(file_ops, tmp_path):
    """Test renaming a file."""
    old = str(tmp_path / "old.txt")
    new = str(tmp_path / "new.txt")
    file_ops.write_text(old, "rename me")
    file_ops.rename(old, new)

    assert file_ops.read_text(new) == "rename me"
    assert not file_ops.exists(old)


def test_rename_nonexistent_raises(file_ops, tmp_path):
    """Test renaming a nonexistent source raises."""
    with pytest.raises(FileNotFoundError):
        file_ops.rename(str(tmp_path / "ghost.txt"), str(tmp_path / "new.txt"))


def test_rename_destination_exists_raises(file_ops, tmp_path):
    """Test renaming to an existing destination raises."""
    a = str(tmp_path / "a.txt")
    b = str(tmp_path / "b.txt")
    file_ops.write_text(a, "aaa")
    file_ops.write_text(b, "bbb")

    with pytest.raises(FileExistsError):
        file_ops.rename(a, b)


def test_delete(file_ops, tmp_path):
    """Test deleting a file."""
    path = str(tmp_path / "delete_me.txt")
    file_ops.write_text(path, "temp")
    assert file_ops.delete(path) is True
    assert file_ops.exists(path) is False


def test_delete_nonexistent(file_ops, tmp_path):
    """Test deleting a nonexistent file returns False."""
    assert file_ops.delete(str(tmp_path / "nope.txt")) is False


def test_list_dir(file_ops, tmp_path):
    """Test listing directory contents."""
    file_ops.write_text(str(tmp_path / "a.txt"), "a")
    file_ops.write_text(str(tmp_path / "b.txt"), "b")
    file_ops.write_text(str(tmp_path / "c.md"), "c")

    entries = file_ops.list_dir(str(tmp_path))
    assert len(entries) == 3

    txt_entries = file_ops.list_dir(str(tmp_path), "*.txt")
    assert len(txt_entries) == 2


def test_list_dir_not_a_directory(file_ops, tmp_path):
    """Test listing a non-directory path raises."""
    path = str(tmp_path / "file.txt")
    file_ops.write_text(path, "not a dir")

    with pytest.raises(NotADirectoryError):
        file_ops.list_dir(path)


def test_exists(file_ops, tmp_path):
    """Test exists check."""
    path = str(tmp_path / "exists.txt")
    assert file_ops.exists(path) is False
    file_ops.write_text(path, "here")
    assert file_ops.exists(path) is True


def test_mkdir(file_ops, tmp_path):
    """Test creating directories."""
    dir_path = str(tmp_path / "new_dir" / "sub_dir")
    result = file_ops.mkdir(dir_path)
    assert result.is_dir()


def test_write_and_read_bytes(file_ops, tmp_path):
    """Test binary write/read."""
    path = str(tmp_path / "binary.bin")
    data = b'\x00\x01\x02\xff'
    file_ops.write_bytes(path, data)
    result = file_ops.read_bytes(path)
    assert result == data

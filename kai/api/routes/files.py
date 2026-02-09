"""File operations routes — full CRUD + rename/move/list."""

import os
import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from kai.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(tags=["files"])

# Configurable allowed paths — defaults to home directory subtree
ALLOWED_ROOTS: list[Path] = [
    Path.home(),
]


def _safe_path(path_str: str) -> Path:
    """Resolve a path and verify it's within allowed roots."""
    resolved = Path(path_str).expanduser().resolve()

    for root in ALLOWED_ROOTS:
        root_resolved = root.resolve()
        if str(resolved).startswith(str(root_resolved)):
            return resolved

    raise ValueError(f"Path not within allowed directories: {path_str}")


class ListRequest(BaseModel):
    path: str = "~"
    pattern: str = "*"


class ReadRequest(BaseModel):
    path: str


class WriteRequest(BaseModel):
    path: str
    content: str


class RenameRequest(BaseModel):
    old_path: str
    new_path: str


class DeleteRequest(BaseModel):
    path: str


@router.post("/list")
async def list_files(req: ListRequest):
    """List directory contents."""
    try:
        dir_path = _safe_path(req.path)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    if not dir_path.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")

    entries = []
    try:
        for item in sorted(dir_path.glob(req.pattern)):
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
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    return {"path": str(dir_path), "entries": entries}


@router.post("/read")
async def read_file(req: ReadRequest):
    """Read a text file."""
    try:
        file_path = _safe_path(req.path)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not valid UTF-8 text")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    return {"path": str(file_path), "content": content, "size": len(content)}


@router.post("/write")
async def write_file(req: WriteRequest):
    """Write a text file (creates parent directories if needed)."""
    try:
        file_path = _safe_path(req.path)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(req.content, encoding="utf-8")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    logger.info(f"Written: {file_path}")
    return {"path": str(file_path), "size": len(req.content), "status": "ok"}


@router.post("/rename")
async def rename_file(req: RenameRequest):
    """Rename or move a file/directory."""
    try:
        old = _safe_path(req.old_path)
        new = _safe_path(req.new_path)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    if not old.exists():
        raise HTTPException(status_code=404, detail="Source not found")

    if new.exists():
        raise HTTPException(status_code=409, detail="Destination already exists")

    try:
        new.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old), str(new))
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    logger.info(f"Moved: {old} -> {new}")
    return {"old_path": str(old), "new_path": str(new), "status": "ok"}


@router.post("/delete")
async def delete_file(req: DeleteRequest):
    """Delete a file or empty directory."""
    try:
        target = _safe_path(req.path)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    if not target.exists():
        raise HTTPException(status_code=404, detail="Not found")

    try:
        if target.is_file():
            target.unlink()
        elif target.is_dir():
            os.rmdir(target)  # Only deletes empty dirs for safety
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
    except OSError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    logger.info(f"Deleted: {target}")
    return {"path": str(target), "status": "deleted"}

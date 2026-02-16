"""Command execution route — sandboxed with an allowlist and injection protection."""

import asyncio
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from nex.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(tags=["commands"])

# Only these commands can be executed — add more as needed
ALLOWED_COMMANDS = {
    "ls", "pwd", "whoami", "date", "uptime", "df",
    "cat", "head", "tail", "wc",
    "echo", "which", "env",
    "python", "python3", "pip", "pip3",
    "git",
    "open",  # macOS
}

# Patterns that bypass the allowlist (code execution, shell injection)
BLOCKED_PATTERNS = [
    r"python3?\s+-[cm]",       # python -c "..." or python -m
    r"\|",                      # pipe chains
    r";",                       # command chaining
    r"&&",                      # conditional chaining
    r"\|\|",                    # OR chaining
    r"`",                       # backtick subshell
    r"\$\(",                    # $() subshell
    r">\s*\(",                  # process substitution
    r"<\(",                     # process substitution
    r"\beval\b",                # eval
    r"\bexec\b",                # exec
    r"\bsource\b",             # source
]

_BLOCKED_RE = re.compile("|".join(BLOCKED_PATTERNS))


def _is_allowed(cmd: str) -> bool:
    """Check if the base command is in the allowlist."""
    parts = cmd.strip().split()
    if not parts:
        return False
    base = parts[0].split("/")[-1]  # Handle full paths like /usr/bin/ls
    return base in ALLOWED_COMMANDS


def _has_injection(cmd: str) -> bool:
    """Check for shell injection / bypass patterns."""
    return bool(_BLOCKED_RE.search(cmd))


class CommandRequest(BaseModel):
    command: str
    timeout: float = 30.0


@router.post("/run")
async def run_command(req: CommandRequest):
    """Execute a sandboxed command and return output."""
    if not _is_allowed(req.command):
        raise HTTPException(
            status_code=403,
            detail=f"Command not in allowlist. Allowed: {sorted(ALLOWED_COMMANDS)}",
        )

    if _has_injection(req.command):
        raise HTTPException(
            status_code=403,
            detail="Command contains blocked patterns (pipes, subshells, or code execution flags).",
        )

    timeout = min(req.timeout, 60.0)  # Cap at 60s

    try:
        proc = await asyncio.create_subprocess_shell(
            req.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
    except asyncio.TimeoutError:
        proc.kill()
        raise HTTPException(status_code=408, detail="Command timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    logger.info(f"Command executed: {req.command} (exit={proc.returncode})")

    return {
        "command": req.command,
        "exit_code": proc.returncode,
        "stdout": stdout.decode(errors="replace"),
        "stderr": stderr.decode(errors="replace"),
    }


@router.get("/allowed")
async def list_allowed():
    """List commands in the allowlist."""
    return {"allowed_commands": sorted(ALLOWED_COMMANDS)}

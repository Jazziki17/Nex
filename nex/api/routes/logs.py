"""
Logs API — serves parsed audit log entries.
"""

import json
import re
from pathlib import Path

from fastapi import APIRouter, Query

router = APIRouter()

AUDIT_FILE = Path.home() / ".nex" / "data" / "audit.log"

# Matches: "2026-02-16 10:30:45,123 | [event.type] {json...}"
_LOG_RE = re.compile(
    r"^(?P<timestamp>[\d\-]+\s[\d:,]+)\s*\|\s*\[(?P<event_type>[^\]]+)\]\s*(?P<json>.*)$"
)


@router.get("/logs")
async def get_logs(limit: int = Query(100, ge=1, le=1000)):
    """Return the last N parsed audit log entries."""
    if not AUDIT_FILE.exists():
        return {"entries": [], "total": 0}

    lines = AUDIT_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    entries = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = _LOG_RE.match(line)
        if m:
            data = {}
            try:
                data = json.loads(m.group("json"))
            except (json.JSONDecodeError, ValueError):
                data = {"raw": m.group("json")}
            entries.append({
                "timestamp": m.group("timestamp"),
                "event_type": m.group("event_type"),
                "data": data,
            })
        else:
            entries.append({
                "timestamp": "",
                "event_type": "raw",
                "data": {"raw": line},
            })

    # Return the last `limit` entries
    total = len(entries)
    entries = entries[-limit:]
    return {"entries": entries, "total": total}

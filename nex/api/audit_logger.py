"""
Audit Logger — Persistent action log for Nex.
Subscribes to key events and writes them to ~/.nex/data/audit.log
with automatic rotation (5 MB max, keeps 3 backups).
"""

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from nex.core.event_bus import EventBus
from nex.utils.logger import setup_logger

logger = setup_logger(__name__)

AUDIT_DIR = Path.home() / ".nex" / "data"
AUDIT_FILE = AUDIT_DIR / "audit.log"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

AUDITED_EVENTS = [
    "system.command",
    "command.response",
    "tool.executing",
    "tool.completed",
    "settings.updated",
    "system.ready",
    "system.module_error",
]


class AuditLogger:
    """Writes key system events to a persistent, rotating log file."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        self._audit = logging.getLogger("nex.audit")
        self._audit.setLevel(logging.INFO)
        self._audit.propagate = False
        if not self._audit.handlers:
            handler = RotatingFileHandler(
                str(AUDIT_FILE), maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT
            )
            handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
            self._audit.addHandler(handler)

    async def start(self):
        for event_type in AUDITED_EVENTS:
            self.event_bus.subscribe(event_type, self._on_event)
        logger.info(f"AuditLogger started — logging to {AUDIT_FILE}")

    async def _on_event(self, data: dict):
        event_type = data.get("_event_type", "unknown")
        # Strip internal metadata and large payloads for the log
        clean = {k: v for k, v in data.items() if not k.startswith("_")}
        # Truncate long text values
        for k, v in clean.items():
            if isinstance(v, str) and len(v) > 300:
                clean[k] = v[:300] + "..."
        self._audit.info(f"[{event_type}] {json.dumps(clean, default=str)}")

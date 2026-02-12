"""
Memory Manager — Persistent memory for Nex across sessions.
Stores user preferences, learned facts, settings, and interaction context.
Loaded on startup so Nex remembers the user.

Smart cleanup: facts have TTL and access tracking. Frequently accessed facts
survive longer. Stale facts are automatically purged on startup and every save.
"""

import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from nex.core.event_bus import EventBus
from nex.utils.logger import setup_logger

logger = setup_logger(__name__)

MEMORY_DIR = Path.home() / ".nex" / "data"
MEMORY_FILE = MEMORY_DIR / "memory.json"

DEFAULT_MEMORY = {
    "user": {"name": None, "preferences": {}},
    "facts": [],
    "settings": {"tts_voice": "Samantha", "tts_rate": "195"},
    "last_updated": None,
}

MAX_FACTS = 200
DEFAULT_TTL_DAYS = 30


class MemoryManager:
    """Manages persistent memory for Nex."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.memory: dict = {}
        self._load()

    def _load(self):
        # Auto-migrate from old ~/.kai directory
        old_dir = Path.home() / ".kai"
        new_dir = Path.home() / ".nex"
        if old_dir.exists() and not new_dir.exists():
            shutil.move(str(old_dir), str(new_dir))
            logger.info("Migrated data directory from ~/.kai to ~/.nex")

        if MEMORY_FILE.exists():
            try:
                self.memory = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
                self._migrate_facts()
                removed = self._cleanup()
                facts = self.memory.get("facts", [])
                logger.info(f"Memory loaded ({len(facts)} facts, {removed} expired removed)")
            except Exception as e:
                logger.warning(f"Failed to load memory, using defaults: {e}")
                self.memory = dict(DEFAULT_MEMORY)
        else:
            self.memory = dict(DEFAULT_MEMORY)

    def _migrate_facts(self):
        """Add new fields to old-format facts that lack them."""
        for fact in self.memory.get("facts", []):
            if "access_count" not in fact:
                fact["access_count"] = 0
            if "last_accessed" not in fact:
                fact["last_accessed"] = None
            if "ttl_days" not in fact:
                fact["ttl_days"] = DEFAULT_TTL_DAYS

    def _cleanup(self) -> int:
        """Remove expired facts. Returns count of removed facts.

        effective_ttl = ttl_days * (1 + access_count / 3)
        A fact expires when (now - timestamp).days > effective_ttl.
        Facts with ttl_days=None are permanent.
        """
        facts = self.memory.get("facts", [])
        if not facts:
            return 0
        now = datetime.now()
        kept = []
        removed = 0
        for fact in facts:
            ttl = fact.get("ttl_days")
            if ttl is None:
                kept.append(fact)
                continue
            try:
                ts = datetime.fromisoformat(fact["timestamp"])
            except (KeyError, ValueError):
                kept.append(fact)
                continue
            age_days = (now - ts).days
            access_count = fact.get("access_count", 0)
            effective_ttl = ttl * (1 + access_count / 3)
            if age_days > effective_ttl:
                removed += 1
                logger.debug(f"Expired fact (age={age_days}d, eff_ttl={effective_ttl:.0f}d): {fact['fact'][:60]}")
            else:
                kept.append(fact)
        self.memory["facts"] = kept
        return removed

    def save(self):
        self._cleanup()
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self.memory["last_updated"] = datetime.now().isoformat()
        # Enforce hard cap after cleanup
        facts = self.memory.get("facts", [])
        if len(facts) > MAX_FACTS:
            self.memory["facts"] = facts[-MAX_FACTS:]
        # Atomic write: tmp file then rename
        try:
            fd, tmp_path = tempfile.mkstemp(dir=str(MEMORY_DIR), suffix=".json.tmp")
            with os.fdopen(fd, "w") as f:
                json.dump(self.memory, f, indent=2, default=str)
            os.replace(tmp_path, str(MEMORY_FILE))
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    async def start(self):
        self.event_bus.subscribe("settings.voice_change", self._on_voice_change)
        self.event_bus.subscribe("settings.updated", self._on_setting_updated)
        logger.info("MemoryManager started")

    async def _on_voice_change(self, data: dict):
        self.memory.setdefault("settings", {})["tts_voice"] = data.get("voice", "Samantha")
        self.save()

    async def _on_setting_updated(self, data: dict):
        key = data.get("key", "")
        value = data.get("value")
        if key.startswith("speech."):
            setting_key = key.split(".", 1)[1]
            self.memory.setdefault("settings", {})[setting_key] = value
            self.save()

    def remember_fact(self, fact: str, source: str = "user", ttl_days: int | None = DEFAULT_TTL_DAYS) -> str:
        entry = {
            "fact": fact,
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "access_count": 0,
            "last_accessed": None,
            "ttl_days": ttl_days,
        }
        self.memory.setdefault("facts", []).append(entry)
        self.save()
        return f"Remembered: {fact}"

    def recall_facts(self, query: str = "") -> str:
        facts = self.memory.get("facts", [])
        if not facts:
            return "I don't have any stored memories yet."
        if query:
            q = query.lower()
            matched = [f for f in facts if q in f["fact"].lower()]
        else:
            matched = facts
        if not matched:
            return f"No memories matching '{query}'."
        # Update access tracking on matched facts
        now = datetime.now().isoformat()
        for f in matched:
            f["access_count"] = f.get("access_count", 0) + 1
            f["last_accessed"] = now
        self.save()
        lines = [f"- {f['fact']} ({f['timestamp'][:10]})" for f in matched[-20:]]
        return f"Memories ({len(matched)} total):\n" + "\n".join(lines)

    def cleanup_memory(self) -> str:
        """Public cleanup method — also exposed as an LLM tool."""
        before = len(self.memory.get("facts", []))
        removed = self._cleanup()
        after = len(self.memory.get("facts", []))
        if removed > 0:
            self.save()
        stats = self.get_stats()
        return (
            f"Memory cleanup complete. Removed {removed} expired facts "
            f"({before} → {after}). {stats}"
        )

    def get_stats(self) -> str:
        """Return memory usage stats."""
        facts = self.memory.get("facts", [])
        if not facts:
            return "Memory is empty."
        timestamps = []
        for f in facts:
            try:
                timestamps.append(datetime.fromisoformat(f["timestamp"]))
            except (KeyError, ValueError):
                pass
        oldest = min(timestamps).strftime("%Y-%m-%d") if timestamps else "?"
        newest = max(timestamps).strftime("%Y-%m-%d") if timestamps else "?"
        permanent = sum(1 for f in facts if f.get("ttl_days") is None)
        try:
            size_bytes = MEMORY_FILE.stat().st_size
            size_str = f"{size_bytes / 1024:.1f}KB"
        except OSError:
            size_str = "unknown"
        return (
            f"Total facts: {len(facts)} (permanent: {permanent}), "
            f"oldest: {oldest}, newest: {newest}, file size: {size_str}"
        )

    def set_user_name(self, name: str) -> str:
        self.memory.setdefault("user", {})["name"] = name
        self.save()
        return f"I'll remember your name is {name}."

    def set_preference(self, key: str, value: str) -> str:
        self.memory.setdefault("user", {}).setdefault("preferences", {})[key] = value
        self.save()
        return f"Preference saved: {key} = {value}"

    def get_context_for_llm(self) -> str:
        parts = []
        user = self.memory.get("user", {})
        if user.get("name"):
            parts.append(f"The user's name is {user['name']}.")
        prefs = user.get("preferences", {})
        if prefs:
            parts.append("User preferences: " + ", ".join(f"{k}: {v}" for k, v in prefs.items()))
        facts = self.memory.get("facts", [])
        if facts:
            recent = facts[-10:]
            parts.append("Things you remember:\n" + "\n".join(f"- {f['fact']}" for f in recent))
        return "\n".join(parts)

    def clear_all(self) -> str:
        self.memory = dict(DEFAULT_MEMORY)
        self.save()
        return "All memories cleared."

"""
Memory Manager — Persistent memory for Kai across sessions.
Stores user preferences, learned facts, settings, and interaction context.
Loaded on startup so Kai remembers the user.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from kai.core.event_bus import EventBus
from kai.utils.logger import setup_logger

logger = setup_logger(__name__)

MEMORY_DIR = Path.home() / ".kai" / "data"
MEMORY_FILE = MEMORY_DIR / "memory.json"

DEFAULT_MEMORY = {
    "user": {"name": None, "preferences": {}},
    "facts": [],
    "settings": {"tts_voice": "Samantha", "tts_rate": "195"},
    "last_updated": None,
}


class MemoryManager:
    """Manages persistent memory for Kai."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.memory: dict = {}
        self._load()

    def _load(self):
        if MEMORY_FILE.exists():
            try:
                self.memory = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
                facts = self.memory.get("facts", [])
                logger.info(f"Memory loaded ({len(facts)} facts)")
            except Exception as e:
                logger.warning(f"Failed to load memory, using defaults: {e}")
                self.memory = dict(DEFAULT_MEMORY)
        else:
            self.memory = dict(DEFAULT_MEMORY)

    def save(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self.memory["last_updated"] = datetime.now().isoformat()
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

    def remember_fact(self, fact: str, source: str = "user") -> str:
        entry = {"fact": fact, "timestamp": datetime.now().isoformat(), "source": source}
        self.memory.setdefault("facts", []).append(entry)
        if len(self.memory["facts"]) > 200:
            self.memory["facts"] = self.memory["facts"][-200:]
        self.save()
        return f"Remembered: {fact}"

    def recall_facts(self, query: str = "") -> str:
        facts = self.memory.get("facts", [])
        if not facts:
            return "I don't have any stored memories yet."
        if query:
            q = query.lower()
            facts = [f for f in facts if q in f["fact"].lower()]
        if not facts:
            return f"No memories matching '{query}'."
        lines = [f"- {f['fact']} ({f['timestamp'][:10]})" for f in facts[-20:]]
        return f"Memories ({len(facts)} total):\n" + "\n".join(lines)

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

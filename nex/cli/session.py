"""
Session — Transcript management, token tracking, auto-compaction, persistence.
"""

import json
import os
import time
import uuid
import datetime
from pathlib import Path

from nex.cli import renderer

# Ollama context windows (approximate)
MODEL_CONTEXT = {
    "llama3.2": 128_000,
    "qwen2.5:1.5b": 32_000,
    "qwen2.5:7b": 128_000,
    "llama3.1:8b": 128_000,
    "deepseek-coder-v2": 128_000,
}
DEFAULT_CONTEXT = 128_000

COMPACT_THRESHOLD = 0.90  # 90% triggers compaction
SESSIONS_DIR = Path.home() / ".nex" / "cli_sessions"


class Session:
    """Manages the conversation transcript, tokens, and persistence."""

    def __init__(self, model: str, cwd: str, system_prompt: str):
        self.id = str(uuid.uuid4())[:8]
        self.model = model
        self.cwd = cwd
        self.system_prompt = system_prompt
        self.transcript: list[dict] = []
        self.created_at = datetime.datetime.now().isoformat()
        self.last_active = self.created_at

        # Token tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.max_context = MODEL_CONTEXT.get(model, DEFAULT_CONTEXT)
        self.compactions = 0

        # Full history (preserved across compactions)
        self._full_history: list[dict] = []

    def add_message(self, role: str, content: str):
        """Add a message to the transcript."""
        msg = {"role": role, "content": content}
        self.transcript.append(msg)
        self._full_history.append({**msg, "timestamp": time.time()})
        self.last_active = datetime.datetime.now().isoformat()

    def build_messages(self) -> list[dict]:
        """Build the full message list for the API call."""
        return [
            {"role": "system", "content": self.system_prompt},
            *self.transcript,
        ]

    def update_tokens(self, input_tokens: int, output_tokens: int):
        """Update token counts from API response."""
        self.total_input_tokens = input_tokens  # prompt_eval_count is cumulative per call
        self.total_output_tokens += output_tokens

    @property
    def context_usage(self) -> float:
        """Return context usage as a fraction (0.0 to 1.0)."""
        if self.max_context <= 0:
            return 0.0
        # Rough estimate: transcript length in chars / 4 ≈ tokens
        estimated_tokens = sum(len(m.get("content", "")) for m in self.transcript) // 4
        estimated_tokens += len(self.system_prompt) // 4
        return min(1.0, estimated_tokens / self.max_context)

    def needs_compaction(self) -> bool:
        """Check if context is approaching the limit."""
        return self.context_usage >= COMPACT_THRESHOLD

    async def compact(self, agent, instructions: str = ""):
        """
        Compact the transcript by asking the model to summarize it.
        The summary replaces the transcript.
        """
        compact_prompt = (
            "Create a detailed continuation summary of our conversation. Preserve:\n"
            "- All files that were modified and their current state\n"
            "- All decisions made and their rationale\n"
            "- Current task status and what remains\n"
            "- Any errors encountered and how they were resolved\n"
            "- Key code patterns and architecture discovered\n"
        )
        if instructions:
            compact_prompt += f"\nAdditional focus: {instructions}\n"

        # Ask the model to summarize
        messages = self.build_messages()
        messages.append({"role": "user", "content": compact_prompt})

        import httpx
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"http://localhost:11434/api/chat", json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                })
                resp.raise_for_status()
                summary = resp.json().get("message", {}).get("content", "")
        except Exception as e:
            renderer.error(f"Compaction failed: {e}")
            return

        if not summary:
            renderer.error("Compaction produced empty summary.")
            return

        # Replace transcript with summary
        self.transcript = [
            {"role": "user", "content": f"Previous conversation summary:\n{summary}"},
            {"role": "assistant", "content": "Understood. I have the full context from our previous conversation and I'm ready to continue."},
        ]
        self.compactions += 1

        renderer.compact_notice()
        self.save()

    def show_context(self, verbose: bool = False):
        """Display context usage."""
        renderer.context_status(
            int(self.context_usage * self.max_context),
            self.max_context,
            self.model,
        )
        if verbose:
            renderer.info(f"  Messages: {len(self.transcript)}")
            renderer.info(f"  Compactions: {self.compactions}")
            renderer.info(f"  Session: {self.id}")
            renderer.info(f"  Created: {self.created_at}")

    def save(self):
        """Save session to disk."""
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "id": self.id,
            "model": self.model,
            "cwd": self.cwd,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "transcript": self.transcript,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "compactions": self.compactions,
        }
        path = SESSIONS_DIR / f"{self.id}.json"
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, session_id: str, system_prompt: str) -> "Session | None":
        """Load a session from disk."""
        path = SESSIONS_DIR / f"{session_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            session = cls(data["model"], data["cwd"], system_prompt)
            session.id = data["id"]
            session.created_at = data["created_at"]
            session.last_active = data["last_active"]
            session.transcript = data["transcript"]
            session.total_input_tokens = data.get("total_input_tokens", 0)
            session.total_output_tokens = data.get("total_output_tokens", 0)
            session.compactions = data.get("compactions", 0)
            return session
        except Exception:
            return None

    @classmethod
    def list_sessions(cls) -> list[dict]:
        """List all saved sessions."""
        if not SESSIONS_DIR.exists():
            return []
        sessions = []
        for f in sorted(SESSIONS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = json.loads(f.read_text())
                sessions.append({
                    "id": data["id"],
                    "cwd": data["cwd"],
                    "last_active": data["last_active"],
                    "messages": len(data.get("transcript", [])),
                })
            except Exception:
                continue
        return sessions[:10]  # Last 10 sessions

    def get_history(self) -> list[dict]:
        """Return full history (including before compaction)."""
        return list(self._full_history)

    def clear(self):
        """Clear transcript entirely."""
        self.transcript = []
        renderer.success("Context cleared.")

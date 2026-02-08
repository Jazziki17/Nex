"""
Speech Synthesizer - Kai's Voice
==================================

LEARNING POINT: Text-to-Speech (TTS)
---------------------------------------
TTS is the reverse of STT — it converts text into spoken audio.
Modern TTS systems produce incredibly natural-sounding voices.

The pipeline:
  Text → Text Normalization → Phoneme Conversion → Audio Synthesis → Speaker Output

Engines we could use:
  - Piper TTS: Fast, local, sounds natural, many voices
  - Coqui TTS: Open source, supports voice cloning
  - macOS `say`: Built-in, zero dependencies (great for development!)

DESIGN PATTERN: Template Method
----------------------------------
The `speak()` method defines the overall algorithm (normalize → synthesize → play).
Subclasses can override individual steps without changing the overall flow.
"""

import asyncio
import subprocess
import sys

from kai.core.engine import Module
from kai.core.event_bus import EventBus
from kai.utils.logger import setup_logger


logger = setup_logger(__name__)


class SpeechSynthesizer(Module):
    """
    Converts text responses into spoken audio output.

    LEARNING POINT: Platform Abstraction
    ---------------------------------------
    This module detects your operating system and uses the
    appropriate TTS engine automatically:
      - macOS: Uses built-in `say` command
      - Linux: Uses espeak or piper
      - Fallback: Just logs the text (still useful for development)
    """

    def __init__(self, event_bus: EventBus, voice: str = "Samantha"):
        super().__init__("SpeechSynthesizer", event_bus)
        self.voice = voice
        self._speech_queue: asyncio.Queue[str] = asyncio.Queue()
        self._speak_task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True

        # Listen for events that need spoken responses
        self.event_bus.subscribe("speech.respond", self._on_respond)

        # Start the speech queue processor
        self._speak_task = asyncio.create_task(self._process_queue())

        logger.info(f"Speech synthesizer ready (voice: {self.voice})")

    async def stop(self) -> None:
        self._running = False
        if self._speak_task:
            self._speak_task.cancel()
            try:
                await self._speak_task
            except asyncio.CancelledError:
                pass

    async def speak(self, text: str) -> None:
        """
        Add text to the speech queue.

        LEARNING POINT: Queue-Based Processing
        ----------------------------------------
        Instead of speaking immediately (which could overlap with
        other speech), we put text into a queue. A background task
        processes the queue one item at a time, ensuring orderly output.

        This is called the "Producer-Consumer" pattern:
          - Producer: anything that calls speak()
          - Consumer: _process_queue() which reads and speaks
        """
        await self._speech_queue.put(text)

    async def _process_queue(self) -> None:
        """Process speech requests one at a time."""
        while self._running:
            try:
                text = await asyncio.wait_for(
                    self._speech_queue.get(),
                    timeout=1.0,
                )
                await self._synthesize(text)
            except asyncio.TimeoutError:
                continue  # No speech to process, keep waiting

    async def _synthesize(self, text: str) -> None:
        """
        Convert text to speech using the platform's TTS engine.

        LEARNING POINT: subprocess
        ----------------------------
        `subprocess.run()` executes an external program from Python.
        Here we use macOS's built-in `say` command. The `await` with
        `run_in_executor` ensures it doesn't block the event loop.
        """
        logger.info(f'Kai says: "{text}"')

        if sys.platform == "darwin":
            # macOS — use the built-in `say` command
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ["say", "-v", self.voice, text],
                    capture_output=True,
                ),
            )
        else:
            # Other platforms — log only for now
            # To add Linux support: subprocess.run(["espeak", text])
            logger.debug(f"TTS not available on {sys.platform}, text logged only.")

    async def _on_respond(self, data: dict) -> None:
        """Handle speech response events."""
        text = data.get("text", "")
        if text:
            await self.speak(text)

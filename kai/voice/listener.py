"""
Voice Listener - The Ears of Kai
=================================

LEARNING POINT: Audio Processing Pipeline
-------------------------------------------
Audio capture is a pipeline:

  Microphone → Raw Audio Bytes → Chunks → Processing → Events

Sound is captured as a stream of numbers (samples). Each sample
represents the air pressure at a single point in time.

Key concepts:
  - Sample Rate: How many samples per second (e.g., 16000 Hz = 16000 samples/sec)
  - Channels: 1 = mono, 2 = stereo
  - Chunk Size: How many samples we process at once
  - Format: Bit depth of each sample (16-bit is common)

LEARNING POINT: Async Generators
----------------------------------
The `listen()` method is an async generator. Instead of returning all
audio at once (impossible — it's a live stream), it YIELDS chunks one
at a time. The caller uses `async for` to receive them:

    async for chunk in listener.listen():
        process(chunk)
"""

import asyncio
import struct
import math

from kai.core.engine import Module
from kai.core.event_bus import EventBus
from kai.utils.logger import setup_logger


logger = setup_logger(__name__)


class VoiceListener(Module):
    """
    Captures audio from the microphone and publishes audio events.

    LEARNING POINT: State Machine
    --------------------------------
    The listener has states: IDLE → LISTENING → PROCESSING → IDLE
    State machines are everywhere in real systems. They make it clear
    what the system is doing and what transitions are valid.
    """

    SAMPLE_RATE = 16000      # 16 kHz — standard for speech recognition
    CHANNELS = 1             # Mono audio
    CHUNK_DURATION = 0.5     # Process every 0.5 seconds
    SILENCE_THRESHOLD = 500  # Below this amplitude = silence

    def __init__(self, event_bus: EventBus):
        super().__init__("VoiceListener", event_bus)
        self._audio_stream = None
        self._listen_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start listening for audio input."""
        self._running = True

        # Subscribe to events that affect this module
        self.event_bus.subscribe("system.mute", self._on_mute)
        self.event_bus.subscribe("system.unmute", self._on_unmute)

        # Start the listening loop as a background task
        self._listen_task = asyncio.create_task(self._listen_loop())
        logger.info("Voice listener is active. Waiting for audio...")

    async def stop(self) -> None:
        """Stop listening and release the microphone."""
        self._running = False
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        logger.info("Voice listener stopped.")

    async def _listen_loop(self) -> None:
        """
        Main listening loop that captures and analyzes audio.

        LEARNING POINT: Simulation vs Real Implementation
        ---------------------------------------------------
        Right now this simulates audio input so you can run and learn
        from the code WITHOUT needing a microphone set up. When you're
        ready to use real audio, you would replace the simulation with
        PyAudio or sounddevice capture code.

        This is a common professional practice: build with simulations
        first to nail down the architecture, then plug in real hardware.
        """
        logger.debug("Listening loop started (simulation mode)")

        while self._running:
            # Simulate receiving an audio chunk
            audio_chunk = self._simulate_audio_chunk()
            amplitude = self._calculate_amplitude(audio_chunk)

            if amplitude > self.SILENCE_THRESHOLD:
                # Sound detected — publish an event
                await self.emit("audio.voice_detected", {
                    "amplitude": amplitude,
                    "duration": self.CHUNK_DURATION,
                    "sample_rate": self.SAMPLE_RATE,
                })
                logger.debug(f"Voice detected (amplitude: {amplitude:.0f})")

            # Wait before capturing next chunk
            await asyncio.sleep(self.CHUNK_DURATION)

    def _simulate_audio_chunk(self) -> list[float]:
        """
        Generate a simulated audio chunk for development/testing.

        LEARNING POINT: Sine Wave Generation
        --------------------------------------
        Sound is a wave. The simplest wave is a sine wave.
        We generate fake audio data using math.sin() to simulate
        what a microphone would capture.
        """
        import random
        chunk_size = int(self.SAMPLE_RATE * self.CHUNK_DURATION)
        # Randomly simulate silence or speech
        if random.random() < 0.3:  # 30% chance of "speech"
            frequency = random.uniform(100, 300)  # Human voice range
            return [
                math.sin(2 * math.pi * frequency * t / self.SAMPLE_RATE) * 2000
                + random.gauss(0, 100)  # Add noise
                for t in range(chunk_size)
            ]
        else:
            # Silence with ambient noise
            return [random.gauss(0, 50) for _ in range(chunk_size)]

    @staticmethod
    def _calculate_amplitude(samples: list[float]) -> float:
        """
        Calculate the RMS (Root Mean Square) amplitude of audio samples.

        LEARNING POINT: RMS
        ----------------------
        RMS is the standard way to measure "loudness" of audio.
        Steps: Square each sample → Average → Square root

        Why not just average? Because audio oscillates between positive
        and negative values, so the plain average would be near zero.
        Squaring makes everything positive first.
        """
        if not samples:
            return 0.0
        sum_of_squares = sum(s * s for s in samples)
        mean_square = sum_of_squares / len(samples)
        return math.sqrt(mean_square)

    async def _on_mute(self, data: dict) -> None:
        """Handle mute command."""
        logger.info("Microphone muted")
        self._running = False

    async def _on_unmute(self, data: dict) -> None:
        """Handle unmute command."""
        logger.info("Microphone unmuted")
        self._running = True
        self._listen_task = asyncio.create_task(self._listen_loop())

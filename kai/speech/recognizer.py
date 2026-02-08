"""
Speech Recognizer - Turning Sound into Text
=============================================

LEARNING POINT: Speech-to-Text (STT)
---------------------------------------
Speech recognition converts audio waveforms into text. The process:

  Audio → Feature Extraction → Acoustic Model → Language Model → Text

Modern STT uses deep learning models like OpenAI's Whisper.
Whisper is particularly good because:
  - It's open source and runs locally
  - It supports 99 languages
  - It's robust to accents and background noise

LEARNING POINT: Model Loading (Lazy Initialization)
------------------------------------------------------
ML models are large and slow to load. We use "lazy initialization":
the model isn't loaded until it's first needed. This means the app
starts fast, and the model only loads when you actually speak.
"""

import asyncio

from kai.core.engine import Module
from kai.core.event_bus import EventBus
from kai.utils.logger import setup_logger


logger = setup_logger(__name__)


class SpeechRecognizer(Module):
    """
    Converts speech audio into text using a speech-to-text model.

    LEARNING POINT: Encapsulation
    --------------------------------
    All the complexity of speech recognition is hidden inside this class.
    Other modules just receive a "speech.transcribed" event with text.
    They don't need to know about audio formats, models, or processing.
    """

    def __init__(self, event_bus: EventBus, model_size: str = "base"):
        super().__init__("SpeechRecognizer", event_bus)
        self.model_size = model_size
        self._model = None  # Lazy loaded

    async def start(self) -> None:
        self._running = True

        # Listen for audio events from the VoiceListener
        self.event_bus.subscribe("audio.voice_detected", self._on_voice_detected)

        logger.info(f"Speech recognizer ready (model: {self.model_size})")

    async def stop(self) -> None:
        self._running = False
        self._model = None  # Free memory
        logger.info("Speech recognizer stopped.")

    async def _on_voice_detected(self, data: dict) -> None:
        """
        Handle incoming audio and transcribe it.

        LEARNING POINT: Async Processing
        -----------------------------------
        We run transcription in a separate thread using `run_in_executor`.
        Why? Because ML inference is CPU-heavy and would block the event
        loop (freezing everything else). `run_in_executor` runs it in a
        thread pool so other modules keep running smoothly.
        """
        if not self._running:
            return

        # In production, this would receive actual audio data
        # For now, we simulate transcription
        transcribed_text = await self._transcribe(data)

        if transcribed_text:
            await self.emit("speech.transcribed", {
                "text": transcribed_text,
                "confidence": 0.92,  # Simulated confidence score
            })

    async def _transcribe(self, audio_data: dict) -> str | None:
        """
        Transcribe audio data to text.

        LEARNING POINT: Simulation for Development
        ---------------------------------------------
        This method simulates what Whisper would do. In production:

            import whisper
            model = whisper.load_model(self.model_size)
            result = model.transcribe(audio_data)
            return result["text"]

        We simulate it so you can:
        1. Run the full system without installing heavy ML dependencies
        2. Understand the data flow before adding complexity
        3. Write tests against predictable output
        """
        # Simulate processing time
        await asyncio.sleep(0.1)

        # Simulated transcriptions for development
        import random
        simulated_phrases = [
            "Hey Kai, what time is it?",
            "Kai, open my documents folder",
            "Hey Kai, play some music",
            "What's the weather like?",
            "Hey Kai, turn off the lights",
            "Kai, take a note",
        ]

        # Only "transcribe" if the amplitude suggests real speech
        if audio_data.get("amplitude", 0) > 500:
            return random.choice(simulated_phrases)

        return None

    def _load_model(self):
        """
        Load the speech recognition model.

        LEARNING POINT: Lazy Loading Pattern
        --------------------------------------
        The model is only loaded the first time we need it.
        Subsequent calls return the cached model.

        This pattern is useful for expensive resources:
            if not self._model:
                self._model = expensive_load()
            return self._model
        """
        if self._model is None:
            logger.info(f"Loading speech model ({self.model_size})... This may take a moment.")
            # Production: self._model = whisper.load_model(self.model_size)
            self._model = {"name": "whisper", "size": self.model_size}  # Placeholder
        return self._model

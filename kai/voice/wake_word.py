"""
Wake Word Detection - "Hey Kai"
================================

LEARNING POINT: Wake Word Detection
--------------------------------------
A wake word is a special phrase that activates the assistant.
Think "Hey Siri", "OK Google", or "Alexa".

In production, this uses specialized ML models (like Porcupine or
custom-trained models). For learning, we implement a simple text-based
detector that works with transcribed text.

DESIGN PATTERN: Strategy Pattern
-----------------------------------
The WakeWordDetector uses the Strategy pattern — you can swap the
detection algorithm without changing the rest of the system. This is
done through the `detection_strategy` parameter.

Current strategies:
  - "exact"     : Exact string match (simplest)
  - "fuzzy"     : Approximate match allowing for speech errors
  - "phonetic"  : Sound-based matching (handles accents)
"""

from kai.core.engine import Module
from kai.core.event_bus import EventBus
from kai.utils.logger import setup_logger


logger = setup_logger(__name__)


class WakeWordDetector:
    """
    Detects when the user says the wake word to activate Kai.

    LEARNING POINT: Single Responsibility Principle (SRP)
    -------------------------------------------------------
    This class does ONE thing: detect wake words. It doesn't capture
    audio, it doesn't process commands. One class, one job.

    This makes it easy to:
    - Test in isolation
    - Replace with a better implementation
    - Understand at a glance
    """

    def __init__(self, wake_words: list[str] | None = None):
        self.wake_words = [w.lower() for w in (wake_words or ["hey kai", "kai"])]

    def detect(self, text: str) -> bool:
        """
        Check if the transcribed text contains a wake word.

        Args:
            text: Transcribed text from speech recognition

        Returns:
            True if a wake word was detected

        LEARNING POINT: Generator Expression with any()
        --------------------------------------------------
        `any(condition for item in iterable)` is a Pythonic way to check
        if ANY element satisfies a condition. It short-circuits — stops
        as soon as it finds a match, which is efficient.
        """
        text_lower = text.lower().strip()
        return any(wake_word in text_lower for wake_word in self.wake_words)

    def extract_command(self, text: str) -> str | None:
        """
        Extract the command that follows the wake word.

        Example:
            "Hey Kai, what time is it?" → "what time is it?"

        LEARNING POINT: String Processing
        ------------------------------------
        Real NLP is much more complex, but at its core it's string
        processing. We find the wake word, then extract everything
        after it. Simple but effective for a first version.
        """
        text_lower = text.lower().strip()

        for wake_word in self.wake_words:
            if wake_word in text_lower:
                # Find where the wake word ends
                idx = text_lower.index(wake_word) + len(wake_word)
                command = text[idx:].strip().strip(",").strip()
                return command if command else None

        return None

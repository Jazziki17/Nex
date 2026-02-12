"""
Intent Classifier - Understanding What You Mean
=================================================

LEARNING POINT: Natural Language Understanding (NLU)
------------------------------------------------------
When you say "What time is it?", the system needs to understand:
  - Intent: GET_TIME (what the user wants)
  - Entities: None in this case

When you say "Set a timer for 5 minutes":
  - Intent: SET_TIMER
  - Entities: {"duration": "5 minutes"}

This process is called Intent Classification + Entity Extraction.

APPROACHES (from simple to complex):
  1. Rule-based: Pattern matching with keywords (what we build here)
  2. ML classifier: Train a model on labeled examples
  3. LLM-based: Ask a language model to understand the intent

We start with rule-based because:
  - No training data needed
  - Easy to understand and debug
  - Good enough for core commands
  - You can upgrade to ML later without changing the interface

DESIGN PATTERN: Chain of Responsibility
------------------------------------------
Each intent handler checks if it can handle the input.
If not, it passes to the next handler. This makes it
easy to add new intents without modifying existing ones.
"""

import re
from dataclasses import dataclass, field

from nex.core.engine import Module
from nex.core.event_bus import EventBus
from nex.utils.logger import setup_logger


logger = setup_logger(__name__)


@dataclass
class Intent:
    """
    Represents a classified user intent.

    LEARNING POINT: @dataclass
    ----------------------------
    The @dataclass decorator automatically generates __init__, __repr__,
    and __eq__ methods based on the fields you define. It's perfect for
    simple data containers. Instead of writing:

        class Intent:
            def __init__(self, name, confidence, entities):
                self.name = name
                self.confidence = confidence
                self.entities = entities

    You just list the fields and Python does the rest.
    """
    name: str                              # e.g., "get_time", "open_file"
    confidence: float                      # 0.0 to 1.0 — how sure we are
    entities: dict = field(default_factory=dict)  # Extracted parameters
    raw_text: str = ""                     # The original input


class IntentClassifier(Module):
    """
    Classifies user text into structured intents.

    LEARNING POINT: Separation of Concerns
    -----------------------------------------
    The classifier doesn't execute commands. It just figures out
    WHAT the user wants. A separate command handler (subscribed to
    intent events) decides HOW to do it.

    This separation means:
    - You can test understanding without executing
    - You can add new commands without changing understanding
    - You can upgrade the classifier without touching commands
    """

    def __init__(self, event_bus: EventBus):
        super().__init__("IntentClassifier", event_bus)

        # Define intent patterns
        # Each tuple: (intent_name, regex_pattern, entity_extractor)
        self._patterns: list[tuple[str, re.Pattern, callable]] = [
            (
                "get_time",
                re.compile(r"what(\s+is)?\s+(the\s+)?time", re.IGNORECASE),
                lambda m: {},
            ),
            (
                "open_file",
                re.compile(r"open\s+(?:my\s+)?(.+?)(?:\s+folder|\s+file)?$", re.IGNORECASE),
                lambda m: {"target": m.group(1).strip()},
            ),
            (
                "take_note",
                re.compile(r"(?:take|make|write)\s+(?:a\s+)?note\s*(.*)", re.IGNORECASE),
                lambda m: {"content": m.group(1).strip()} if m.group(1).strip() else {},
            ),
            (
                "set_timer",
                re.compile(r"set\s+(?:a\s+)?timer\s+(?:for\s+)?(.+)", re.IGNORECASE),
                lambda m: {"duration": m.group(1).strip()},
            ),
            (
                "play_music",
                re.compile(r"play\s+(?:some\s+)?(.+)?", re.IGNORECASE),
                lambda m: {"query": m.group(1).strip()} if m.group(1) else {},
            ),
            (
                "system_status",
                re.compile(r"(?:system\s+)?status|how\s+are\s+you", re.IGNORECASE),
                lambda m: {},
            ),
            (
                "shutdown",
                re.compile(r"shut\s*down|goodbye|exit|quit", re.IGNORECASE),
                lambda m: {},
            ),
        ]

    async def start(self) -> None:
        self._running = True
        self.event_bus.subscribe("speech.transcribed", self._on_transcription)
        logger.info(f"Intent classifier ready ({len(self._patterns)} patterns loaded)")

    async def stop(self) -> None:
        self._running = False

    def classify(self, text: str) -> Intent:
        """
        Classify text into an intent.

        LEARNING POINT: Pattern Matching with Regex
        ----------------------------------------------
        Regular expressions (regex) are powerful text matching patterns.
        Examples:
          r"what\\s+time"  — matches "what time" with any whitespace
          r"open\\s+(.+)"  — matches "open X" and captures X
          re.IGNORECASE    — matches regardless of capitalization

        The `(...)` groups capture parts of the match, which we use
        to extract entities (like the file name in "open my documents").

        Returns:
            Intent object with name, confidence, and extracted entities
        """
        text = text.strip()

        for intent_name, pattern, entity_extractor in self._patterns:
            match = pattern.search(text)
            if match:
                entities = entity_extractor(match)
                return Intent(
                    name=intent_name,
                    confidence=0.85,  # Rule-based gets a fixed confidence
                    entities=entities,
                    raw_text=text,
                )

        # No pattern matched — unknown intent
        return Intent(
            name="unknown",
            confidence=0.0,
            entities={},
            raw_text=text,
        )

    async def _on_transcription(self, data: dict) -> None:
        """Handle transcribed speech and classify the intent."""
        text = data.get("text", "")
        if not text:
            return

        intent = self.classify(text)
        logger.info(f"Intent: {intent.name} (confidence: {intent.confidence:.0%})")

        if intent.entities:
            logger.debug(f"  Entities: {intent.entities}")

        # Publish the classified intent for command handlers
        await self.emit("intent.classified", {
            "intent": intent.name,
            "confidence": intent.confidence,
            "entities": intent.entities,
            "raw_text": intent.raw_text,
        })

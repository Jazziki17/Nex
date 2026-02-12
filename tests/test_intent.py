"""
Tests for Intent Classification
==================================

LEARNING POINT: Parameterized Tests
--------------------------------------
When you want to test the same logic with many different inputs,
use `@pytest.mark.parametrize`. This creates a separate test for
each set of parameters — much cleaner than writing 10 separate
test functions that all look the same.
"""

import pytest

from nex.core.event_bus import EventBus
from nex.speech.intent import IntentClassifier, Intent


@pytest.fixture
def classifier():
    """Create an IntentClassifier for testing."""
    bus = EventBus()
    return IntentClassifier(event_bus=bus)


# ─── Parameterized Tests ────────────────────────────────────

@pytest.mark.parametrize("text, expected_intent", [
    ("What time is it?", "get_time"),
    ("what is the time", "get_time"),
    ("open my documents folder", "open_file"),
    ("open photos", "open_file"),
    ("take a note buy groceries", "take_note"),
    ("make a note", "take_note"),
    ("set a timer for 5 minutes", "set_timer"),
    ("set timer for 30 seconds", "set_timer"),
    ("play some music", "play_music"),
    ("play jazz", "play_music"),
    ("system status", "system_status"),
    ("how are you", "system_status"),
    ("shutdown", "shutdown"),
    ("goodbye", "shutdown"),
    ("exit", "shutdown"),
])
def test_classify_known_intents(classifier, text, expected_intent):
    """Test that known phrases are classified correctly."""
    result = classifier.classify(text)
    assert result.name == expected_intent
    assert result.confidence > 0


def test_classify_unknown_intent(classifier):
    """Test that unrecognized text returns 'unknown'."""
    result = classifier.classify("asdfghjkl random gibberish")
    assert result.name == "unknown"
    assert result.confidence == 0.0


def test_entity_extraction_open_file(classifier):
    """Test that entity extraction works for file commands."""
    result = classifier.classify("open my documents folder")
    assert result.entities.get("target") == "my documents"


def test_entity_extraction_timer(classifier):
    """Test entity extraction for timer commands."""
    result = classifier.classify("set a timer for 10 minutes")
    assert result.entities.get("duration") == "10 minutes"


def test_entity_extraction_note(classifier):
    """Test entity extraction for note-taking."""
    result = classifier.classify("take a note buy milk and eggs")
    assert "buy milk and eggs" in result.entities.get("content", "")


def test_intent_has_raw_text(classifier):
    """Test that the original text is preserved in the Intent."""
    text = "What time is it?"
    result = classifier.classify(text)
    assert result.raw_text == text


def test_intent_is_dataclass():
    """
    Test that Intent is a proper dataclass.

    LEARNING POINT: Testing Data Structures
    ------------------------------------------
    Dataclasses automatically generate __eq__, so you can compare
    two Intent objects directly. This test verifies that behavior.
    """
    intent1 = Intent(name="test", confidence=0.9, raw_text="hello")
    intent2 = Intent(name="test", confidence=0.9, raw_text="hello")
    assert intent1 == intent2

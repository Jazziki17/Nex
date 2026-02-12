"""
Tests for Wake Word Detection
================================
"""

import pytest

from nex.voice.wake_word import WakeWordDetector


@pytest.fixture
def detector():
    return WakeWordDetector()


@pytest.mark.parametrize("text", [
    "Hey Nex, what time is it?",
    "hey nex turn off the lights",
    "Nex, play some music",
    "nex help me",
])
def test_detects_wake_word(detector, text):
    """Test that various wake word phrases are detected."""
    assert detector.detect(text) is True


@pytest.mark.parametrize("text", [
    "What time is it?",
    "Play some music",
    "Hello there",
    "",
])
def test_no_wake_word(detector, text):
    """Test that non-wake-word phrases are not detected."""
    assert detector.detect(text) is False


def test_extract_command(detector):
    """Test command extraction after wake word."""
    command = detector.extract_command("Hey Nex, what time is it?")
    assert command == "what time is it?"


def test_extract_command_no_content(detector):
    """Test extraction when nothing follows the wake word."""
    command = detector.extract_command("Hey Nex")
    assert command is None


def test_custom_wake_words():
    """Test with custom wake words."""
    detector = WakeWordDetector(wake_words=["jarvis", "computer"])
    assert detector.detect("Jarvis, do something") is True
    assert detector.detect("Computer, report") is True
    assert detector.detect("Hey Nex") is False

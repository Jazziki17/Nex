"""
Tests for the Event Bus
=========================

LEARNING POINT: Unit Testing
-------------------------------
Unit tests verify that individual pieces of code work correctly
IN ISOLATION. Each test:

1. ARRANGE — Set up the test conditions
2. ACT — Run the code being tested
3. ASSERT — Verify the result is correct

LEARNING POINT: pytest
-------------------------
pytest is the most popular Python testing framework. Key features:
  - Tests are just functions starting with `test_`
  - Use plain `assert` statements
  - `pytest.fixture` creates reusable test setup
  - Run with: `pytest tests/` from the project root

NAMING CONVENTION:
  test_<what>_<scenario>_<expected_result>
  Example: test_publish_with_subscribers_calls_all_handlers
"""

import asyncio
import pytest

from nex.core.event_bus import EventBus


# ─── Fixtures ────────────────────────────────────────────────
# Fixtures provide reusable test setup. Any test that has a
# parameter named "event_bus" will automatically receive a
# fresh EventBus instance.

@pytest.fixture
def event_bus():
    """Create a fresh EventBus for each test."""
    return EventBus()


# ─── Tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_subscribe_and_publish(event_bus):
    """Test that a subscriber receives published events."""
    # ARRANGE
    received = []

    async def handler(data):
        received.append(data)

    event_bus.subscribe("test_event", handler)

    # ACT
    await event_bus.publish("test_event", {"message": "hello"})

    # ASSERT
    assert len(received) == 1
    assert received[0]["message"] == "hello"


@pytest.mark.asyncio
async def test_multiple_subscribers(event_bus):
    """Test that multiple subscribers all receive the event."""
    results = []

    async def handler_a(data):
        results.append("A")

    async def handler_b(data):
        results.append("B")

    event_bus.subscribe("test_event", handler_a)
    event_bus.subscribe("test_event", handler_b)

    await event_bus.publish("test_event", {})

    assert "A" in results
    assert "B" in results
    assert len(results) == 2


@pytest.mark.asyncio
async def test_publish_without_subscribers(event_bus):
    """Test that publishing to an event with no subscribers doesn't crash."""
    # This should NOT raise an exception
    await event_bus.publish("nonexistent_event", {"data": 42})


@pytest.mark.asyncio
async def test_unsubscribe(event_bus):
    """Test that unsubscribed handlers no longer receive events."""
    received = []

    async def handler(data):
        received.append(data)

    event_bus.subscribe("test_event", handler)
    event_bus.unsubscribe("test_event", handler)

    await event_bus.publish("test_event", {"message": "should not arrive"})

    assert len(received) == 0


@pytest.mark.asyncio
async def test_event_history(event_bus):
    """Test that the event bus keeps a history of events."""
    await event_bus.publish("event_1", {"n": 1})
    await event_bus.publish("event_2", {"n": 2})

    history = event_bus.get_history()

    assert len(history) == 2
    assert history[0]["type"] == "event_1"
    assert history[1]["type"] == "event_2"


@pytest.mark.asyncio
async def test_subscriber_count(event_bus):
    """Test the subscriber count property."""
    async def dummy(data):
        pass

    event_bus.subscribe("event_a", dummy)
    event_bus.subscribe("event_a", dummy)
    event_bus.subscribe("event_b", dummy)

    counts = event_bus.subscriber_count
    assert counts["event_a"] == 2
    assert counts["event_b"] == 1


@pytest.mark.asyncio
async def test_handler_error_does_not_crash_others(event_bus):
    """
    Test that one failing handler doesn't prevent others from running.

    LEARNING POINT: Fault Tolerance
    ----------------------------------
    In a real system, you can't let one buggy subscriber crash the
    entire event system. The `return_exceptions=True` in asyncio.gather
    catches exceptions and lets other handlers complete.
    """
    results = []

    async def bad_handler(data):
        raise ValueError("I'm broken!")

    async def good_handler(data):
        results.append("success")

    event_bus.subscribe("test_event", bad_handler)
    event_bus.subscribe("test_event", good_handler)

    await event_bus.publish("test_event", {})

    # The good handler should still have been called
    assert "success" in results

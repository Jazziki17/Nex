"""
Kai Entry Point
===============

LEARNING POINT: __main__.py
----------------------------
This file is what runs when you execute a package as a script:

    python -m kai

Python looks for __main__.py inside the package and runs it.
Think of it as the "front door" of your application.

PATTERN USED: Composition Root
-------------------------------
This is where we wire everything together. Instead of modules creating
their own dependencies, we create them here and pass them in. This is
called "Dependency Injection" — one of the most important patterns in
professional software engineering.

WHY? Because it makes your code:
  1. Testable — you can pass in fake/mock dependencies
  2. Flexible — swap implementations without changing module code
  3. Clear — you can see the full system wiring in one place
"""

import asyncio
import signal
import sys

from kai.core.engine import KaiEngine
from kai.utils.logger import setup_logger


logger = setup_logger(__name__)


async def main():
    """
    The main async function that boots up Kai.

    LEARNING POINT: async/await
    ----------------------------
    Kai uses asynchronous programming because it needs to do multiple
    things at once (listen for voice, watch camera, etc.) WITHOUT
    blocking each other.

    Think of it like a restaurant:
    - Synchronous  = one waiter who finishes each table before moving on
    - Asynchronous = one waiter who takes an order, goes to the next
                     table while the kitchen prepares, comes back when ready

    `async def` declares a coroutine (a function that can pause and resume).
    `await` pauses the coroutine until the awaited task completes.
    """

    logger.info("=" * 50)
    logger.info("  Kai AI Assistant - Starting Up")
    logger.info("=" * 50)

    # --- Create the engine (the brain of Kai) ---
    engine = KaiEngine()

    # --- Handle graceful shutdown ---
    # When you press Ctrl+C, we want to clean up properly
    # instead of just crashing.
    def handle_shutdown(sig, frame):
        logger.info("Shutdown signal received. Cleaning up...")
        asyncio.get_event_loop().create_task(engine.shutdown())

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # --- Start the engine ---
    try:
        await engine.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    finally:
        await engine.shutdown()
        logger.info("Kai has shut down. Goodbye.")


if __name__ == "__main__":
    # asyncio.run() creates an event loop and runs our main coroutine
    asyncio.run(main())

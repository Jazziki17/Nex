"""
Nex Core Engine - The Brain
============================

LEARNING POINT: Orchestrator Pattern
--------------------------------------
The Engine is the central coordinator. It doesn't DO the work itself —
it manages the modules that do. Think of it as a conductor in an orchestra:
the conductor doesn't play any instrument, but makes sure everyone plays
together in harmony.

LEARNING POINT: Abstract Base Classes (ABC)
---------------------------------------------
We define a `Module` base class that all modules must follow.
This is called "programming to an interface" — you define WHAT
a module must do, not HOW it does it. This means you can swap
implementations freely (e.g., replace one speech engine with another).

LEARNING POINT: Lifecycle Management
--------------------------------------
Every module goes through a lifecycle:
  1. Initialize — set up resources
  2. Start — begin processing
  3. Stop — clean up resources

The engine manages this lifecycle for all modules.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any

from nex.core.event_bus import EventBus
from nex.utils.logger import setup_logger


logger = setup_logger(__name__)


class Module(ABC):
    """
    Abstract base class that all Nex modules must implement.

    LEARNING POINT: ABC (Abstract Base Class)
    -------------------------------------------
    - `ABC` means this class cannot be instantiated directly
    - `@abstractmethod` means subclasses MUST implement these methods
    - If a subclass forgets to implement an abstract method, Python
      raises TypeError at instantiation time — catching bugs early

    This is like a contract: "If you want to be a Nex module,
    you MUST provide these methods."
    """

    def __init__(self, name: str, event_bus: EventBus):
        self.name = name
        self.event_bus = event_bus
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    @abstractmethod
    async def start(self) -> None:
        """Start the module. Must be implemented by subclasses."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the module and clean up resources."""
        ...

    async def emit(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        """
        Convenience method to publish an event from this module.
        Automatically tags the event with the module name.
        """
        if data is None:
            data = {}
        data["source_module"] = self.name
        await self.event_bus.publish(event_type, data)


class NexEngine:
    """
    The central engine that orchestrates all modules.

    LEARNING POINT: Composition over Inheritance
    ----------------------------------------------
    Notice how NexEngine doesn't inherit from Module — it CONTAINS modules.
    This is "composition": building complex objects by combining simpler ones.
    It's generally preferred over deep inheritance hierarchies because it's
    more flexible.
    """

    def __init__(self):
        self.event_bus = EventBus()
        self._modules: list[Module] = []
        self._running = False

        # Register core event handlers
        self.event_bus.subscribe("system.module_error", self._on_module_error)
        self.event_bus.subscribe("system.command", self._on_command)

    def register_module(self, module: Module) -> None:
        """
        Add a module to the engine.

        LEARNING POINT: Dependency Injection
        -------------------------------------
        Modules are created externally and passed in. The engine doesn't
        create modules itself. This means:
        - You control what modules are loaded
        - You can pass mock modules for testing
        - Modules can be swapped without changing engine code
        """
        self._modules.append(module)
        logger.info(f"Module registered: {module.name}")

    async def start(self) -> None:
        """
        Start all registered modules and enter the main loop.

        LEARNING POINT: Error Isolation
        --------------------------------
        Each module starts in its own try/except block. If one module
        fails to start, the others still run. This is called "fault isolation"
        and is critical in real systems — you don't want a camera failure
        to prevent voice commands from working.
        """
        logger.info("Nex Engine starting...")
        self._running = True

        # Import and register all available modules
        await self._discover_and_register_modules()

        # Start each module
        for module in self._modules:
            try:
                await module.start()
                logger.info(f"  [OK] {module.name}")
            except Exception as e:
                logger.error(f"  [FAIL] {module.name}: {e}")

        await self.event_bus.publish("system.ready", {
            "modules_loaded": [m.name for m in self._modules],
        })

        logger.info("Nex is ready. Listening for input...")
        logger.info("Press Ctrl+C to shut down.\n")

        # Main loop — keeps the program alive
        await self._main_loop()

    async def _discover_and_register_modules(self) -> None:
        """
        Discover and register all available modules.

        LEARNING POINT: Graceful Degradation
        --------------------------------------
        We try to import each module, but if a dependency is missing
        (e.g., PyAudio not installed), we skip that module instead of
        crashing. The system runs with whatever modules ARE available.
        """
        # Try to register each module — skip if dependencies are missing
        module_loaders = [
            ("Voice Listener", "nex.voice.listener", "VoiceListener"),
            ("Speech Recognizer", "nex.speech.recognizer", "SpeechRecognizer"),
            ("Speech Synthesizer", "nex.speech.synthesizer", "SpeechSynthesizer"),
            ("Intent Classifier", "nex.speech.intent", "IntentClassifier"),
            ("Camera Stream", "nex.vision.camera", "CameraStream"),
            ("Motion Detector", "nex.vision.motion", "MotionDetector"),
            ("Gesture Recognizer", "nex.vision.gesture", "GestureRecognizer"),
            ("File Manager", "nex.io.file_manager", "FileManager"),
        ]

        for display_name, module_path, class_name in module_loaders:
            try:
                # Dynamic import — loads the module only if available
                import importlib
                mod = importlib.import_module(module_path)
                cls = getattr(mod, class_name)
                instance = cls(event_bus=self.event_bus)
                self.register_module(instance)
            except ImportError as e:
                logger.warning(f"  [SKIP] {display_name} — missing dependency: {e}")
            except Exception as e:
                logger.warning(f"  [SKIP] {display_name} — error: {e}")

    async def _main_loop(self) -> None:
        """
        The main event loop that keeps Nex alive.

        LEARNING POINT: Event Loop
        ----------------------------
        This loop is the heartbeat of the application. It runs forever,
        sleeping briefly each iteration to avoid consuming 100% CPU.
        Real work happens in the modules (running as async tasks).
        """
        while self._running:
            await asyncio.sleep(0.1)

    async def shutdown(self) -> None:
        """Stop all modules and clean up."""
        if not self._running:
            return

        logger.info("Shutting down Nex...")
        self._running = False

        # Stop modules in reverse order (last started = first stopped)
        for module in reversed(self._modules):
            try:
                await module.stop()
                logger.info(f"  [STOPPED] {module.name}")
            except Exception as e:
                logger.error(f"  [ERROR] stopping {module.name}: {e}")

    async def _on_module_error(self, data: dict) -> None:
        """Handle errors reported by modules."""
        logger.error(f"Module error in {data.get('module')}: {data.get('error')}")

    async def _on_command(self, data: dict) -> None:
        """Handle system-level commands."""
        command = data.get("command")
        if command == "shutdown":
            await self.shutdown()
        elif command == "status":
            status = {m.name: m.is_running for m in self._modules}
            logger.info(f"Module status: {status}")

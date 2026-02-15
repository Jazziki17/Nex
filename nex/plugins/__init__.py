"""
Nex Plugin System
=================
Drop Python files into this directory to auto-load them as Nex modules.

Each plugin file should export a class that inherits from nex.core.engine.Module
and takes event_bus as a constructor argument.

Example plugin (nex/plugins/my_plugin.py):

    from nex.core.engine import Module
    from nex.core.event_bus import EventBus

    class MyPlugin(Module):
        def __init__(self, event_bus: EventBus):
            super().__init__("MyPlugin", event_bus)

        async def start(self):
            self._running = True
            self.event_bus.subscribe("system.command", self.on_command)

        async def stop(self):
            self._running = False

        async def on_command(self, data):
            pass
"""

import importlib
import inspect
from pathlib import Path

from nex.core.engine import Module
from nex.utils.logger import setup_logger

logger = setup_logger(__name__)

PLUGIN_DIR = Path(__file__).parent


def discover_plugins(event_bus) -> list[Module]:
    """Scan the plugins directory and instantiate any Module subclasses found."""
    plugins = []
    for path in sorted(PLUGIN_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        module_name = f"nex.plugins.{path.stem}"
        try:
            mod = importlib.import_module(module_name)
            for attr_name in dir(mod):
                obj = getattr(mod, attr_name)
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, Module)
                    and obj is not Module
                ):
                    instance = obj(event_bus=event_bus)
                    plugins.append(instance)
                    logger.info(f"  Plugin discovered: {instance.name} ({path.name})")
        except Exception as e:
            logger.warning(f"  Plugin load failed ({path.name}): {e}")
    return plugins

"""
System Monitor — Collects live PC performance stats using psutil
and publishes them via EventBus for real-time dashboard display.
"""

import asyncio

import psutil

from kai.core.event_bus import EventBus
from kai.utils.logger import setup_logger

logger = setup_logger(__name__)

POLL_INTERVAL = 2.0


class SystemMonitor:
    """Periodically collects system stats and publishes them."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self):
        self._running = True
        # Initial CPU call so first poll isn't 0%
        psutil.cpu_percent(interval=None)
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("SystemMonitor started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    async def _poll_loop(self):
        while self._running:
            try:
                stats = self._collect()
                await self.event_bus.publish("system.stats", stats)
            except Exception as e:
                logger.warning(f"Stats collection error: {e}")
            await asyncio.sleep(POLL_INTERVAL)

    def _collect(self) -> dict:
        cpu_percent = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()
        battery = psutil.sensors_battery()

        return {
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count(),
            },
            "memory": {
                "total_gb": round(mem.total / (1024**3), 1),
                "used_gb": round(mem.used / (1024**3), 1),
                "percent": mem.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 1),
                "used_gb": round(disk.used / (1024**3), 1),
                "percent": round(disk.percent, 1),
            },
            "network": {
                "bytes_sent": net.bytes_sent,
                "bytes_recv": net.bytes_recv,
            },
            "battery": {
                "percent": battery.percent,
                "plugged": battery.power_plugged,
            } if battery else None,
        }

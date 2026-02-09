"""Status route — /api/status with real engine data."""

import time

from fastapi import APIRouter

router = APIRouter(tags=["status"])

_start_time = time.time()


@router.get("/status")
async def get_status():
    """Return engine status with module information."""
    from kai.api.server import engine

    uptime = time.time() - _start_time

    if engine is None:
        return {
            "status": "starting",
            "modules": {},
            "uptime": uptime,
            "event_history_count": 0,
        }

    modules = {}
    for module in engine._modules:
        modules[module.name] = {
            "status": "active" if module.is_running else "stopped",
        }

    return {
        "status": "online",
        "modules": modules,
        "uptime": uptime,
        "event_history_count": len(engine.event_bus.get_history()),
        "subscriber_count": engine.event_bus.subscriber_count,
    }

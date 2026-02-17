"""
Modules API — reports loaded module names and status.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/modules")
async def get_modules():
    """Return list of loaded modules with status."""
    from nex.api.server import engine

    if engine is None:
        return {"modules": []}

    modules = []

    # Core modules registered on the engine
    for m in engine._modules:
        modules.append({
            "name": m.name,
            "status": "running" if m.is_running else "stopped",
            "type": "core",
        })

    # Standalone services attached to engine
    standalone = [
        ("MemoryManager", "_memory"),
        ("SystemMonitor", "_sys_monitor"),
        ("AuditLogger", "_audit_logger"),
        ("MicListener", "_mic_listener"),
    ]
    for name, attr in standalone:
        obj = getattr(engine, attr, None)
        if obj is not None:
            running = getattr(obj, "_running", None)
            if running is None:
                running = True  # assume running if no flag
            modules.append({
                "name": name,
                "status": "running" if running else "stopped",
                "type": "core",
            })

    # CommandHandler is always present if engine is running
    if engine._running:
        modules.append({
            "name": "CommandHandler",
            "status": "running",
            "type": "core",
        })

    return {"modules": modules}

"""
Nex API Server — FastAPI application
======================================
Serves the orb UI as static files, provides REST endpoints for file ops,
commands, and status, and bridges WebSocket for real-time events.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from nex.api.routes import commands, files, spreadsheets, status
from nex.api.routes.settings import router as settings_router
from nex.api.websocket_handler import router as ws_router
from nex.core.engine import NexEngine
from nex.utils.logger import setup_logger

logger = setup_logger(__name__)

PORT = 8420

STATIC_DIR = Path(__file__).parent.parent / "ui" / "static"

# Shared engine instance — set during lifespan
engine: NexEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start NexEngine on startup, shut down on exit."""
    global engine
    engine = NexEngine()

    # Start engine (discovers and starts modules) without blocking
    import asyncio
    engine_task = asyncio.create_task(_start_engine(engine))

    yield

    # Shutdown
    await engine.shutdown()
    engine_task.cancel()
    engine = None


async def _start_engine(eng: NexEngine):
    """
    Start only the modules that do real work.
    Simulation modules (voice, speech, vision) are NOT loaded —
    they create a feedback loop of fake events and TTS spam.
    """
    try:
        # Only load FileManager — the one module that does real I/O
        try:
            from nex.io.file_manager import FileManager
            fm = FileManager(event_bus=eng.event_bus)
            eng.register_module(fm)
            await fm.start()
            logger.info("  [OK] FileManager")
        except Exception as e:
            logger.warning(f"  [SKIP] FileManager: {e}")

        # Start Memory Manager (before CommandHandler so it can use it)
        from nex.api.memory_manager import MemoryManager
        memory_mgr = MemoryManager(eng.event_bus)
        await memory_mgr.start()
        eng._memory = memory_mgr
        logger.info("  [OK] MemoryManager")

        # Start System Monitor (background stats polling)
        from nex.api.system_monitor import SystemMonitor
        sys_monitor = SystemMonitor(eng.event_bus)
        await sys_monitor.start()
        eng._sys_monitor = sys_monitor
        logger.info("  [OK] SystemMonitor")

        # Start the command handler (processes real commands)
        from nex.api.command_handler import CommandHandler
        handler = CommandHandler(eng.event_bus, memory_manager=memory_mgr)
        await handler.start()
        logger.info("  [OK] CommandHandler")

        # Start MicListener (real microphone → whisper STT → commands)
        mic = None
        try:
            from nex.voice.mic_listener import MicListener
            mic = MicListener(eng.event_bus)
            await mic.start()
            eng._mic_listener = mic
            logger.info("  [OK] MicListener")
        except Exception as e:
            logger.warning(f"  [SKIP] MicListener: {e}")

        loaded = [m.name for m in eng._modules] + ["MemoryManager", "SystemMonitor", "CommandHandler"]
        if mic:
            loaded.append("MicListener")
        await eng.event_bus.publish("system.ready", {
            "modules_loaded": loaded,
        })
        eng._running = True
        logger.info("Nex engine ready.")
    except Exception as e:
        logger.error(f"Engine startup error: {e}")


def get_engine() -> NexEngine:
    """Get the running engine instance."""
    if engine is None:
        raise RuntimeError("Engine not started")
    return engine


# ─── Create App ────────────────────────────────────────────

app = FastAPI(title="Nex API", version="0.1.0", lifespan=lifespan)

# CORS — allow Electron and mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(status.router, prefix="/api")
app.include_router(files.router, prefix="/api/files")
app.include_router(commands.router, prefix="/api/commands")
app.include_router(spreadsheets.router, prefix="/api/files")
app.include_router(settings_router, prefix="/api/settings")
app.include_router(ws_router)

# Redirect bare paths to trailing slash so StaticFiles serves index.html
@app.get("/ui")
async def redirect_ui():
    return RedirectResponse(url="/ui/")


@app.get("/")
async def redirect_root():
    return RedirectResponse(url="/ui/")


# Serve the orb UI at /ui
if STATIC_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(STATIC_DIR), html=True), name="ui")

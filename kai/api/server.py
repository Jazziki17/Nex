"""
Kai API Server — FastAPI application
======================================
Serves the orb UI as static files, provides REST endpoints for file ops,
commands, and status, and bridges WebSocket for real-time events.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from kai.api.routes import commands, files, spreadsheets, status
from kai.api.websocket_handler import router as ws_router
from kai.core.engine import KaiEngine
from kai.utils.logger import setup_logger

logger = setup_logger(__name__)

PORT = 8420

STATIC_DIR = Path(__file__).parent.parent / "ui" / "static"

# Shared engine instance — set during lifespan
engine: KaiEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start KaiEngine on startup, shut down on exit."""
    global engine
    engine = KaiEngine()

    # Start engine (discovers and starts modules) without blocking
    import asyncio
    engine_task = asyncio.create_task(_start_engine(engine))

    yield

    # Shutdown
    await engine.shutdown()
    engine_task.cancel()
    engine = None


async def _start_engine(eng: KaiEngine):
    """Run engine startup in background so server starts immediately."""
    try:
        await eng._discover_and_register_modules()
        for module in eng._modules:
            try:
                await module.start()
                logger.info(f"  [OK] {module.name}")
            except Exception as e:
                logger.error(f"  [FAIL] {module.name}: {e}")

        await eng.event_bus.publish("system.ready", {
            "modules_loaded": [m.name for m in eng._modules],
        })
        eng._running = True
        logger.info("Kai engine ready.")
    except Exception as e:
        logger.error(f"Engine startup error: {e}")


def get_engine() -> KaiEngine:
    """Get the running engine instance."""
    if engine is None:
        raise RuntimeError("Engine not started")
    return engine


# ─── Create App ────────────────────────────────────────────

app = FastAPI(title="Kai API", version="0.1.0", lifespan=lifespan)

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
app.include_router(ws_router)

# Serve the orb UI at /ui (and also at root for convenience)
if STATIC_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(STATIC_DIR), html=True), name="ui")
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="root")

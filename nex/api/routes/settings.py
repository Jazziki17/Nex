"""Settings routes — preferences."""

import shutil
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(tags=["settings"])


@router.get("/voices")
async def list_voices():
    return {"voices": [{"name": "Andrew", "id": "en-US-AndrewMultilingualNeural"}]}


@router.get("/current")
async def get_settings():
    from nex.api.server import engine
    if engine and hasattr(engine, '_memory'):
        user = engine._memory.memory.get("user", {})
        return {"voice": "Andrew", "user_name": user.get("name")}
    return {"voice": "Andrew", "user_name": None}


@router.get("/voice-auth-status")
async def voice_auth_status():
    try:
        from nex.api.voice_auth import VoiceAuth
        va = VoiceAuth()
        return {"enrolled": va.is_enrolled(), "available": True}
    except ImportError:
        return {"enrolled": False, "available": False}


@router.post("/clear-cache")
async def clear_cache():
    """Clear __pycache__ directories under the Nex runtime folder."""
    nex_root = Path.home() / "Nex"
    removed = 0
    for cache_dir in nex_root.rglob("__pycache__"):
        if cache_dir.is_dir():
            shutil.rmtree(cache_dir, ignore_errors=True)
            removed += 1
    return {"cleared": removed, "message": f"Removed {removed} cache directories"}

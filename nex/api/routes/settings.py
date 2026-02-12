"""Settings routes — voice selection, preferences."""

import asyncio
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["settings"])


class VoiceRequest(BaseModel):
    voice: str


@router.get("/voices")
async def list_voices():
    proc = await asyncio.create_subprocess_exec(
        "say", "-v", "?", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
    )
    stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
    voices = []
    for line in stdout.decode().strip().split("\n"):
        parts = line.strip().split()
        if len(parts) >= 2:
            voices.append({"name": parts[0], "language": parts[1]})
    return {"voices": voices}


@router.post("/voice")
async def set_voice(req: VoiceRequest):
    from nex.api.server import engine
    if engine:
        await engine.event_bus.publish("settings.voice_change", {"voice": req.voice})
    return {"status": "ok", "voice": req.voice}


@router.get("/current")
async def get_settings():
    from nex.api.server import engine
    if engine and hasattr(engine, '_memory'):
        settings = engine._memory.memory.get("settings", {})
        user = engine._memory.memory.get("user", {})
        return {"voice": settings.get("tts_voice", "Samantha"), "user_name": user.get("name")}
    return {"voice": "Samantha", "user_name": None}

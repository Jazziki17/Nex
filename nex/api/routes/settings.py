"""Settings routes — preferences."""

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

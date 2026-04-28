from app.core.config import get_settings
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "environment": settings.app_env,
        "providers": {
            "database_configured": bool(settings.database_url),
            "livekit_configured": bool(
                settings.livekit_url and settings.livekit_api_key and settings.livekit_api_secret
            ),
            "openai_configured": bool(settings.openai_api_key),
            "deepgram_configured": bool(settings.deepgram_api_key),
            "cartesia_configured": bool(settings.cartesia_api_key),
        },
    }

from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health", summary="Health Check")
async def health_check():
    """
    Returns server status, current configuration and timestamp.
    Used by the mobile client to verify connectivity and latency.
    """
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.OLLAMA_MODEL
    }

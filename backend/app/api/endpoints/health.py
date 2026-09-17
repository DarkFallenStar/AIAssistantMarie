from fastapi import APIRouter

router = APIRouter()

@router.get("/health", summary="Health Check")
async def health_check():
    """
    Endpoint de salud básico para comprobar que el backend está en línea.
    """
    return {"status": "ok"}

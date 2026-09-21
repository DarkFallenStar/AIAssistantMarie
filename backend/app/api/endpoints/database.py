from fastapi import APIRouter, Depends
from app.core.database import check_database_connection
from app.core.security import verify_api_bearer_token

router = APIRouter()

@router.get("/db/status", summary="Estado de Conexión a Base de Datos (Supabase)")
async def database_status(_authorized: bool = Depends(verify_api_bearer_token)):
    """
    Verifica y reporta el estado de conectividad con Supabase / PostgreSQL.
    """
    return await check_database_connection()

from fastapi import APIRouter
from app.core.database import check_database_connection

router = APIRouter()

@router.get("/db/status", summary="Estado de Conexión a Base de Datos (Supabase)")
async def database_status():
    """
    Verifica y reporta el estado de conectividad con Supabase / PostgreSQL.
    """
    return await check_database_connection()

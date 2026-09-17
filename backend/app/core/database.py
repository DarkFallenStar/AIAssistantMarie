from typing import Optional, Dict, Any
from supabase import create_client, Client
from app.core.config import settings

# Global cached client
_supabase_client: Optional[Client] = None

REQUIRED_SCHEMA_TABLES = [
    "users",
    "tasks",
    "emails",
    "financial_accounts",
    "credit_cards",
    "loans",
    "saving_goals",
    "transactions"
]

def get_supabase_client() -> Optional[Client]:
    """
    Returns the initialized Supabase client singleton, or None if credentials are not configured.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        return None

    try:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return _supabase_client
    except Exception as e:
        print(f"[Supabase] Error initializing client: {e}")
        return None

async def check_database_connection() -> Dict[str, Any]:
    """
    Verifies connection status to Supabase and reports configuration state.
    """
    is_configured = bool(settings.SUPABASE_URL and settings.SUPABASE_KEY)
    
    if not is_configured:
        return {
            "status": "unconfigured",
            "connected": False,
            "message": "SUPABASE_URL o SUPABASE_KEY no están configuradas en backend/.env",
            "tables_defined": REQUIRED_SCHEMA_TABLES
        }
    
    client = get_supabase_client()
    if not client:
        return {
            "status": "error",
            "connected": False,
            "message": "Error al instanciar el cliente de Supabase con las credenciales dadas",
            "tables_defined": REQUIRED_SCHEMA_TABLES
        }

    try:
        # Test basic query on users table
        response = client.table("users").select("id", count="exact").limit(1).execute()
        return {
            "status": "connected",
            "connected": True,
            "message": "Conexión a Supabase establecida exitosamente",
            "supabase_url": settings.SUPABASE_URL,
            "tables_defined": REQUIRED_SCHEMA_TABLES
        }
    except Exception as e:
        return {
            "status": "reachable_with_schema_notice",
            "connected": False,
            "message": f"Conexión con Supabase alcanzada pero tabla users no responde (¿esquema ejecutado?): {str(e)}",
            "supabase_url": settings.SUPABASE_URL,
            "tables_defined": REQUIRED_SCHEMA_TABLES
        }

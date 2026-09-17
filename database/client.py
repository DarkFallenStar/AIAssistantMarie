import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde backend/.env si existe
env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def get_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Aviso: SUPABASE_URL o SUPABASE_KEY no configuradas en backend/.env")
        return None
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Error al conectar con Supabase: {e}")
        return None

def test_connection():
    print(f"Probando conexion con Supabase URL: {SUPABASE_URL or 'No configurada'}...")
    client = get_client()
    if not client:
        print("Estado: NO CONECTADO (Faltan credenciales)")
        return False
    try:
        res = client.table("users").select("id").limit(1).execute()
        print("Estado: CONECTADO EXITOSAMENTE a Supabase!")
        print(f"Respuesta tabla users: {res.data}")
        return True
    except Exception as e:
        print(f"Conexión alcanzada, pero la tabla users devolvió: {e}")
        print("Asegúrate de haber ejecutado database/schema.sql en el SQL Editor de Supabase.")
        return False

if __name__ == "__main__":
    test_connection()

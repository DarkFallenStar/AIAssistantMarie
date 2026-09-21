import asyncio
import os
import sys
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import get_supabase_client, DEFAULT_USER_ID

USER_DATA = {
    "id": DEFAULT_USER_ID,
    "email": "usuario@ejemplo.com",
    "full_name": "Usuario Demo MVP",
    "phone_number": "+573001234567",
    "preferences": {"language": "es", "currency": "COP", "notifications": True}
}

TASKS_DATA = [
    {
        "id": "b0000000-0000-0000-0000-000000000001",
        "user_id": DEFAULT_USER_ID,
        "title": "Revisar presupuesto mensual",
        "description": "Analizar los gastos de la semana con el Asistente Financiero",
        "status": "pending",
        "priority": "high",
        "category": "finanzas"
    },
    {
        "id": "b0000000-0000-0000-0000-000000000002",
        "user_id": DEFAULT_USER_ID,
        "title": "Entregar informe de avance de tesis",
        "description": "Enviar borrador del capítulo metodológico al director de tesis",
        "status": "pending",
        "priority": "high",
        "category": "academico"
    },
    {
        "id": "b0000000-0000-0000-0000-000000000003",
        "user_id": DEFAULT_USER_ID,
        "title": "Comprar víveres y café para la semana",
        "description": "Pasar al supermercado al salir del trabajo",
        "status": "pending",
        "priority": "medium",
        "category": "hogar"
    }
]

EMAILS_DATA = [
    {
        "id": "c0000000-0000-0000-0000-000000000001",
        "user_id": DEFAULT_USER_ID,
        "sender": "director@universidad.edu",
        "recipient": "usuario@ejemplo.com",
        "subject": "Revisión de Avance de Tesis",
        "snippet": "Estimado estudiante, por favor confirma la entrega del capítulo 3 para este viernes.",
        "status": "unread",
        "category": "work",
        "is_important": True
    },
    {
        "id": "c0000000-0000-0000-0000-000000000002",
        "user_id": DEFAULT_USER_ID,
        "sender": "alertas@bancolombia.com",
        "recipient": "usuario@ejemplo.com",
        "subject": "Notificación de Transferencia Recibida",
        "snippet": "Has recibido una transferencia por $1.500.000 COP en tu cuenta de ahorros.",
        "status": "unread",
        "category": "finance",
        "is_important": True
    },
    {
        "id": "c0000000-0000-0000-0000-000000000003",
        "user_id": DEFAULT_USER_ID,
        "sender": "soporte@empresa.com",
        "recipient": "usuario@ejemplo.com",
        "subject": "Confirmación de Reunión de Planeación",
        "snippet": "La sesión técnica de planeación del sprint ha sido programada para el lunes a las 10:00 a.m.",
        "status": "read",
        "category": "work",
        "is_important": False
    }
]

ACCOUNT_DATA = {
    "id": "d0000000-0000-0000-0000-000000000001",
    "user_id": DEFAULT_USER_ID,
    "account_name": "Cuenta de Ahorros Principal",
    "account_type": "savings",
    "institution": "Bancolombia",
    "account_number_mask": "**** 1234",
    "balance": 3500000.00,
    "currency": "COP"
}

TRANSACTIONS_DATA = [
    # 1. Alimentación
    {
        "id": "10000000-0000-0000-0000-000000000001",
        "user_id": DEFAULT_USER_ID,
        "account_id": ACCOUNT_DATA["id"],
        "type": "expense",
        "amount": 85000.00,
        "currency": "COP",
        "category": "alimentacion",
        "description": "Compra de despensa semanal en supermercado",
        "merchant": "Supermercado Éxito",
        "source": "manual"
    },
    {
        "id": "10000000-0000-0000-0000-000000000002",
        "user_id": DEFAULT_USER_ID,
        "account_id": ACCOUNT_DATA["id"],
        "type": "expense",
        "amount": 32000.00,
        "currency": "COP",
        "category": "alimentacion",
        "description": "Almuerzo ejecutivo en restaurante",
        "merchant": "Restaurante Central",
        "source": "manual"
    },
    # 2. Transporte
    {
        "id": "10000000-0000-0000-0000-000000000003",
        "user_id": DEFAULT_USER_ID,
        "account_id": ACCOUNT_DATA["id"],
        "type": "expense",
        "amount": 45000.00,
        "currency": "COP",
        "category": "transporte",
        "description": "Tanqueo de gasolina en estación de servicio",
        "merchant": "Estación Terpel",
        "source": "manual"
    },
    {
        "id": "10000000-0000-0000-0000-000000000004",
        "user_id": DEFAULT_USER_ID,
        "account_id": ACCOUNT_DATA["id"],
        "type": "expense",
        "amount": 18500.00,
        "currency": "COP",
        "category": "transporte",
        "description": "Viaje en taxi hacia la oficina",
        "merchant": "Taxi Urbano",
        "source": "manual"
    },
    # 3. Educación
    {
        "id": "10000000-0000-0000-0000-000000000005",
        "user_id": DEFAULT_USER_ID,
        "account_id": ACCOUNT_DATA["id"],
        "type": "expense",
        "amount": 120000.00,
        "currency": "COP",
        "category": "educacion",
        "description": "Pago de curso online y certificación técnica",
        "merchant": "Plataforma Educativa",
        "source": "manual"
    },
    {
        "id": "10000000-0000-0000-0000-000000000006",
        "user_id": DEFAULT_USER_ID,
        "account_id": ACCOUNT_DATA["id"],
        "type": "expense",
        "amount": 45000.00,
        "currency": "COP",
        "category": "educacion",
        "description": "Compra de libros y materiales de estudio",
        "merchant": "Librería Nacional",
        "source": "manual"
    },
    # 4. Ocio
    {
        "id": "10000000-0000-0000-0000-000000000007",
        "user_id": DEFAULT_USER_ID,
        "account_id": ACCOUNT_DATA["id"],
        "type": "expense",
        "amount": 55000.00,
        "currency": "COP",
        "category": "ocio",
        "description": "Entradas de cine y combo de alimentos",
        "merchant": "Cine Colombia",
        "source": "manual"
    },
    {
        "id": "10000000-0000-0000-0000-000000000008",
        "user_id": DEFAULT_USER_ID,
        "account_id": ACCOUNT_DATA["id"],
        "type": "expense",
        "amount": 28000.00,
        "currency": "COP",
        "category": "ocio",
        "description": "Suscripción mensual de entretenimiento",
        "merchant": "Streaming Plus",
        "source": "manual"
    },
    # 5. Servicios
    {
        "id": "10000000-0000-0000-0000-000000000009",
        "user_id": DEFAULT_USER_ID,
        "account_id": ACCOUNT_DATA["id"],
        "type": "expense",
        "amount": 95000.00,
        "currency": "COP",
        "category": "servicios",
        "description": "Factura de servicio de energía eléctrica",
        "merchant": "Empresa de Energía",
        "source": "manual"
    },
    {
        "id": "10000000-0000-0000-0000-000000000010",
        "user_id": DEFAULT_USER_ID,
        "account_id": ACCOUNT_DATA["id"],
        "type": "expense",
        "amount": 75000.00,
        "currency": "COP",
        "category": "servicios",
        "description": "Pago de plan de internet de fibra óptica",
        "merchant": "Claro Hogar",
        "source": "manual"
    },
    # Ingreso nómina
    {
        "id": "10000000-0000-0000-0000-000000000011",
        "user_id": DEFAULT_USER_ID,
        "account_id": ACCOUNT_DATA["id"],
        "type": "income",
        "amount": 2500000.00,
        "currency": "COP",
        "category": "ingreso",
        "description": "Transferencia Recibida (Nómina quincenal)",
        "merchant": "Empresa Empleadora",
        "source": "manual"
    }
]

def seed():
    client = get_supabase_client()
    if not client:
        print("[SEED] Supabase not connected. Skipping remote seeding.")
        return

    print("[SEED] Seeding user...")
    client.table("users").upsert(USER_DATA).execute()

    print("[SEED] Seeding financial account...")
    client.table("financial_accounts").upsert(ACCOUNT_DATA).execute()

    print("[SEED] Seeding tasks (3)...")
    for t in TASKS_DATA:
        client.table("tasks").upsert(t).execute()

    print("[SEED] Seeding emails (3)...")
    for e in EMAILS_DATA:
        client.table("emails").upsert(e).execute()

    print("[SEED] Seeding transactions (10+ COP across 5 categories)...")
    for tx in TRANSACTIONS_DATA:
        client.table("transactions").upsert(tx).execute()

    print("[SEED] All MVP seed data synchronized successfully in Supabase.")

if __name__ == "__main__":
    seed()

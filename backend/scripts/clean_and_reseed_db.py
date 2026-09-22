import sys
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import get_supabase_client, DEFAULT_USER_ID

MINIMAL_USER = {
    "id": DEFAULT_USER_ID,
    "email": "usuario@ejemplo.com",
    "full_name": "Usuario Demo",
    "phone_number": "+573001234567",
    "preferences": {"language": "es", "currency": "COP", "notifications": True}
}

MINIMAL_ACCOUNT = {
    "id": "d0000000-0000-0000-0000-000000000001",
    "user_id": DEFAULT_USER_ID,
    "account_name": "Cuenta de Ahorros Principal",
    "account_type": "savings",
    "institution": "Bancolombia",
    "account_number_mask": "**** 1234",
    "balance": 3500000.00,
    "currency": "COP",
    "status": "active"
}

MINIMAL_CARD = {
    "id": "e0000000-0000-0000-0000-000000000001",
    "user_id": DEFAULT_USER_ID,
    "card_name": "Tarjeta de Crédito Visa",
    "institution": "Bancolombia",
    "card_number_mask": "**** 4321",
    "credit_limit": 5000000.00,
    "current_balance": 0.00,
    "currency": "COP",
    "cutoff_day": 15,
    "due_day": 30,
    "status": "active"
}

MINIMAL_GOAL = {
    "id": "f0000000-0000-0000-0000-000000000001",
    "user_id": DEFAULT_USER_ID,
    "goal_name": "Fondo de Emergencia",
    "target_amount": 2000000.00,
    "current_amount": 500000.00,
    "currency": "COP",
    "deadline": "2026-12-31",
    "status": "in_progress"
}

MINIMAL_TASKS = [
    {
        "id": "b0000000-0000-0000-0000-000000000001",
        "user_id": DEFAULT_USER_ID,
        "title": "Revisar informe de presupuesto mensual",
        "description": "Verificar los gastos consolidados con el Asistente Financiero",
        "status": "pending",
        "priority": "high",
        "category": "finanzas"
    },
    {
        "id": "b0000000-0000-0000-0000-000000000002",
        "user_id": DEFAULT_USER_ID,
        "title": "Configurar asistente personal",
        "description": "Ajustar preferencias de notificaciones y conexión remota",
        "status": "completed",
        "priority": "medium",
        "category": "tecnologia"
    }
]

MINIMAL_EMAILS = [
    {
        "id": "c0000000-0000-0000-0000-000000000001",
        "user_id": DEFAULT_USER_ID,
        "sender": "director@universidad.edu",
        "recipient": "usuario@ejemplo.com",
        "subject": "Revisión técnica de avance",
        "snippet": "Estimado estudiante, por favor confirma la entrega del avance metodológico.",
        "status": "unread",
        "category": "work",
        "is_important": True
    },
    {
        "id": "c0000000-0000-0000-0000-000000000002",
        "user_id": DEFAULT_USER_ID,
        "sender": "marie@asistente.ai",
        "recipient": "usuario@ejemplo.com",
        "subject": "Bienvenido a tu Asistente Marie",
        "snippet": "Tu asistente inteligente está listo para organizar tus tareas y finanzas personales.",
        "status": "read",
        "category": "general",
        "is_important": False
    }
]

MINIMAL_TRANSACTIONS = [
    {
        "id": "10000000-0000-0000-0000-000000000001",
        "user_id": DEFAULT_USER_ID,
        "account_id": MINIMAL_ACCOUNT["id"],
        "type": "income",
        "amount": 2500000.00,
        "currency": "COP",
        "category": "ingreso",
        "description": "Transferencia Recibida (Nómina quincenal)",
        "merchant": "Empresa Empleadora",
        "source": "manual"
    },
    {
        "id": "10000000-0000-0000-0000-000000000002",
        "user_id": DEFAULT_USER_ID,
        "account_id": MINIMAL_ACCOUNT["id"],
        "type": "expense",
        "amount": 85000.00,
        "currency": "COP",
        "category": "alimentacion",
        "description": "Compra de despensa semanal en supermercado",
        "merchant": "Supermercado Éxito",
        "source": "manual"
    },
    {
        "id": "10000000-0000-0000-0000-000000000003",
        "user_id": DEFAULT_USER_ID,
        "account_id": MINIMAL_ACCOUNT["id"],
        "type": "expense",
        "amount": 20000.00,
        "currency": "COP",
        "category": "transporte",
        "description": "Recarga de transporte público",
        "merchant": "Sistema Integrado Transporte",
        "source": "manual"
    }
]

import argparse

def clean_and_reseed(empty_only: bool = False):
    client = get_supabase_client()
    if not client:
        print("[CLEAN-DB] Error: No Supabase client configured.")
        return

    print(f"[CLEAN-DB] Iniciando purga de tablas en orden relacional (empty_only={empty_only})...")

    # 1. Purgar tablas dependientes
    tables_to_purge = [
        "transactions",
        "saving_goals",
        "loans",
        "credit_cards",
        "financial_accounts",
        "emails",
        "tasks"
    ]

    for table in tables_to_purge:
        try:
            # Borrar todos los registros donde id != nil UUID
            res = client.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            count = len(res.data) if res.data else 0
            print(f"  -> Tabla '{table}' purgada ({count} registros eliminados).")
        except Exception as e:
            print(f"  [WARN] Error purgando '{table}': {e}")

    # Sembrar y asegurar Usuario Principal
    client.table("users").upsert(MINIMAL_USER).execute()
    # Eliminar usuarios secundarios o residuales de tests
    try:
        client.table("users").delete().neq("id", DEFAULT_USER_ID).execute()
    except Exception as e:
        print(f"  [WARN] Error limpiando usuarios secundarios: {e}")
    print("  + Usuario principal verificado y sembrado (DEFAULT_USER_ID).")

    if empty_only:
        print("\n[CLEAN-DB] Modo vaciado total activo: No se insertarán registros adicionales.")
    else:
        print("\n[CLEAN-DB] Sembrando conjunto mínimo y limpio de datos...")

        # Sembrar Cuenta Financiera
        client.table("financial_accounts").upsert(MINIMAL_ACCOUNT).execute()
        print("  + 1 Cuenta bancaria principal sembrada.")

        # Sembrar Tarjeta de Crédito
        client.table("credit_cards").upsert(MINIMAL_CARD).execute()
        print("  + 1 Tarjeta de crédito sembrada.")

        # Sembrar Meta de Ahorro
        client.table("saving_goals").upsert(MINIMAL_GOAL).execute()
        print("  + 1 Meta de ahorro sembrada.")

        # Sembrar Tareas (2)
        for t in MINIMAL_TASKS:
            client.table("tasks").upsert(t).execute()
        print("  + 2 Tareas limpias sembradas.")

        # Sembrar Correos (2)
        for e in MINIMAL_EMAILS:
            client.table("emails").upsert(e).execute()
        print("  + 2 Correos limpios sembrados.")

        # Sembrar Transacciones (3)
        for tx in MINIMAL_TRANSACTIONS:
            client.table("transactions").upsert(tx).execute()
        print("  + 3 Transacciones COP limpias sembradas.")

    print("\n[CLEAN-DB] Verificación de conteo final en Supabase:")
    for table in ["users", "tasks", "emails", "financial_accounts", "credit_cards", "saving_goals", "transactions"]:
        cnt = client.table(table).select("id", count="exact").execute().count
        print(f"  - {table}: {cnt} registros.")

    mode_label = "vaciada completamente (0 datos)" if empty_only else "re-sembrada con datos mínimos"
    print(f"\n[CLEAN-DB] ¡Base de datos {mode_label} con éxito!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Limpieza y gestión de base de datos Supabase")
    parser.add_argument("--empty", "--purge-all", action="store_true", dest="empty", help="Deja la base de datos completamente vacía (0 registros, solo usuario base)")
    args = parser.parse_args()
    clean_and_reseed(empty_only=args.empty)

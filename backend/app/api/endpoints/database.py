import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from app.core.database import (
    check_database_connection,
    get_supabase_client,
    is_valid_uuid,
    DEFAULT_USER_ID,
    REQUIRED_SCHEMA_TABLES
)
from app.core.security import verify_api_bearer_token
from app.tools.task_tool import TaskTools
from app.tools.reminder_tool import ReminderTools
from app.tools.transaction_tool import TransactionTools
from app.services.email.mock_client import MockEmailClient

router = APIRouter()

ALLOWED_TABLES = [
    "tasks",
    "reminders",
    "transactions",
    "financial_accounts",
    "credit_cards",
    "loans",
    "saving_goals",
    "emails"
]

def _resolve_table_name(table_name: str) -> str:
    """Maps virtual table names like 'reminders' to actual Supabase tables."""
    clean = table_name.lower().strip()
    if clean == "reminders":
        return "tasks"
    return clean

@router.get("/db/status", summary="Estado de Conexión a Base de Datos (Supabase)")
async def database_status(_authorized: bool = Depends(verify_api_bearer_token)):
    """
    Verifica y reporta el estado de conectividad con Supabase / PostgreSQL.
    """
    return await check_database_connection()

@router.get("/db/summary", summary="Resumen de Conteos por Tabla")
async def database_summary(_authorized: bool = Depends(verify_api_bearer_token)):
    """
    Retorna el total de registros por cada tabla soportada en la base de datos.
    """
    client = get_supabase_client()
    summary: Dict[str, int] = {}
    
    if client:
        try:
            for table in REQUIRED_SCHEMA_TABLES:
                if table == "users":
                    continue
                try:
                    res = client.table(table).select("id", count="exact").execute()
                    summary[table] = res.count if res.count is not None else len(res.data or [])
                except Exception as ex:
                    print(f"[DB] Error counting {table}: {ex}")
                    summary[table] = 0

            # Contar recordatorios separadamente
            try:
                rem_res = client.table("tasks").select("id", count="exact").eq("category", "reminder").execute()
                summary["reminders"] = rem_res.count if rem_res.count is not None else len(rem_res.data or [])
                # Ajustar tasks para no duplicar si se desea
                task_only = client.table("tasks").select("id", count="exact").neq("category", "reminder").execute()
                summary["tasks_only"] = task_only.count if task_only.count is not None else len(task_only.data or [])
            except Exception:
                summary["reminders"] = 0

            return {
                "status": "connected",
                "counts": summary,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            print(f"[DB] Error querying Supabase summary: {e}")

    # Fallback en memoria si Supabase no está disponible
    task_tool = TaskTools()
    rem_tool = ReminderTools()
    tx_tool = TransactionTools()
    email_client = MockEmailClient()

    summary = {
        "tasks": len(task_tool._tasks),
        "reminders": len(rem_tool._reminders),
        "transactions": len(tx_tool._shared_transactions),
        "financial_accounts": 3,
        "credit_cards": 2,
        "loans": 1,
        "saving_goals": 2,
        "emails": len(email_client.list_all())
    }

    return {
        "status": "in_memory_fallback",
        "counts": summary,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/db/table/{table_name}", summary="Listar Registros de una Tabla")
async def list_table_records(
    table_name: str,
    category: Optional[str] = Query(None, description="Filtro opcional por categoría"),
    status: Optional[str] = Query(None, description="Filtro opcional por estado"),
    limit: int = Query(100, ge=1, le=500),
    _authorized: bool = Depends(verify_api_bearer_token)
):
    """
    Retorna la lista de registros para una tabla específica con orden cronológico descendente.
    """
    clean_name = table_name.lower().strip()
    if clean_name not in ALLOWED_TABLES:
        raise HTTPException(status_code=400, detail=f"Tabla '{table_name}' no soportada. Permitidas: {ALLOWED_TABLES}")

    actual_table = _resolve_table_name(clean_name)
    client = get_supabase_client()

    if client:
        try:
            query = client.table(actual_table).select("*")
            
            # Filtro para la vista virtual 'reminders'
            if clean_name == "reminders":
                query = query.eq("category", "reminder")
            elif clean_name == "tasks" and category is None:
                # Si consultan tasks sin categoría específica, podemos excluir reminders para que cada tab sea único
                pass

            if category:
                query = query.eq("category", category)
            if status:
                query = query.eq("status", status)

            # Ordenamiento apropiado por tabla
            if actual_table == "transactions":
                query = query.order("transaction_date", desc=True)
            elif actual_table == "emails":
                query = query.order("received_at", desc=True)
            elif "created_at" in ["tasks", "financial_accounts", "credit_cards", "loans", "saving_goals"]:
                query = query.order("created_at", desc=True)

            res = query.limit(limit).execute()
            records = res.data or []

            return {
                "status": "success",
                "table": clean_name,
                "count": len(records),
                "data": records
            }
        except Exception as e:
            print(f"[DB] Error querying Supabase table {actual_table}: {e}")

    # Fallback en memoria si Supabase no está conectado
    records: List[Dict[str, Any]] = []
    if clean_name == "tasks":
        records = [t for t in TaskTools()._tasks if t.get("category") != "reminder"]
    elif clean_name == "reminders":
        records = ReminderTools()._reminders
    elif clean_name == "transactions":
        records = TransactionTools()._shared_transactions
    elif clean_name == "emails":
        records = [e.to_dict() for e in MockEmailClient().list_all()]
    elif clean_name == "financial_accounts":
        records = [
            {"id": "fa-001", "account_name": "Cuenta de Ahorros Principal", "account_type": "savings", "institution": "Bancolombia", "balance": 3500000.0, "currency": "COP", "status": "active"},
            {"id": "fa-002", "account_name": "Billetera Digital Nequi", "account_type": "digital_wallet", "institution": "Nequi", "balance": 450000.0, "currency": "COP", "status": "active"},
            {"id": "fa-003", "account_name": "Fondo de Emergencia", "account_type": "savings", "institution": "Davivienda", "balance": 2000000.0, "currency": "COP", "status": "active"}
        ]
    elif clean_name == "credit_cards":
        records = [
            {"id": "cc-001", "card_name": "Visa Oro", "institution": "Bancolombia", "card_number_mask": "**** 4321", "credit_limit": 5000000.0, "current_balance": 1250000.0, "available_credit": 3750000.0, "currency": "COP", "cutoff_day": 15, "due_day": 5, "status": "active"},
            {"id": "cc-002", "card_name": "Mastercard Black", "institution": "Davivienda", "card_number_mask": "**** 9876", "credit_limit": 8000000.0, "current_balance": 450000.0, "available_credit": 7550000.0, "currency": "COP", "cutoff_day": 20, "due_day": 10, "status": "active"}
        ]
    elif clean_name == "loans":
        records = [
            {"id": "ln-001", "lender_name": "Banco de Bogotá", "loan_type": "personal", "original_amount": 10000000.0, "remaining_balance": 6200000.0, "interest_rate_annual": 18.5, "monthly_payment": 350000.0, "payment_day": 16, "start_date": "2024-01-15", "status": "active"}
        ]
    elif clean_name == "saving_goals":
        records = [
            {"id": "sg-001", "goal_name": "Fondo de Vacaciones", "target_amount": 5000000.0, "current_amount": 3200000.0, "currency": "COP", "deadline": "2026-12-20", "status": "in_progress"},
            {"id": "sg-002", "goal_name": "Nuevo Computador Portátil", "target_amount": 4000000.0, "current_amount": 1800000.0, "currency": "COP", "deadline": "2026-10-30", "status": "in_progress"}
        ]

    return {
        "status": "in_memory_fallback",
        "table": clean_name,
        "count": len(records),
        "data": records
    }

@router.post("/db/table/{table_name}", summary="Crear Registro Manualmente")
async def create_table_record(
    table_name: str,
    payload: Dict[str, Any] = Body(..., description="Campos del nuevo registro"),
    _authorized: bool = Depends(verify_api_bearer_token)
):
    """
    Crea un nuevo registro en la tabla especificada con validación de tipos e inserción directa en base de datos.
    """
    clean_name = table_name.lower().strip()
    if clean_name not in ALLOWED_TABLES:
        raise HTTPException(status_code=400, detail=f"Tabla '{table_name}' no permitida. Permitidas: {ALLOWED_TABLES}")

    actual_table = _resolve_table_name(clean_name)
    client = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()

    record: Dict[str, Any] = dict(payload)

    # Asegurar UUID válido
    if "id" not in record or not is_valid_uuid(record["id"]):
        record["id"] = str(uuid.uuid4())

    # Asignar usuario por defecto si no viene
    if "user_id" not in record:
        record["user_id"] = DEFAULT_USER_ID

    # Defaults específicos por tipo de dato
    if clean_name == "reminders":
        record["category"] = "reminder"
        if "status" not in record:
            record["status"] = "pending"
        if "priority" not in record:
            record["priority"] = "medium"
    elif actual_table == "tasks":
        if "status" not in record:
            record["status"] = "pending"
        if "priority" not in record:
            record["priority"] = "medium"
        if "category" not in record:
            record["category"] = "general"
    elif actual_table == "transactions":
        if "currency" not in record:
            record["currency"] = "COP"
        if "type" not in record:
            record["type"] = "expense"
        if "status" not in record:
            record["status"] = "posted"
        if "source" not in record:
            record["source"] = "manual"
        if "transaction_date" not in record:
            record["transaction_date"] = now_iso
    elif actual_table in ["financial_accounts", "credit_cards", "saving_goals"]:
        if "currency" not in record:
            record["currency"] = "COP"

    record["created_at"] = now_iso
    record["updated_at"] = now_iso

    if client:
        try:
            res = client.table(actual_table).insert(record).execute()
            inserted = res.data[0] if res.data else record
            print(f"[DB] Inserted into {actual_table}: {inserted.get('id')}")

            # Sincronizar cache en memoria si aplica
            if actual_table == "tasks":
                TaskTools()._tasks.append(inserted)
            elif actual_table == "transactions":
                TransactionTools()._shared_transactions.append(inserted)

            return {
                "status": "created",
                "table": clean_name,
                "data": inserted
            }
        except Exception as e:
            print(f"[DB] Error inserting into {actual_table}: {e}")
            raise HTTPException(status_code=500, detail=f"Error al insertar en {actual_table}: {str(e)}")

    # Fallback en memoria
    if clean_name == "reminders":
        ReminderTools()._reminders.append(record)
    elif actual_table == "tasks":
        TaskTools()._tasks.append(record)
    elif actual_table == "transactions":
        TransactionTools()._shared_transactions.append(record)

    return {
        "status": "created_in_memory",
        "table": clean_name,
        "data": record
    }

@router.patch("/db/table/{table_name}/{record_id}", summary="Actualizar Registro Manualmente")
async def update_table_record(
    table_name: str,
    record_id: str,
    updates: Dict[str, Any] = Body(..., description="Campos a actualizar"),
    _authorized: bool = Depends(verify_api_bearer_token)
):
    """
    Actualiza campos específicos de un registro existente por su ID.
    """
    clean_name = table_name.lower().strip()
    if clean_name not in ALLOWED_TABLES:
        raise HTTPException(status_code=400, detail=f"Tabla '{table_name}' no permitida.")

    actual_table = _resolve_table_name(clean_name)
    client = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()

    clean_updates = {k: v for k, v in updates.items() if k not in ["id", "user_id"]}
    clean_updates["updated_at"] = now_iso

    # Si se completa una tarea, registrar completed_at
    if actual_table == "tasks" and clean_updates.get("status") == "completed":
        clean_updates["completed_at"] = now_iso

    if client and is_valid_uuid(record_id):
        try:
            res = client.table(actual_table).update(clean_updates).eq("id", record_id).execute()
            if res.data:
                updated = res.data[0]
                print(f"[DB] Updated in {actual_table}: {record_id}")
                return {
                    "status": "updated",
                    "table": clean_name,
                    "id": record_id,
                    "data": updated
                }
        except Exception as e:
            print(f"[DB] Error updating {actual_table} id={record_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error actualizando en {actual_table}: {str(e)}")

    # Fallback en memoria
    return {
        "status": "updated_fallback",
        "table": clean_name,
        "id": record_id,
        "data": clean_updates
    }

@router.delete("/db/table/{table_name}/{record_id}", summary="Eliminar Registro Manualmente")
async def delete_table_record(
    table_name: str,
    record_id: str,
    _authorized: bool = Depends(verify_api_bearer_token)
):
    """
    Elimina un registro de la base de datos por su ID.
    """
    clean_name = table_name.lower().strip()
    if clean_name not in ALLOWED_TABLES:
        raise HTTPException(status_code=400, detail=f"Tabla '{table_name}' no permitida.")

    actual_table = _resolve_table_name(clean_name)
    client = get_supabase_client()

    deleted = False
    if client and is_valid_uuid(record_id):
        try:
            res = client.table(actual_table).delete().eq("id", record_id).execute()
            print(f"[DB] Deleted from {actual_table}: {record_id}")
            deleted = True
        except Exception as e:
            print(f"[DB] Error deleting from {actual_table} id={record_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error eliminando de {actual_table}: {str(e)}")

    # Limpiar de cache en memoria
    if actual_table == "tasks":
        TaskTools()._tasks = [t for t in TaskTools()._tasks if str(t.get("id")) != str(record_id)]
    elif actual_table == "transactions":
        TransactionTools()._shared_transactions = [t for t in TransactionTools()._shared_transactions if str(t.get("id")) != str(record_id)]

    return {
        "status": "deleted",
        "table": clean_name,
        "id": record_id,
        "success": True
    }

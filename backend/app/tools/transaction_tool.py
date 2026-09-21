import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from app.tools.base import BaseTool, ToolResult
from app.core.database import get_supabase_client, is_valid_uuid, DEFAULT_USER_ID

class TransactionTools(BaseTool):
    """
    Independent tool for querying, creating, and categorizing financial transactions.
    Interacts with Supabase 'transactions' table with an in-memory fallback.
    """

    MOCK_TRANSACTIONS: List[Dict[str, Any]] = [
        # Alimentación
        {
            "id": "10000000-0000-0000-0000-000000000001",
            "account_id": "d0000000-0000-0000-0000-000000000001",
            "credit_card_id": None,
            "type": "expense",
            "amount": 85000.00,
            "currency": "COP",
            "category": "alimentacion",
            "description": "Compra de despensa semanal en supermercado",
            "merchant": "Supermercado Éxito",
            "transaction_date": "2026-09-21T10:00:00Z",
            "status": "posted",
            "source": "manual"
        },
        {
            "id": "10000000-0000-0000-0000-000000000002",
            "account_id": "d0000000-0000-0000-0000-000000000001",
            "credit_card_id": None,
            "type": "expense",
            "amount": 32000.00,
            "currency": "COP",
            "category": "alimentacion",
            "description": "Almuerzo ejecutivo en restaurante",
            "merchant": "Restaurante Central",
            "transaction_date": "2026-09-20T13:30:00Z",
            "status": "posted",
            "source": "manual"
        },
        # Transporte
        {
            "id": "10000000-0000-0000-0000-000000000003",
            "account_id": "d0000000-0000-0000-0000-000000000001",
            "credit_card_id": None,
            "type": "expense",
            "amount": 45000.00,
            "currency": "COP",
            "category": "transporte",
            "description": "Tanqueo de gasolina en estación de servicio",
            "merchant": "Estación Terpel",
            "transaction_date": "2026-09-19T17:30:00Z",
            "status": "posted",
            "source": "manual"
        },
        {
            "id": "10000000-0000-0000-0000-000000000004",
            "account_id": "d0000000-0000-0000-0000-000000000001",
            "credit_card_id": None,
            "type": "expense",
            "amount": 18500.00,
            "currency": "COP",
            "category": "transporte",
            "description": "Viaje en taxi hacia la oficina",
            "merchant": "Taxi Urbano",
            "transaction_date": "2026-09-19T08:15:00Z",
            "status": "posted",
            "source": "manual"
        },
        # Educación
        {
            "id": "10000000-0000-0000-0000-000000000005",
            "account_id": "d0000000-0000-0000-0000-000000000001",
            "credit_card_id": None,
            "type": "expense",
            "amount": 120000.00,
            "currency": "COP",
            "category": "educacion",
            "description": "Pago de curso online y certificación técnica",
            "merchant": "Plataforma Educativa",
            "transaction_date": "2026-09-18T11:00:00Z",
            "status": "posted",
            "source": "manual"
        },
        {
            "id": "10000000-0000-0000-0000-000000000006",
            "account_id": "d0000000-0000-0000-0000-000000000001",
            "credit_card_id": None,
            "type": "expense",
            "amount": 45000.00,
            "currency": "COP",
            "category": "educacion",
            "description": "Compra de libros y materiales de estudio",
            "merchant": "Librería Nacional",
            "transaction_date": "2026-09-17T16:20:00Z",
            "status": "posted",
            "source": "manual"
        },
        # Ocio
        {
            "id": "10000000-0000-0000-0000-000000000007",
            "account_id": "d0000000-0000-0000-0000-000000000001",
            "credit_card_id": None,
            "type": "expense",
            "amount": 55000.00,
            "currency": "COP",
            "category": "ocio",
            "description": "Entradas de cine y combo de alimentos",
            "merchant": "Cine Colombia",
            "transaction_date": "2026-09-16T20:00:00Z",
            "status": "posted",
            "source": "manual"
        },
        {
            "id": "10000000-0000-0000-0000-000000000008",
            "account_id": "d0000000-0000-0000-0000-000000000001",
            "credit_card_id": None,
            "type": "expense",
            "amount": 28000.00,
            "currency": "COP",
            "category": "ocio",
            "description": "Suscripción mensual de entretenimiento",
            "merchant": "Streaming Plus",
            "transaction_date": "2026-09-16T10:00:00Z",
            "status": "posted",
            "source": "manual"
        },
        # Servicios
        {
            "id": "10000000-0000-0000-0000-000000000009",
            "account_id": "d0000000-0000-0000-0000-000000000001",
            "credit_card_id": None,
            "type": "expense",
            "amount": 95000.00,
            "currency": "COP",
            "category": "servicios",
            "description": "Factura de servicio de energía eléctrica",
            "merchant": "Empresa de Energía",
            "transaction_date": "2026-09-15T14:00:00Z",
            "status": "posted",
            "source": "manual"
        },
        {
            "id": "10000000-0000-0000-0000-000000000010",
            "account_id": "d0000000-0000-0000-0000-000000000001",
            "credit_card_id": None,
            "type": "expense",
            "amount": 75000.00,
            "currency": "COP",
            "category": "servicios",
            "description": "Pago de plan de internet de fibra óptica",
            "merchant": "Claro Hogar",
            "transaction_date": "2026-09-15T15:00:00Z",
            "status": "posted",
            "source": "manual"
        },
        # Ingreso
        {
            "id": "10000000-0000-0000-0000-000000000011",
            "account_id": "d0000000-0000-0000-0000-000000000001",
            "credit_card_id": None,
            "type": "income",
            "amount": 2500000.00,
            "currency": "COP",
            "category": "ingreso",
            "description": "Transferencia Recibida (Nómina quincenal)",
            "merchant": "Empresa Empleadora",
            "transaction_date": "2026-09-15T09:00:00Z",
            "status": "posted",
            "source": "manual"
        }
    ]

    _shared_transactions: Optional[List[Dict[str, Any]]] = None

    def __init__(self):
        if TransactionTools._shared_transactions is None:
            TransactionTools._shared_transactions = [dict(tx) for tx in self.MOCK_TRANSACTIONS]
        self._transactions = TransactionTools._shared_transactions

    @classmethod
    def reset_mock_data(cls):
        cls._shared_transactions = [dict(tx) for tx in cls.MOCK_TRANSACTIONS]

    @property
    def name(self) -> str:
        return "transaction_tool"

    @property
    def description(self) -> str:
        return "Consulta el historial de transacciones bancarias, registra nuevos ingresos/gastos y categoriza movimientos."

    async def get_transactions(
        self,
        limit: int = 10,
        category: Optional[str] = None,
        type: Optional[str] = None,
        source: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Retrieves recent transactions, optionally filtered by category, type (income, expense), or source.
        """
        transactions: List[Dict[str, Any]] = []
        client = get_supabase_client()
        if client:
            try:
                query = client.table("transactions").select("*").limit(limit).order("transaction_date", desc=True)
                if user_id:
                    query = query.eq("user_id", user_id)
                if category:
                    query = query.ilike("category", f"%{category.strip()}%")
                if type:
                    query = query.eq("type", type.strip().lower())
                if source:
                    query = query.eq("source", source.strip().lower())
                res = query.execute()
                if res and res.data:
                    transactions.extend(res.data)
            except Exception as exc:
                print(f"[TOOL] Supabase get_transactions failed ({exc}), using mock fallback")

        # Strict persistence priority:
        # If database records are present, database is the Single Source of Truth.
        default_mock_ids = {t.get("id") for t in self.MOCK_TRANSACTIONS}
        seen_ids = set()
        combined: List[Dict[str, Any]] = []

        if transactions:
            # 1. Any newly created session transaction that isn't a static mock and isn't yet in DB query
            for t in self._transactions:
                t_id = t.get("id")
                if t_id and t_id not in default_mock_ids and t_id not in seen_ids:
                    seen_ids.add(t_id)
                    matches_cat = not category or category.lower() in t.get("category", "").lower()
                    matches_type = not type or t.get("type", "").lower() == type.lower()
                    matches_source = not source or t.get("source", "").lower() == source.lower()
                    if matches_cat and matches_type and matches_source:
                        combined.append(t)

            # 2. Add database records
            for t in transactions:
                t_id = t.get("id")
                if t_id and t_id not in seen_ids:
                    seen_ids.add(t_id)
                    combined.append(t)
        else:
            # Fallback when database is unreachable or offline
            for t in self._transactions:
                t_id = t.get("id")
                if t_id and t_id not in seen_ids:
                    seen_ids.add(t_id)
                    matches_cat = not category or category.lower() in t.get("category", "").lower()
                    matches_type = not type or t.get("type", "").lower() == type.lower()
                    matches_source = not source or t.get("source", "").lower() == source.lower()
                    if matches_cat and matches_type and matches_source:
                        combined.append(t)

        filtered = combined[:limit]
        return ToolResult(
            success=True,
            data={"count": len(filtered), "transactions": filtered},
            message=f"Se obtuvieron {len(filtered)} transacciones financieras."
        )

    async def create_transaction(
        self,
        amount: float,
        type: str = "expense",
        category: str = "general",
        description: str = "",
        merchant: Optional[str] = None,
        account_id: Optional[str] = None,
        credit_card_id: Optional[str] = None,
        user_id: Optional[str] = None,
        currency: str = "COP",
        source: str = "voice_agent",
        transaction_date: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Records a new financial transaction (income or expense) in the database.
        """
        clean_amount = abs(float(amount))
        tx_id = str(uuid.uuid4())
        eff_user_id = user_id or DEFAULT_USER_ID
        tx_date = transaction_date or datetime.now(timezone.utc).isoformat()

        payload = {
            "id": tx_id,
            "user_id": eff_user_id,
            "account_id": account_id,
            "credit_card_id": credit_card_id,
            "type": type.lower() if type in ["income", "expense", "transfer"] else "expense",
            "amount": clean_amount,
            "currency": (currency or "COP").upper(),
            "category": (category or "general").strip().lower(),
            "description": description or f"Movimiento {type}",
            "merchant": merchant or description or "Comercio",
            "transaction_date": tx_date,
            "status": "posted",
            "source": source if source in ["manual", "webhook_bank", "voice_agent", "email_import"] else "webhook_bank",
            "metadata": metadata or {}
        }

        # Keep in-memory copy updated
        self._transactions.insert(0, payload)

        client = get_supabase_client()
        if client:
            try:
                client.table("transactions").insert(payload).execute()
            except Exception as exc:
                print(f"[TOOL] Supabase create_transaction failed ({exc}), stored in mock storage")

        formatted_amount = f"${clean_amount:,.0f}" if payload['currency'] == "COP" else f"${clean_amount:.2f}"
        return ToolResult(
            success=True,
            data=payload,
            message=f"Transacción de {formatted_amount} {payload['currency']} ({payload['type']}) en '{payload['category']}' registrada correctamente."
        )

    async def categorize_transaction(
        self,
        transaction_id: str,
        category: str,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Updates the category of an existing transaction.
        """
        clean_cat = (category or "").strip().lower()
        if not clean_cat:
            return ToolResult(
                success=False,
                data=None,
                message="Debe especificar una categoría válida."
            )

        client = get_supabase_client()
        if client and is_valid_uuid(transaction_id):
            try:
                query = client.table("transactions").update({"category": clean_cat}).eq("id", transaction_id)
                if user_id:
                    query = query.eq("user_id", user_id)
                res = query.execute()
                if res and res.data:
                    return ToolResult(
                        success=True,
                        data=res.data[0],
                        message=f"Transacción '{transaction_id}' categorizada como '{clean_cat}' exitosamente."
                    )
            except Exception as exc:
                print(f"[TOOL] Supabase categorize_transaction failed ({exc}), updating in mock")

        # In-memory fallback
        for tx in self._transactions:
            if tx.get("id") == transaction_id:
                tx["category"] = clean_cat
                return ToolResult(
                    success=True,
                    data=tx,
                    message=f"Transacción '{tx.get('description')}' categorizada como '{clean_cat}' correctamente."
                )

        return ToolResult(
            success=False,
            data=None,
            message=f"No se encontró ninguna transacción con el ID '{transaction_id}'."
        )

    async def delete_transaction(
        self,
        transaction_id: str,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Deletes a transaction from Supabase and in-memory fallback.
        """
        client = get_supabase_client()
        if client and is_valid_uuid(transaction_id):
            try:
                query = client.table("transactions").delete().eq("id", transaction_id)
                if user_id:
                    query = query.eq("user_id", user_id)
                query.execute()
                self._transactions = [t for t in self._transactions if t.get("id") != transaction_id]
                TransactionTools._shared_transactions = self._transactions
                return ToolResult(
                    success=True,
                    data={"deleted_id": transaction_id},
                    message=f"Transacción '{transaction_id}' eliminada exitosamente de la base de datos."
                )
            except Exception as exc:
                print(f"[TOOL] Supabase delete_transaction failed ({exc}), deleting from mock")

        # In-memory fallback
        initial_len = len(self._transactions)
        self._transactions = [t for t in self._transactions if t.get("id") != transaction_id]
        TransactionTools._shared_transactions = self._transactions
        if len(self._transactions) < initial_len:
            return ToolResult(
                success=True,
                data={"deleted_id": transaction_id},
                message=f"Transacción '{transaction_id}' eliminada correctamente."
            )
        return ToolResult(
            success=False,
            data=None,
            message=f"No se encontró ninguna transacción con el ID '{transaction_id}'."
        )

    async def execute(
        self,
        action: str = "list",
        limit: int = 5,
        category: Optional[str] = None,
        type: Optional[str] = None,
        amount: Optional[float] = None,
        description: Optional[str] = None,
        merchant: Optional[str] = None,
        transaction_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        Generic dispatch method adhering to BaseTool interface.
        """
        print(f"[TOOL] Executing transaction_tool (action='{action}', category='{category}', amount={amount})")

        if action in ["create", "add", "record"]:
            amt = amount or kwargs.get("monto", 0.0)
            return await self.create_transaction(
                amount=amt,
                type=type or kwargs.get("tipo", "expense"),
                category=category or kwargs.get("categoria", "general"),
                description=description or kwargs.get("descripcion", ""),
                merchant=merchant,
                currency=kwargs.get("currency", "COP"),
                user_id=user_id
            )

        if action in ["categorize", "update_category"]:
            tx_id = transaction_id or kwargs.get("id")
            cat = category or kwargs.get("nueva_categoria", "general")
            if not tx_id:
                return ToolResult(success=False, data=None, message="Se requiere el ID de la transacción para categorizarla.")
            return await self.categorize_transaction(transaction_id=tx_id, category=cat, user_id=user_id)

        if action in ["delete", "remove", "eliminar", "borrar"]:
            tx_id = transaction_id or kwargs.get("id")
            if not tx_id:
                return ToolResult(success=False, data=None, message="Se requiere el ID de la transacción para eliminarla.")
            return await self.delete_transaction(transaction_id=tx_id, user_id=user_id)

        # Default is list/get
        return await self.get_transactions(limit=limit, category=category, type=type, user_id=user_id)


# Backward compatibility alias
TransactionTool = TransactionTools

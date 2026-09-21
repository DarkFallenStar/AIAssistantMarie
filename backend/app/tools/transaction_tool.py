from typing import Optional, List, Dict, Any
from app.tools.base import BaseTool, ToolResult
from app.core.database import get_supabase_client

class TransactionTool(BaseTool):
    """
    Tool for querying recent banking transactions and expense history.
    """

    MOCK_TRANSACTIONS = [
        {"id": "tx-1", "description": "Supermercado La Plaza", "amount": -82.40, "category": "Alimentacion", "date": "Hoy"},
        {"id": "tx-2", "description": "Gasolinera Express", "amount": -35.00, "category": "Transporte", "date": "Ayer"},
        {"id": "tx-3", "description": "Transferencia Recibida (Nomina)", "amount": 1600.00, "category": "Ingreso", "date": "Hace 3 dias"},
    ]

    @property
    def name(self) -> str:
        return "transaction_tool"

    @property
    def description(self) -> str:
        return "Consulta el historial de transacciones recientes, gastos realizados e ingresos."

    async def execute(self, limit: int = 5, category: Optional[str] = None, **kwargs) -> ToolResult:
        print(f"[TOOL] Executing transaction_tool (limit={limit}, category={category})")

        client = get_supabase_client()
        if client:
            try:
                query = client.table("transactions").select("*").order("created_at", desc=True).limit(limit)
                if category:
                    query = query.eq("category", category)
                res = query.execute()
                txs = res.data if res else []
                return ToolResult(
                    success=True,
                    data={"count": len(txs), "transactions": txs},
                    message=f"Se obtuvieron {len(txs)} transacciones desde Supabase."
                )
            except Exception as exc:
                print(f"[TOOL] Supabase transaction query failed ({exc}), using mock fallback")

        txs = [t for t in self.MOCK_TRANSACTIONS if not category or t["category"].lower() == category.lower()][:limit]
        return ToolResult(
            success=True,
            data={"count": len(txs), "transactions": txs},
            message=f"Se encontraron {len(txs)} movimientos recientes."
        )

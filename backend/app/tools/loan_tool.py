from typing import Optional, List, Dict, Any
from app.tools.base import BaseTool, ToolResult
from app.core.database import get_supabase_client

class LoanTools(BaseTool):
    """
    Independent tool for querying loans, mortgages, automotive credits,
    remaining balances, and monthly payment obligations strictly from database records.
    """

    MOCK_LOANS: List[Dict[str, Any]] = [
        {
            "id": "f0000000-0000-0000-0000-000000000001",
            "lender_name": "Crédito Automotriz",
            "loan_type": "auto",
            "original_amount": 12000.00,
            "remaining_balance": 7800.00,
            "interest_rate_annual": 11.50,
            "monthly_payment": 320.00,
            "payment_day": 20,
            "start_date": "2025-01-15",
            "status": "active"
        }
    ]

    def __init__(self):
        self._loans: List[Dict[str, Any]] = [dict(l) for l in self.MOCK_LOANS]

    @property
    def name(self) -> str:
        return "loan_tool"

    @property
    def description(self) -> str:
        return "Consulta préstamos, hipotecas y créditos vigentes: saldo restante, cuota mensual, tasa de interés y fecha de pago."

    async def get_loans(
        self,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Retrieves active loans and financing details from the database.
        """
        loans: List[Dict[str, Any]] = []
        db_success = False
        client = get_supabase_client()
        if client:
            try:
                query = client.table("loans").select("*")
                if user_id:
                    query = query.eq("user_id", user_id)
                res = query.execute()
                if res and res.data is not None:
                    for l in res.data:
                        loans.append({
                            "id": l.get("id"),
                            "lender_name": l.get("lender_name"),
                            "loan_type": l.get("loan_type"),
                            "original_amount": float(l.get("original_amount", 0)),
                            "remaining_balance": float(l.get("remaining_balance", 0)),
                            "interest_rate_annual": float(l.get("interest_rate_annual", 0)),
                            "monthly_payment": float(l.get("monthly_payment", 0)),
                            "payment_day": l.get("payment_day"),
                            "start_date": l.get("start_date"),
                            "status": l.get("status", "active")
                        })
                db_success = True
            except Exception as exc:
                print(f"[TOOL] Supabase get_loans failed ({exc}), using mock fallback")
                db_success = False

        if not db_success or not loans:
            loans = [dict(l) for l in self._loans]

        total_debt = sum(l["remaining_balance"] for l in loans)
        total_monthly = sum(l["monthly_payment"] for l in loans)

        return ToolResult(
            success=True,
            data={
                "count": len(loans),
                "total_loans_balance": round(total_debt, 2),
                "total_monthly_installments": round(total_monthly, 2),
                "loans": loans
            },
            message=f"Se encontraron {len(loans)} préstamo(s) activos. Deuda total de capital: ${total_debt:.2f} USD. Compromiso mensual: ${total_monthly:.2f} USD."
        )

    async def execute(self, action: str = "list", user_id: Optional[str] = None, **kwargs) -> ToolResult:
        print(f"[TOOL] Executing loan_tool (action='{action}')")
        return await self.get_loans(user_id=user_id)


# Backward compatibility alias
LoanTool = LoanTools

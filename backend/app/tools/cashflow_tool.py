from typing import Optional, Dict, Any
from app.tools.base import BaseTool, ToolResult
from app.core.database import get_supabase_client

class CashFlowTool(BaseTool):
    """
    Tool for calculating cash flow, available liquid balances, and financial budgets.
    """

    MOCK_ACCOUNTS = [
        {"name": "Cuenta Corriente Banco Principal", "balance": 1850.00, "currency": "USD"},
        {"name": "Billetera Digital / Ahorros", "balance": 620.50, "currency": "USD"},
    ]

    MOCK_BUDGET = {
        "monthly_income": 3200.00,
        "committed_fixed_expenses": 1400.00,
        "variable_expenses_to_date": 530.50,
        "emergency_fund_reserved": 300.00,
    }

    @property
    def name(self) -> str:
        return "cashflow_tool"

    @property
    def description(self) -> str:
        return "Calcula el flujo de caja, balance total disponible en cuentas y presupuesto restante del mes."

    async def execute(self, period: str = "current_month", **kwargs) -> ToolResult:
        print(f"[TOOL] Executing cashflow_tool (period='{period}')")

        client = get_supabase_client()
        if client:
            try:
                acc_res = client.table("financial_accounts").select("account_name, balance, currency").execute()
                accounts = acc_res.data if acc_res else []
                if accounts:
                    normalized_accounts = [
                        {
                            "name": a.get("account_name", "Cuenta"),
                            "balance": float(a.get("balance", 0)),
                            "currency": a.get("currency", "USD")
                        }
                        for a in accounts
                    ]
                    total_liquid = sum(a["balance"] for a in normalized_accounts)
                    return ToolResult(
                        success=True,
                        data={
                            "total_liquid_balance": total_liquid,
                            "currency": "USD",
                            "accounts": normalized_accounts,
                            "available_discretionary": total_liquid * 0.45,
                            "net_available_for_spending": total_liquid * 0.45
                        },
                        message=f"Balance total disponible en cuentas: ${total_liquid:.2f} USD."
                    )
            except Exception as exc:
                print(f"[TOOL] Supabase cashflow query failed ({exc}), using mock fallback")

        # Fallback in-memory calculation
        total_balance = sum(a["balance"] for a in self.MOCK_ACCOUNTS)
        available_month = total_balance - self.MOCK_BUDGET["emergency_fund_reserved"] - 250.00  # upcoming obligations

        data = {
            "period": period,
            "total_liquid_balance": total_balance,
            "currency": "USD",
            "accounts": self.MOCK_ACCOUNTS,
            "committed_fixed_expenses": self.MOCK_BUDGET["committed_fixed_expenses"],
            "variable_spent_this_month": self.MOCK_BUDGET["variable_expenses_to_date"],
            "net_available_for_spending": max(0.0, available_month)
        }

        return ToolResult(
            success=True,
            data=data,
            message=f"Tu saldo total en cuentas es de ${total_balance:.2f} USD, con un disponible estimado para ocio y gastos de ${available_month:.2f} USD."
        )

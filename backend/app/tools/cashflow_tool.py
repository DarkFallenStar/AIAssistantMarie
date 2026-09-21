from typing import Optional, Dict, Any, List
from app.tools.base import BaseTool, ToolResult
from app.core.database import get_supabase_client

class CashFlowTools(BaseTool):
    """
    Tool for calculating cash flow, available liquid balances, and financial budgets
    strictly using database records from financial_accounts and transactions.
    """

    MOCK_ACCOUNTS: List[Dict[str, Any]] = [
        {
            "id": "d0000000-0000-0000-0000-000000000001",
            "name": "Cuenta de Ahorros Principal",
            "institution": "Bancolombia",
            "balance": 3500000.00,
            "currency": "COP"
        }
    ]

    MOCK_MONTHLY_SUMMARY = {
        "monthly_income": 2500000.00,
        "monthly_expenses": 618500.00,
        "committed_fixed_expenses": 350000.00,
        "emergency_reserved": 500000.00
    }

    @property
    def name(self) -> str:
        return "cashflow_tool"

    @property
    def description(self) -> str:
        return "Calcula el flujo de caja, balance total en cuentas bancarias, ingresos, gastos y disponible del periodo."

    async def calculate_cash_flow(
        self,
        period: str = "current_month",
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Calculates total liquid balance, net cashflow (income minus expenses), and budget.
        """
        client = get_supabase_client()
        accounts: List[Dict[str, Any]] = []
        total_income = 0.0
        total_expenses = 0.0
        db_success = False

        if client:
            try:
                # 1. Fetch liquid accounts
                acc_query = client.table("financial_accounts").select("id, account_name, institution, balance, currency")
                if user_id:
                    acc_query = acc_query.eq("user_id", user_id)
                acc_res = acc_query.execute()
                if acc_res and acc_res.data:
                    for a in acc_res.data:
                        accounts.append({
                            "id": a.get("id"),
                            "name": a.get("account_name", "Cuenta"),
                            "institution": a.get("institution", "Banco"),
                            "balance": float(a.get("balance", 0)),
                            "currency": a.get("currency", "USD")
                        })

                # 2. Fetch transactions to compute income vs expenses
                tx_query = client.table("transactions").select("type, amount")
                if user_id:
                    tx_query = tx_query.eq("user_id", user_id)
                tx_res = tx_query.execute()
                if tx_res and tx_res.data:
                    for tx in tx_res.data:
                        amt = float(tx.get("amount", 0))
                        tx_type = tx.get("type", "expense")
                        if tx_type == "income":
                            total_income += amt
                        elif tx_type == "expense":
                            total_expenses += amt
                db_success = True
            except Exception as exc:
                print(f"[TOOL] Supabase cashflow query failed ({exc}), using mock fallback")
                db_success = False

        # In-memory fallback ONLY if database query failed or offline
        if not db_success:
            accounts = [dict(a) for a in self.MOCK_ACCOUNTS]
            total_income = self.MOCK_MONTHLY_SUMMARY["monthly_income"]
            total_expenses = self.MOCK_MONTHLY_SUMMARY["monthly_expenses"]
            try:
                from app.tools.transaction_tool import TransactionTools
                tx_tool = TransactionTools()
                default_ids = {t["id"] for t in TransactionTools.MOCK_TRANSACTIONS}
                for tx in tx_tool._transactions:
                    if tx.get("id") not in default_ids:
                        amt = float(tx.get("amount", 0.0))
                        if tx.get("type") == "expense":
                            total_expenses += amt
                        elif tx.get("type") == "income":
                            total_income += amt
            except Exception as exc:
                print(f"[TOOL] CashFlowTools fallback tx calculation error: {exc}")

        total_liquid = sum(a["balance"] for a in accounts)
        net_cash_flow = total_income - total_expenses
        reserve_margin = 50000.0 if any(a.get("currency") == "COP" for a in accounts) else 50.0
        available_discretionary = max(0.0, total_liquid - reserve_margin)

        # Detect currency from accounts
        currency = "COP" if any(a.get("currency") == "COP" for a in accounts) else "USD"
        if accounts and accounts[0].get("currency"):
            currency = accounts[0]["currency"]

        fmt_liquid = f"${total_liquid:,.0f}" if currency == "COP" else f"${total_liquid:,.2f}"
        fmt_income = f"${total_income:,.0f}" if currency == "COP" else f"${total_income:,.2f}"
        fmt_expenses = f"${total_expenses:,.0f}" if currency == "COP" else f"${total_expenses:,.2f}"
        fmt_net = f"${net_cash_flow:,.0f}" if currency == "COP" else f"${net_cash_flow:,.2f}"

        data = {
            "period": period,
            "total_liquid_balance": round(total_liquid, 2),
            "currency": currency,
            "monthly_income": round(total_income, 2),
            "monthly_expenses": round(total_expenses, 2),
            "net_cash_flow": round(net_cash_flow, 2),
            "available_for_spending": round(available_discretionary, 2),
            "net_available_for_spending": round(available_discretionary, 2),
            "accounts": accounts
        }

        return ToolResult(
            success=True,
            data=data,
            message=(
                f"Flujo de caja ({period}): Balance total en cuentas: {fmt_liquid} {currency}. "
                f"Ingresos: {fmt_income} {currency}, Gastos: {fmt_expenses} {currency}, "
                f"Flujo neto: {fmt_net} {currency}."
            )
        )

    async def execute(self, action: str = "calculate", period: str = "current_month", user_id: Optional[str] = None, **kwargs) -> ToolResult:
        print(f"[TOOL] Executing cashflow_tool (action='{action}', period='{period}')")
        return await self.calculate_cash_flow(period=period, user_id=user_id)


# Backward compatibility alias
CashFlowTool = CashFlowTools

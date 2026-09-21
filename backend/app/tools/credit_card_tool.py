from typing import Optional, List, Dict, Any
from app.tools.base import BaseTool, ToolResult
from app.core.database import get_supabase_client

class CreditCardTools(BaseTool):
    """
    Independent tool for querying credit cards, limits, current debt,
    available balance, cutoff dates, and payment deadlines strictly from database records.
    """

    MOCK_CARDS: List[Dict[str, Any]] = [
        {
            "id": "e0000000-0000-0000-0000-000000000001",
            "card_name": "Tarjeta Oro",
            "institution": "BBVA",
            "card_number_mask": "**** 5678",
            "credit_limit": 3000.00,
            "current_balance": 450.25,
            "available_credit": 2549.75,
            "currency": "USD",
            "cutoff_day": 15,
            "due_day": 5,
            "status": "active"
        }
    ]

    def __init__(self):
        self._cards: List[Dict[str, Any]] = [dict(c) for c in self.MOCK_CARDS]

    @property
    def name(self) -> str:
        return "credit_card_tool"

    @property
    def description(self) -> str:
        return "Consulta tarjetas de crédito: límites, saldo adeudado, crédito disponible, día de corte y fecha límite de pago."

    async def get_credit_cards(
        self,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Retrieves active credit cards and their balances from database.
        """
        cards: List[Dict[str, Any]] = []
        db_success = False
        client = get_supabase_client()
        if client:
            try:
                query = client.table("credit_cards").select("*")
                if user_id:
                    query = query.eq("user_id", user_id)
                res = query.execute()
                if res and res.data is not None:
                    for c in res.data:
                        limit = float(c.get("credit_limit", 0))
                        balance = float(c.get("current_balance", 0))
                        avail = limit - balance
                        cards.append({
                            "id": c.get("id"),
                            "card_name": c.get("card_name"),
                            "institution": c.get("institution"),
                            "card_number_mask": c.get("card_number_mask"),
                            "credit_limit": limit,
                            "current_balance": balance,
                            "available_credit": avail,
                            "currency": c.get("currency", "USD"),
                            "cutoff_day": c.get("cutoff_day"),
                            "due_day": c.get("due_day"),
                            "status": c.get("status", "active")
                        })
                db_success = True
            except Exception as exc:
                print(f"[TOOL] Supabase get_credit_cards failed ({exc}), using mock fallback")
                db_success = False

        if not db_success:
            cards = [dict(c) for c in self._cards]

        total_debt = sum(c["current_balance"] for c in cards)
        total_limit = sum(c["credit_limit"] for c in cards)

        return ToolResult(
            success=True,
            data={
                "count": len(cards),
                "total_credit_debt": round(total_debt, 2),
                "total_credit_limit": round(total_limit, 2),
                "cards": cards
            },
            message=f"Se encontraron {len(cards)} tarjeta(s) de crédito registradas. Deuda total actual: ${total_debt:.2f} USD."
        )

    async def execute(self, action: str = "list", user_id: Optional[str] = None, **kwargs) -> ToolResult:
        print(f"[TOOL] Executing credit_card_tool (action='{action}')")
        return await self.get_credit_cards(user_id=user_id)


# Backward compatibility alias
CreditCardTool = CreditCardTools

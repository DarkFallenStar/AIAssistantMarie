from typing import Dict, Any, Optional
from app.tools.base import BaseTool, ToolResult
from app.tools.email_tool import EmailTools
from app.tools.task_tool import TaskTools
from app.tools.reminder_tool import ReminderTools
from app.tools.cashflow_tool import CashFlowTools
from app.tools.transaction_tool import TransactionTools
from app.tools.credit_card_tool import CreditCardTools
from app.tools.loan_tool import LoanTools
from app.tools.saving_goal_tool import SavingGoalTools

class ToolDispatcher:
    """
    Central dispatcher for executing tools requested via Function Calling / Structured Output.
    Maps canonical tool function names directly to underlying tool instances.
    """

    def __init__(self):
        # Instantiate tools
        self.email_tool = EmailTools()
        self.task_tool = TaskTools()
        self.reminder_tool = ReminderTools()
        self.cashflow_tool = CashFlowTools()
        self.transaction_tool = TransactionTools()
        self.credit_card_tool = CreditCardTools()
        self.loan_tool = LoanTools()
        self.saving_goal_tool = SavingGoalTools()

    async def dispatch(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """
        Dispatches tool invocation by canonical tool name or underlying tool name with action.
        """
        normalized = tool_name.strip().lower()
        args = dict(arguments)

        # -----------------------------------------------------------------
        # 1. Financial Tools Dispatching
        # -----------------------------------------------------------------
        if normalized in ["calculate_cash_flow", "get_cash_flow", "calculate_cashflow", "get_balance", "cash_flow"]:
            period = args.get("period", "current_month")
            return await self.cashflow_tool.execute(action="calculate", period=period)

        elif normalized in ["list_transactions", "get_transactions", "recent_transactions"]:
            return await self.transaction_tool.execute(
                action="list",
                account_id=args.get("account_id"),
                category=args.get("category"),
                limit=int(args.get("limit", 5))
            )

        elif normalized in ["create_transaction", "record_expense", "add_transaction", "record_income"]:
            amount = float(args.get("amount", 0.0))
            tx_type = args.get("type", "expense")
            category = args.get("category", "general")
            description = args.get("description", f"Registro de {category}")
            merchant = args.get("merchant", category.capitalize())
            return await self.transaction_tool.execute(
                action="create",
                account_id=args.get("account_id"),
                amount=amount,
                type=tx_type,
                category=category,
                description=description,
                merchant=merchant
            )

        elif normalized in ["categorize_transaction", "update_transaction_category"]:
            return await self.transaction_tool.execute(
                action="categorize",
                transaction_id=args.get("transaction_id"),
                category=args.get("category", "general")
            )

        elif normalized in ["list_credit_cards", "get_credit_cards"]:
            return await self.credit_card_tool.execute(action="list")

        elif normalized in ["get_credit_card"]:
            return await self.credit_card_tool.execute(action="get", card_id=args.get("card_id"))

        elif normalized in ["list_loans", "get_loans"]:
            return await self.loan_tool.execute(action="list")

        elif normalized in ["get_loan"]:
            return await self.loan_tool.execute(action="get", loan_id=args.get("loan_id"))

        elif normalized in ["list_saving_goals", "get_saving_goals"]:
            return await self.saving_goal_tool.execute(action="list")

        elif normalized in ["get_saving_goal"]:
            return await self.saving_goal_tool.execute(action="get", goal_id=args.get("goal_id"))

        elif normalized in ["update_saving_goal", "contribute_saving_goal"]:
            goal_id = args.get("goal_id", "00000000-0000-0000-0000-000000000001")
            amt = float(args.get("current_amount", args.get("amount", 0.0)))
            return await self.saving_goal_tool.execute(
                action="update",
                goal_id=goal_id,
                current_amount=amt
            )

        # -----------------------------------------------------------------
        # 2. Secretary Tools Dispatching
        # -----------------------------------------------------------------
        elif normalized in ["list_tasks", "get_tasks"]:
            return await self.task_tool.execute(
                action="list",
                status=args.get("status"),
                limit=int(args.get("limit", 5))
            )

        elif normalized in ["create_task", "add_task"]:
            return await self.task_tool.execute(
                action="create",
                title=args.get("title", "Nueva tarea"),
                due_date=args.get("due_date"),
                priority=args.get("priority", "medium")
            )

        elif normalized in ["complete_task"]:
            return await self.task_tool.execute(
                action="complete",
                task_id=args.get("task_id")
            )

        elif normalized in ["list_reminders", "get_reminders"]:
            return await self.reminder_tool.execute(
                action="list",
                timeframe=args.get("timeframe", "all"),
                limit=int(args.get("limit", 5))
            )

        elif normalized in ["create_reminder", "set_reminder", "add_reminder"]:
            return await self.reminder_tool.execute(
                action="create",
                title=args.get("title", "Recordatorio"),
                remind_at=args.get("remind_at", "pronto"),
                channel=args.get("channel", "app")
            )

        elif normalized in ["acknowledge_reminder"]:
            return await self.reminder_tool.execute(
                action="acknowledge",
                reminder_id=args.get("reminder_id")
            )

        elif normalized in ["list_emails", "get_emails"]:
            return await self.email_tool.execute(
                action="list",
                status=args.get("status"),
                limit=int(args.get("limit", 5))
            )

        elif normalized in ["list_unread_emails", "unread_emails", "correos_no_leidos"]:
            return await self.email_tool.execute(
                action="unread",
                limit=int(args.get("limit", 5))
            )

        elif normalized in ["get_email"]:
            return await self.email_tool.execute(
                action="get",
                email_id=args.get("email_id")
            )

        elif normalized in ["search_emails"]:
            return await self.email_tool.execute(
                action="search",
                search=args.get("search", "")
            )

        elif normalized in ["summarize_email", "summarize_emails", "resumir_correo"]:
            return await self.email_tool.execute(
                action="summarize",
                email_id=args.get("email_id"),
                search=args.get("query") or args.get("search")
            )

        elif normalized in ["prioritize_emails", "priorizar_correos"]:
            return await self.email_tool.execute(
                action="prioritize",
                limit=int(args.get("limit", 5))
            )

        elif normalized in ["draft_email", "create_draft_email"]:
            return await self.email_tool.execute(
                action="draft",
                recipient=args.get("recipient", "contacto@empresa.com"),
                subject=args.get("subject", "Sin asunto"),
                body=args.get("body", "")
            )

        elif normalized in ["send_email", "enviar_correo"]:
            return await self.email_tool.execute(
                action="send",
                recipient=args.get("recipient", "contacto@empresa.com"),
                subject=args.get("subject", "Sin asunto"),
                body=args.get("body", ""),
                confirmed=bool(args.get("confirmed", False))
            )

        # -----------------------------------------------------------------
        # 3. Generic Tool Fallback (Direct class lookup if registered)
        # -----------------------------------------------------------------
        raw_tools: Dict[str, BaseTool] = {
            "cashflow_tool": self.cashflow_tool,
            "transaction_tool": self.transaction_tool,
            "credit_card_tool": self.credit_card_tool,
            "loan_tool": self.loan_tool,
            "saving_goal_tool": self.saving_goal_tool,
            "task_tool": self.task_tool,
            "reminder_tool": self.reminder_tool,
            "email_tool": self.email_tool,
        }

        if normalized in raw_tools:
            return await raw_tools[normalized].execute(**args)

        return ToolResult(
            success=False,
            data=None,
            message=f"Herramienta desconocida '{tool_name}' solicitada por Function Calling."
        )

_dispatcher_instance: Optional[ToolDispatcher] = None

def get_tool_dispatcher() -> ToolDispatcher:
    global _dispatcher_instance
    if _dispatcher_instance is None:
        _dispatcher_instance = ToolDispatcher()
    return _dispatcher_instance

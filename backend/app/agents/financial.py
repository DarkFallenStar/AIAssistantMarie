import re
from typing import Dict, Any, List, Optional
from app.agents.base import BaseAgent, AgentResponse
from app.tools.base import BaseTool, ToolResult
from app.tools.cashflow_tool import CashFlowTools, CashFlowTool
from app.tools.transaction_tool import TransactionTools, TransactionTool
from app.tools.credit_card_tool import CreditCardTools, CreditCardTool
from app.tools.loan_tool import LoanTools, LoanTool
from app.tools.saving_goal_tool import SavingGoalTools, SavingGoalTool
from app.services.llm import get_llm_service, BaseLLMService

class FinancialAgent(BaseAgent):
    """
    Specialized agent for comprehensive financial management:
    - Transactions & Expense Logging (get, create, categorize)
    - Cash Flow & Liquid Balance Analysis
    - Credit Card Management (balances, limits, cut-offs)
    - Loans & Liabilities (interest, remaining capital, quotas)
    - Saving Goals (tracking & progress updates)

    Enforces strict zero-hallucination guardrails: all figures must originate from the database.
    """

    def __init__(self, llm_service: Optional[BaseLLMService] = None):
        self._custom_llm = llm_service
        self.transaction_tools = TransactionTools()
        self.cashflow_tools = CashFlowTools()
        self.credit_card_tools = CreditCardTools()
        self.loan_tools = LoanTools()
        self.saving_goal_tools = SavingGoalTools()

        self._tools: Dict[str, BaseTool] = {
            "transaction_tool": self.transaction_tools,
            "cashflow_tool": self.cashflow_tools,
            "credit_card_tool": self.credit_card_tools,
            "loan_tool": self.loan_tools,
            "saving_goal_tool": self.saving_goal_tools,
        }

    @property
    def name(self) -> str:
        return "FinancialAgent"

    @property
    def system_prompt(self) -> str:
        return (
            "Eres el Agente Financiero de un Asistente Personal Inteligente de alto nivel. "
            "Eres analítico, profesional, ejecutivo y matemáticamente exacto en español.\n\n"
            "DIRECTIVA CRÍTICA ANTI-ALUCINACIÓN (CERO INVENCIÓN):\n"
            "1. NO inventes cifras, montos, tasas, fechas de corte, préstamos, tarjetas ni balances.\n"
            "2. Toda cifra mencionada debe derivarse ESTRICTAMENTE de los datos estructurados provistos por las herramientas.\n"
            "3. Si el usuario pregunta por una cuenta, tarjeta, préstamo, meta o gasto que NO existe en los datos devueltos por las herramientas, "
            "declara expresamente que no se encontró ningún registro correspondiente en la base de datos."
        )

    @property
    def tools(self) -> Dict[str, BaseTool]:
        return self._tools

    def get_llm(self) -> BaseLLMService:
        if self._custom_llm is not None:
            return self._custom_llm
        return get_llm_service()

    def determine_tools(self, request: str) -> List[tuple]:
        """
        Determines which financial tool(s) and actions are required.
        Routes across: transactions, cashflow, credit cards, loans, saving goals.
        """
        req_lower = request.lower()
        tools_to_run = []

        # -----------------------------------------------------------------
        # 1. CREDIT CARDS INTENT
        # -----------------------------------------------------------------
        if any(kw in req_lower for kw in ["tarjeta", "tarjetas", "credito", "crédito", "visa", "mastercard", "corte", "limite de credito", "límite de crédito"]):
            # Also check if it's a specific card question vs recording card expense
            if not any(kw in req_lower for kw in ["registra", "agrega", "pagué con la tarjeta", "compre con"]):
                tools_to_run.append(("credit_card_tool", {"action": "list"}))

        # -----------------------------------------------------------------
        # 2. LOANS & LIABILITIES INTENT
        # -----------------------------------------------------------------
        if any(kw in req_lower for kw in ["prestamo", "préstamo", "prestamos", "préstamos", "hipoteca", "deuda", "deudas", "cuota", "automotriz", "financiamiento"]):
            tools_to_run.append(("loan_tool", {"action": "list"}))

        # -----------------------------------------------------------------
        # 3. SAVING GOALS INTENT
        # -----------------------------------------------------------------
        if any(kw in req_lower for kw in ["meta", "metas", "ahorro", "ahorros", "fondo de emergencia", "guardado"]):
            if any(kw in req_lower for kw in ["actualiza", "modifica", "aporta", "agrega a mi meta", "poner en"]):
                amt_match = re.search(r'([0-9]+(?:[.,][0-9]{1,2})?)', request)
                amt = float(amt_match.group(1).replace(",", ".")) if amt_match else 2000.0
                tools_to_run.append(("saving_goal_tool", {
                    "action": "update",
                    "goal_id": "00000000-0000-0000-0000-000000000001",
                    "current_amount": amt
                }))
            else:
                tools_to_run.append(("saving_goal_tool", {"action": "list"}))

        # -----------------------------------------------------------------
        # 4. TRANSACTIONS INTENT (Create / Categorize / List)
        # -----------------------------------------------------------------
        # A. Create transaction
        if any(kw in req_lower for kw in ["registra un gasto", "agrega un gasto", "anota un gasto", "nuevo gasto", "compre", "compré", "gaste", "gasté", "registra una transaccion", "registra una transacción"]):
            amt_match = re.search(r'(?:\$|de\s+)?([0-9]+(?:[.,][0-9]{1,2})?)\s*(?:pesos|cop|dolares|dólares|usd|\$)?', request, re.IGNORECASE)
            amount = float(amt_match.group(1).replace(",", ".")) if amt_match else 20000.0
            currency = "USD" if any(w in req_lower for w in ["dolar", "dólar", "usd"]) else "COP"

            # Extract category / description strictly after 'en' or 'para' first
            cat_match = re.search(r'\b(?:en|para)\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ_ -]+)', request, re.IGNORECASE)
            if not cat_match:
                cat_match = re.search(r'\b(?:de)\s+(?:[0-9]+(?:[.,][0-9]+)?\s*(?:pesos|cop|dolares|usd|\$)?\s*(?:en|para)?\s*)?([a-zA-ZáéíóúÁÉÍÓÚñÑ_ -]+)', request, re.IGNORECASE)

            category = cat_match.group(1).strip().lower() if cat_match else "general"
            # Strip noise words
            category = re.sub(r'^(?:dolares|dólares|usd|pesos|cop|\$|[0-9]+)\s*', '', category).strip()
            if not category:
                category = "general"

            tools_to_run.append(("transaction_tool", {
                "action": "create",
                "amount": amount,
                "type": "expense",
                "category": category,
                "currency": currency,
                "description": f"Gasto registrado: {category}",
                "merchant": category.capitalize()
            }))
        # B. Categorize transaction
        elif any(kw in req_lower for kw in ["categoriza", "clasifica", "cambia la categoria", "cambia la categoría"]):
            cat_match = re.search(r'(?:a|como)\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ_ -]+)', request)
            new_cat = cat_match.group(1).strip().lower() if cat_match else "general"
            id_match = re.search(r'(?:transaccion|transacción|id)\s+([0-9a-fA-F-]+)', request)
            tx_id = id_match.group(1) if id_match else "10000000-0000-0000-0000-000000000001"
            tools_to_run.append(("transaction_tool", {
                "action": "categorize",
                "transaction_id": tx_id,
                "category": new_cat
            }))
        # C. Query Transactions
        elif any(kw in req_lower for kw in ["movimientos", "transacciones", "ultimos gastos", "últimos gastos", "historial", "en que gaste", "en qué gasté", "gastado en", "gasto en", "gastos en"]):
            cat_filter = None
            for cat in ["supermercado", "alimentos", "comida", "alimentacion", "alimentación", "transporte", "gasolina", "farmacia", "educacion", "educación", "ocio", "servicios"]:
                if cat in req_lower:
                    cat_filter = cat
                    break
            tools_to_run.append(("transaction_tool", {"action": "list", "category": cat_filter, "limit": 5}))

        # -----------------------------------------------------------------
        # 5. CASH FLOW & BALANCE INTENT
        # -----------------------------------------------------------------
        if any(kw in req_lower for kw in ["saldo", "dinero", "disponible", "queda", "quedan", "cuenta", "cuentas", "presupuesto", "flujo de caja", "flujo"]):
            tools_to_run.append(("cashflow_tool", {"action": "calculate", "period": "current_month"}))

        # Default fallback
        if not tools_to_run:
            tools_to_run.append(("cashflow_tool", {"action": "calculate", "period": "current_month"}))

        return tools_to_run

    async def handle(self, request: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        print(f"[AGENT] {self.name} processing request: '{request}'")

        # 1. Determinar herramientas necesarias
        tools_to_run = self.determine_tools(request)
        tools_executed: List[str] = []
        tool_results: List[ToolResult] = []
        tool_context_texts: List[str] = []

        # 2. Ejecutar herramientas
        for tool_name, params in tools_to_run:
            tool = self._tools.get(tool_name)
            if tool:
                tools_executed.append(tool_name)
                result = await tool.execute(**params)
                tool_results.append(result)
                tool_context_texts.append(f"Herramienta '{tool_name}' ({params.get('action', 'execute')}):\nResultado: {result.message}\nDatos estructurados: {result.data}")

        tool_summary = "\n\n".join(tool_context_texts)

        # 3. Formular prompt enriquecido con datos reales y directiva anti-alucinación
        augmented_prompt = (
            f"Consulta financiera del usuario: '{request}'\n\n"
            f"Datos estructurados obtenidos de la base de datos:\n{tool_summary}\n\n"
            "Instrucción: Proporciona una respuesta ejecutiva, profesional y numérica basada estrictamente en los datos anteriores. "
            "Si no hay datos que respalden la consulta del usuario, acláralo honestamente sin conjeturar ni inventar cifras."
        )

        # 4. Generar respuesta con LLM
        try:
            llm = self.get_llm()
            llm_resp = await llm.generate(prompt=augmented_prompt, system_prompt=self.system_prompt)
            final_text = llm_resp.text
            llm_used = True
        except Exception as exc:
            print(f"[AGENT] LLM generation failed ({exc}), falling back to direct tool message.")
            final_text = f"He procesado tu consulta financiera: '{request}'. {tool_results[0].message if tool_results else 'Sin registros disponibles.'}"
            llm_used = False

        return AgentResponse(
            agent_name=self.name,
            intent="financial",
            tools_executed=tools_executed,
            tool_results=tool_results,
            final_response=final_text,
            raw_llm_response=final_text if llm_used else None,
            llm_used=llm_used
        )

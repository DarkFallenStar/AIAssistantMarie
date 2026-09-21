from typing import Dict, Any, List, Optional
from app.agents.base import BaseAgent, AgentResponse
from app.tools.base import BaseTool, ToolResult
from app.tools.cashflow_tool import CashFlowTool
from app.tools.transaction_tool import TransactionTool
from app.services.llm import get_llm_service, BaseLLMService

class FinancialAgent(BaseAgent):
    """
    Specialized agent for financial analysis, cashflow monitoring, budget, and transactions.
    """

    def __init__(self, llm_service: Optional[BaseLLMService] = None):
        self._custom_llm = llm_service
        self._tools: Dict[str, BaseTool] = {
            "cashflow_tool": CashFlowTool(),
            "transaction_tool": TransactionTool(),
        }

    @property
    def name(self) -> str:
        return "FinancialAgent"

    @property
    def system_prompt(self) -> str:
        return (
            "Eres el Agente Financiero de un Asistente Personal Inteligente. "
            "Eres experto en presupuestos, análisis de flujo de caja, saldos y control de gastos. "
            "Responde de forma concisa, precisa, profesional y numérica en español. "
            "Basa todas tus cifras y conclusiones estrictamente en los datos provistos por las herramientas financieras."
        )

    @property
    def tools(self) -> Dict[str, BaseTool]:
        return self._tools

    def get_llm(self) -> BaseLLMService:
        if self._custom_llm is not None:
            return self._custom_llm
        return get_llm_service()

    def determine_tools(self, request: str) -> List[tuple]:
        req_lower = request.lower()
        tools_to_run = []

        # Cashflow / Balance keywords
        if any(kw in req_lower for kw in ["saldo", "dinero", "disponible", "queda", "quedan", "cuenta", "presupuesto", "fin de semana", "mes", "ahorro"]):
            tools_to_run.append(("cashflow_tool", {"period": "current_month"}))

        # Transactions keywords
        if any(kw in req_lower for kw in ["gasto", "gaste", "gasté", "gastos", "compre", "compré", "movimientos", "transacciones", "tarjeta", "ultimos"]):
            tools_to_run.append(("transaction_tool", {"limit": 5}))

        # Default fallback if financial intent detected
        if not tools_to_run:
            tools_to_run.append(("cashflow_tool", {"period": "current_month"}))

        return tools_to_run

    async def handle(self, request: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        print(f"[AGENT] {self.name} processing request: '{request}'")

        # 1. Determinar herramientas necesarias
        tools_to_run = self.determine_tools(request)
        tools_executed: List[str] = []
        tool_results: List[ToolResult] = []
        tool_context_texts: List[str] = []

        # 2. Ejecutar herramientas financieras
        for tool_name, params in tools_to_run:
            tool = self._tools.get(tool_name)
            if tool:
                tools_executed.append(tool_name)
                result = await tool.execute(**params)
                tool_results.append(result)
                tool_context_texts.append(f"Herramienta '{tool_name}': {result.message}\nDatos: {result.data}")

        tool_summary = "\n\n".join(tool_context_texts)

        # 3. Prompt aumentado con números y balances reales
        augmented_prompt = (
            f"Consulta financiera del usuario: '{request}'\n\n"
            f"Datos contables y financieros obtenidos del sistema:\n{tool_summary}\n\n"
            "Instrucción: Proporciona una respuesta clara, profesional y con cifras exactas respondiendo directamente a la inquietud del usuario."
        )

        # 4. Síntesis con LLM
        try:
            llm = self.get_llm()
            llm_resp = await llm.generate(prompt=augmented_prompt, system_prompt=self.system_prompt)
            final_text = llm_resp.text
            llm_used = True
        except Exception as exc:
            print(f"[AGENT] LLM generation failed ({exc}), falling back to tool message.")
            final_text = f"He recibido tu consulta financiera: '{request}'. {tool_results[0].message if tool_results else 'Sin registros disponibles.'}"
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

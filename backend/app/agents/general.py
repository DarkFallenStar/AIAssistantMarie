from typing import Dict, Any, List, Optional
from app.agents.base import BaseAgent, AgentResponse
from app.tools.base import BaseTool
from app.services.llm import get_llm_service, BaseLLMService

class GeneralAgent(BaseAgent):
    """
    Agent for handling general queries, greetings, and system capability explanations.
    """

    def __init__(self, llm_service: Optional[BaseLLMService] = None):
        self._custom_llm = llm_service

    @property
    def name(self) -> str:
        return "GeneralOrchestrator"

    @property
    def system_prompt(self) -> str:
        return (
            "Eres Marie, una Asistente Personal Inteligente multi-agente, carismática, eficiente y amigable. "
            "Responde de manera natural, empática y concisa en español a cualquier interacción general: "
            "saludos, conversación casual, curiosidades, preguntas de cultura general y solicitudes de entretenimiento ligero (como chistes, anécdotas o trabalenguas). "
            "Si el usuario te pide un chiste, cuéntale uno gracioso y ocurrente de inmediato con buen humor. "
            "Además, puedes orientar al usuario recordándole que cuentas con agentes especializados en Secretaría (gestión de tareas, recordatorios y correos) "
            "y Finanzas (saldo disponible, flujo de caja, gastos, transacciones, tarjetas, préstamos y metas de ahorro)."
        )

    @property
    def tools(self) -> Dict[str, BaseTool]:
        return {}

    def get_llm(self) -> BaseLLMService:
        if self._custom_llm is not None:
            return self._custom_llm
        return get_llm_service()

    async def handle(self, request: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        print(f"[AGENT] {self.name} processing request: '{request}'")
        try:
            llm = self.get_llm()
            llm_resp = await llm.generate(prompt=request, system_prompt=self.system_prompt)
            final_text = llm_resp.text
        except Exception as exc:
            print(f"[AGENT] LLM generation failed ({exc}), falling back to friendly message.")
            final_text = f"Hola, he recibido tu mensaje: '{request}'. ¿En qué puedo ayudarte hoy?"

        return AgentResponse(
            agent_name=self.name,
            intent="general",
            tools_executed=[],
            tool_results=[],
            final_response=final_text,
            raw_llm_response=final_text
        )

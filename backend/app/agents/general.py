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
            "Eres un Asistente Personal Inteligente multi-agente con control por voz. "
            "Responde de manera amable, útil y concisa en español. "
            "Puedes asistir al usuario en dos áreas principales: "
            "1. Secretaría (tareas, recordatorios, correos). "
            "2. Finanzas (saldo disponible, flujo de caja, gastos y transacciones)."
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

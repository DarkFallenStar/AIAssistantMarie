from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.services.llm import get_llm_service, BaseLLMService
from app.agents.base import BaseAgent, AgentResponse
from app.agents.secretary import SecretaryAgent
from app.agents.financial import FinancialAgent
from app.agents.general import GeneralAgent

class OrchestratorResponse(BaseModel):
    input_text: str
    intent: str
    agent: str
    response: str
    llm_used: bool = False
    tools_executed: List[str] = Field(default_factory=list)


class OrchestratorService:
    """
    Central Orchestrator (Fase 8).
    Coordinates the 7-step multi-agent execution pipeline:
      1. Recibir la petición.
      2. Analizar intención.
      3. Determinar qué agente necesita (Secretary, Financial, General).
      4. Determinar qué herramientas necesita.
      5. Ejecutar las herramientas.
      6. Recibir los resultados.
      7. Generar la respuesta final (vía LLM con contexto enriquecido).
    """

    FINANCIAL_KEYWORDS = [
        "dinero", "saldo", "gasto", "gaste", "gasté", "gastos", "disponible", 
        "quedan", "cuenta", "presupuesto", "comprar", "tarjeta", 
        "finanzas", "banco", "prestamo", "ahorro", "pagar", "flujo", "caja"
    ]

    SECRETARY_KEYWORDS = [
        "recuerda", "recordar", "recordatorio", "tarea", "tareas", 
        "agenda", "reunion", "reunión", "evento", "cita", "anota", "nota", 
        "pendiente", "manana", "mañana", "calendario", "correo", "email", 
        "buzon", "buzón", "decano", "mensaje", "escribio", "escribió", "respondio", "respondió"
    ]

    def __init__(self, llm_service: Optional[BaseLLMService] = None):
        self._llm_service = llm_service
        self.secretary_agent = SecretaryAgent(llm_service=self._llm_service)
        self.financial_agent = FinancialAgent(llm_service=self._llm_service)
        self.general_agent = GeneralAgent(llm_service=self._llm_service)

    def set_llm_service(self, llm_service: Optional[BaseLLMService]):
        self._llm_service = llm_service
        self.secretary_agent = SecretaryAgent(llm_service=llm_service)
        self.financial_agent = FinancialAgent(llm_service=llm_service)
        self.general_agent = GeneralAgent(llm_service=llm_service)

    def normalize_text(self, text: str) -> str:
        import unicodedata
        normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        return normalized.lower()

    def classify_intent(self, text: str) -> str:
        text_clean = self.normalize_text(text)

        # Count keyword occurrences
        secretary_score = sum(1 for kw in self.SECRETARY_KEYWORDS if kw in text_clean)
        financial_score = sum(1 for kw in self.FINANCIAL_KEYWORDS if kw in text_clean)

        # Explicit email/reminder verbs take priority
        if any(kw in text_clean for kw in ["correo", "email", "decano", "recuerda", "recordar", "recordatorio", "anota"]):
            return "secretary"

        if financial_score > secretary_score:
            return "financial"
        elif secretary_score > financial_score:
            return "secretary"
        elif financial_score > 0:
            return "financial"

        return "general"

    async def process_user_input(self, text: str, use_llm: bool = True) -> OrchestratorResponse:
        trimmed = text.strip()
        print(f"[ORCHESTRATOR] Step 1 - Input received: '{trimmed}'")

        if not trimmed:
            return OrchestratorResponse(
                input_text="",
                intent="unknown",
                agent="Orchestrator",
                response="No logre escuchar con claridad tu audio, por favor intentalo de nuevo.",
                llm_used=False,
                tools_executed=[]
            )

        # Step 2: Analizar intención
        intent = self.classify_intent(trimmed)
        print(f"[ORCHESTRATOR] Step 2 - Intent analyzed: '{intent}'")

        # Step 3: Determinar qué agente necesita
        if intent == "financial":
            target_agent: BaseAgent = self.financial_agent
        elif intent == "secretary":
            target_agent: BaseAgent = self.secretary_agent
        else:
            target_agent: BaseAgent = self.general_agent

        print(f"[ORCHESTRATOR] Step 3 - Routing to agent: {target_agent.name}")

        # If use_llm is False (e.g. deterministic fast unit test without LLM)
        if not use_llm:
            if intent == "financial":
                fallback = f"He recibido tu consulta financiera: '{trimmed}'. Analizando tus cuentas y saldo disponible."
            elif intent == "secretary":
                fallback = f"He recibido tu solicitud de organizacion: '{trimmed}'. Gestionando tus tareas y agenda."
            else:
                fallback = f"He procesado tu mensaje: '{trimmed}'. Estoy listo para ayudarte."

            return OrchestratorResponse(
                input_text=trimmed,
                intent=intent,
                agent=target_agent.name,
                response=fallback,
                llm_used=False,
                tools_executed=[]
            )

        # Steps 4 to 7: Delegate to Agent (Determine Tools -> Execute Tools -> Capture Results -> Synthesize LLM)
        print(f"[ORCHESTRATOR] Steps 4-7 - Executing agent pipeline ({target_agent.name})...")
        agent_response: AgentResponse = await target_agent.handle(trimmed)

        print(f"[ORCHESTRATOR] Pipeline completed. Tools executed: {agent_response.tools_executed}")
        return OrchestratorResponse(
            input_text=trimmed,
            intent=intent,
            agent=target_agent.name,
            response=agent_response.final_response,
            llm_used=agent_response.llm_used,
            tools_executed=agent_response.tools_executed
        )


_orchestrator_instance: Optional[OrchestratorService] = None

def get_orchestrator_service() -> OrchestratorService:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = OrchestratorService()
    return _orchestrator_instance

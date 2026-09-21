import re
import json
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

from app.services.llm import get_llm_service, BaseLLMService
from app.agents.base import BaseAgent, AgentResponse
from app.agents.secretary import SecretaryAgent
from app.agents.financial import FinancialAgent
from app.agents.general import GeneralAgent
from app.schemas.structured import StructuredIntent, SubIntentAction
from app.tools.dispatcher import get_tool_dispatcher, ToolDispatcher

class OrchestratorResponse(BaseModel):
    input_text: str
    intent: str
    agent: str
    response: str
    llm_used: bool = False
    tools_executed: List[str] = Field(default_factory=list)
    structured_intent: Optional[StructuredIntent] = None


FUNCTION_CALLING_SYSTEM_PROMPT = """
Eres el Núcleo de Clasificación y Function Calling de un Asistente Personal Inteligente multi-agente.
Tu función es analizar la petición del usuario y generar estrictamente un objeto JSON estructurado con el agente responsable, la herramienta canónica a invocar y sus argumentos.

AGENTES DISPONIBLES:
1. "general":
   - Se utiliza para: Saludos ("hola", "buenos días"), conversación casual, preguntas sobre ti ("¿quién eres?"), preguntas generales de cultura y solicitudes de entretenimiento o humor (CHISTES, bromas, trabalenguas, etc.).
   - Para el agente "general", la herramienta "tool" SIEMPRE debe ser null y "arguments" debe ser {}.

2. "financial":
   - Se utiliza para: Consultas y operaciones de finanzas personales.
   - Herramientas disponibles:
     * "calculate_cash_flow": Calcula saldo neto y flujo de caja del mes. Argumentos: {"period": "current_month"}
     * "list_transactions": Consulta transacciones o movimientos recientes. Argumentos: {"category": null o string, "limit": 5}
     * "create_transaction": Registra un nuevo gasto o ingreso. Argumentos: {"amount": float, "type": "expense" | "income", "category": str, "description": str, "merchant": str, "currency": "COP" | "USD"}
     * "categorize_transaction": Modifica la categoría de una transacción. Argumentos: {"transaction_id": str, "category": str}
     * "list_credit_cards": Consulta tarjetas de crédito y saldo disponible. Argumentos: {}
     * "list_loans": Consulta préstamos, cuotas y deudas activas. Argumentos: {}
     * "list_saving_goals": Consulta metas de ahorro y progreso. Argumentos: {}
     * "update_saving_goal": Actualiza o abona dinero a una meta de ahorro. Argumentos: {"goal_id": str, "current_amount": float}

3. "secretary":
   - Se utiliza para: Gestión de agenda, tareas, recordatorios y correos electrónicos.
   - Herramientas disponibles:
     * "list_tasks": Lista tareas pendientes. Argumentos: {"status": "pending" o null, "limit": 5}
     * "create_task": Crea una nueva tarea. Argumentos: {"title": str, "due_date": str o null, "priority": "low" | "medium" | "high"}
     * "complete_task": Marca una tarea como completada. Argumentos: {"task_id": str}
     * "list_reminders": Lista recordatorios. Argumentos: {"timeframe": "all" | "today" | "upcoming", "limit": 5}
     * "create_reminder": Programa un recordatorio. Argumentos: {"title": str, "remind_at": str, "channel": "app"}
     * "list_unread_emails": Consulta correos no leídos pendientes. Argumentos: {"limit": 5}
     * "list_emails": Consulta correos recibidos. Argumentos: {"status": "unread" o null, "limit": 5}
     * "get_email": Lee un correo específico por ID. Argumentos: {"email_id": str}
     * "search_emails": Busca correos por remitente o asunto. Argumentos: {"search": str}
     * "summarize_email": Genera resumen ejecutivo de un correo específico o por búsqueda. Argumentos: {"query": str o null, "email_id": str o null}
     * "prioritize_emails": Clasifica y ordena los correos por nivel de prioridad o urgencia. Argumentos: {"limit": 5}
     * "draft_email": Redacta un borrador de correo sin enviarlo. Argumentos: {"recipient": str, "subject": str, "body": str}
     * "send_email": Solicita enviar un correo (crea borrador y solicita confirmación previa). Argumentos: {"recipient": str, "subject": str, "body": str, "confirmed": false}

4. "combined":
   - Se utiliza cuando la petición del usuario contiene MÚLTIPLES intenciones o acciones de diferentes agentes (ej. Secretaría + Finanzas: "Anota una tarea de pagar la luz y dime cuánto dinero me queda en la cuenta").
   - Para "combined", "tool" debe ser null y se incluye la lista "actions":
     [
       {"agent": "secretary", "tool": "create_task", "arguments": {"title": "Pagar la luz", "priority": "medium"}},
       {"agent": "financial", "tool": "calculate_cash_flow", "arguments": {"period": "current_month"}}
     ]

REGLAS DE SALIDA:
- Responde ÚNICAMENTE con un JSON válido.
- NO agregues bloques ```json ni texto adicional antes o después del JSON.
- Estructura JSON requerida:
{
  "agent": "financial" | "secretary" | "general" | "combined",
  "tool": "<nombre_herramienta>" | null,
  "arguments": { ... },
  "actions": [ ... ],
  "reasoning": "<breve justificación>"
}
"""


class OrchestratorService:
    """
    Central Orchestrator (Fases 8 y 11).
    Coordinates intent extraction via Function Calling / Structured Output,
    executes tools via ToolDispatcher, and synthesizes natural language responses.
    """

    GENERAL_KEYWORDS = [
        "chiste", "chistes", "broma", "bromas", "gracioso", "graciosa", "chistoso",
        "hola", "buenos dias", "buenas tardes", "buenas noches", "que tal",
        "como estas", "quien eres", "como te llamas", "que puedes hacer", "ayuda",
        "gracias", "muchas gracias", "adios", "hasta luego", "cuentame algo", "cuentame una historia"
    ]

    FINANCIAL_KEYWORDS = [
        "dinero", "saldo", "gasto", "gaste", "gasté", "gastos", "disponible", 
        "quedan", "presupuesto", "comprar", "tarjeta", "tarjetas", "credito", "crédito",
        "finanzas", "banco", "prestamo", "préstamo", "prestamos", "ahorro", "ahorros",
        "pagar", "flujo", "caja", "cuenta bancaria", "mis cuentas", "en mi cuenta"
    ]

    SECRETARY_KEYWORDS = [
        "recuerda", "recordar", "recordatorio", "recordatorios", "tarea", "tareas", 
        "agenda", "reunion", "reunión", "evento", "cita", "anota", "nota", 
        "pendiente", "pendientes", "manana", "mañana", "calendario", "correo", "email", 
        "buzon", "buzón", "decano", "mensaje", "escribio", "escribió", "respondio", "respondió"
    ]

    def __init__(self, llm_service: Optional[BaseLLMService] = None):
        self._llm_service = llm_service
        self.secretary_agent = SecretaryAgent(llm_service=self._llm_service)
        self.financial_agent = FinancialAgent(llm_service=self._llm_service)
        self.general_agent = GeneralAgent(llm_service=self._llm_service)
        self.dispatcher = get_tool_dispatcher()
        self._pending_confirmation: Optional[Dict[str, Any]] = None

    def set_llm_service(self, llm_service: Optional[BaseLLMService]):
        self._llm_service = llm_service
        self.secretary_agent = SecretaryAgent(llm_service=llm_service)
        self.financial_agent = FinancialAgent(llm_service=llm_service)
        self.general_agent = GeneralAgent(llm_service=llm_service)

    def get_llm(self) -> BaseLLMService:
        if self._llm_service is not None:
            return self._llm_service
        return get_llm_service()

    def normalize_text(self, text: str) -> str:
        import unicodedata
        normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        return normalized.lower()

    def classify_intent(self, text: str) -> str:
        """
        Fast heuristic classifier with strict word-boundary checks and general intent protection.
        Prevents substring collisions like 'cuenta' in 'cuentame un chiste'.
        """
        text_clean = self.normalize_text(text)

        # 1. Highest Priority: Explicit general conversation / jokes / greetings
        for kw in self.GENERAL_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_clean) or kw in text_clean:
                return "general"

        # 2. Score financial keywords
        financial_score = 0
        for kw in self.FINANCIAL_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_clean):
                financial_score += 1

        # Specific check for standalone 'cuenta' or 'cuentas' (NOT cuentame)
        if re.search(r'\bcuentas?\b', text_clean) and not any(verb in text_clean for verb in ["cuentame", "cuentanos", "cuentale"]):
            financial_score += 1

        # 3. Score secretary keywords
        secretary_score = 0
        for kw in self.SECRETARY_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_clean):
                secretary_score += 1

        if any(kw in text_clean for kw in ["correo", "email", "decano", "recuerda", "recordar", "recordatorio", "anota"]):
            secretary_score += 1

        # 4. Check for combined multi-agent intent (both secretary and financial present with coordination)
        has_coordination = bool(re.search(r'\b(y|ademas|además|tambien|también|despues|después|pero)\b', text_clean))
        if financial_score > 0 and secretary_score > 0:
            if has_coordination or (financial_score >= 2 and secretary_score >= 2):
                return "combined"

        if financial_score > secretary_score:
            return "financial"
        elif secretary_score > financial_score:
            return "secretary"
        elif financial_score > 0:
            return "financial"
        elif secretary_score > 0:
            return "secretary"

        return "general"

    async def extract_structured_intent(self, text: str) -> Optional[StructuredIntent]:
        """
        Fase 11 & 19: Invokes LLM with Function Calling prompt to produce a structured JSON intent.
        Supports single-agent tools and combined multi-agent actions.
        """
        llm = self.get_llm()
        try:
            resp = await llm.generate(
                prompt=f"Petición del usuario: '{text}'",
                system_prompt=FUNCTION_CALLING_SYSTEM_PROMPT,
                temperature=0.1
            )
            raw_text = resp.text.strip()
            print(f"[FUNCTION-CALLING] Raw LLM intent output: {raw_text[:200]}")

            # Extract JSON block even if model wraps in backticks
            clean_json = raw_text
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if json_match:
                clean_json = json_match.group(0)

            parsed = json.loads(clean_json)
            agent = parsed.get("agent", "general").lower()
            if agent not in ["financial", "secretary", "general", "combined", "multi", "multiagent"]:
                agent = "general"

            tool = parsed.get("tool")
            if tool and isinstance(tool, str):
                tool = tool.strip()
                if tool.lower() in ["null", "none", ""]:
                    tool = None
            else:
                tool = None

            arguments = parsed.get("arguments", {})
            if not isinstance(arguments, dict):
                arguments = {}

            # Parse sub-actions if combined intent
            parsed_actions: Optional[List[SubIntentAction]] = None
            raw_actions = parsed.get("actions")
            if isinstance(raw_actions, list) and len(raw_actions) > 0:
                agent = "combined"
                parsed_actions = []
                for act in raw_actions:
                    if isinstance(act, dict):
                        act_agent = act.get("agent", "general").lower()
                        if act_agent not in ["financial", "secretary", "general"]:
                            act_agent = "general"
                        act_tool = act.get("tool")
                        if act_tool and isinstance(act_tool, str):
                            act_tool = act_tool.strip()
                            if act_tool.lower() in ["null", "none", ""]:
                                act_tool = None
                        else:
                            act_tool = None
                        act_args = act.get("arguments", {})
                        if not isinstance(act_args, dict):
                            act_args = {}
                        parsed_actions.append(SubIntentAction(
                            agent=act_agent,
                            tool=act_tool,
                            arguments=act_args,
                            reasoning=act.get("reasoning")
                        ))

            if agent in ["multi", "multiagent"]:
                agent = "combined"

            structured = StructuredIntent(
                agent=agent,
                tool=tool,
                arguments=arguments,
                actions=parsed_actions,
                reasoning=parsed.get("reasoning")
            )
            print(f"[FUNCTION-CALLING] Parsed StructuredIntent: agent={structured.agent}, tool={structured.tool}, args={structured.arguments}, actions={len(parsed_actions) if parsed_actions else 0}")
            return structured

        except Exception as exc:
            print(f"[FUNCTION-CALLING] Structured intent extraction failed ({exc}). Falling back to heuristic classification.")
            return None

    async def process_user_input(self, text: str, use_llm: bool = True) -> OrchestratorResponse:
        """
        Main execution pipeline integrating Function Calling, Tool Execution, and Natural Language Synthesis.
        """
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

        # -------------------------------------------------------------
        # Step 0: Check Pending Human-in-the-Loop Confirmation (Fase 12)
        # -------------------------------------------------------------
        if self._pending_confirmation is not None:
            clean_input = self.normalize_text(trimmed)
            if any(w in clean_input for w in ["si", "sí", "enviar", "confirmo", "adelante", "procede", "enviarlo", "mándalo", "mandalo", "confirmar", "ok"]):
                pending = self._pending_confirmation
                self._pending_confirmation = None
                print(f"[ORCHESTRATOR] Human confirmed email dispatch to {pending.get('recipient')}")
                send_res = await self.dispatcher.dispatch("send_email", {
                    "recipient": pending.get("recipient"),
                    "subject": pending.get("subject"),
                    "body": pending.get("body"),
                    "confirmed": True
                })
                return OrchestratorResponse(
                    input_text=trimmed,
                    intent="secretary",
                    agent=self.secretary_agent.name,
                    response=send_res.message,
                    llm_used=True,
                    tools_executed=["send_email"]
                )
            elif any(w in clean_input for w in ["no", "cancela", "cancelar", "no enviar", "detener", "abortar"]):
                self._pending_confirmation = None
                return OrchestratorResponse(
                    input_text=trimmed,
                    intent="secretary",
                    agent=self.secretary_agent.name,
                    response="Envío de correo cancelado por el usuario. El borrador permanece guardado.",
                    llm_used=False,
                    tools_executed=[]
                )

        # -------------------------------------------------------------
        # Deterministic / Fast Mode (Without LLM calls)
        # -------------------------------------------------------------
        if not use_llm:
            intent = self.classify_intent(trimmed)
            if intent == "combined":
                fallback = f"He recibido tu solicitud combinada: '{trimmed}'. Coordinando las acciones entre Secretaría y Finanzas."
                agent_name = "MultiAgent"
            elif intent == "financial":
                fallback = f"He recibido tu consulta financiera: '{trimmed}'. Analizando tus cuentas y saldo disponible."
                agent_name = self.financial_agent.name
            elif intent == "secretary":
                fallback = f"He recibido tu solicitud de organizacion: '{trimmed}'. Gestionando tus tareas y agenda."
                agent_name = self.secretary_agent.name
            else:
                fallback = f"He procesado tu mensaje: '{trimmed}'. Estoy listo para ayudarte."
                agent_name = self.general_agent.name

            return OrchestratorResponse(
                input_text=trimmed,
                intent=intent,
                agent=agent_name,
                response=fallback,
                llm_used=False,
                tools_executed=[]
            )

        # -------------------------------------------------------------
        # Step 2: Function Calling / Structured Intent Extraction (LLM)
        # -------------------------------------------------------------
        structured_intent = await self.extract_structured_intent(trimmed)

        # Fallback to heuristic intent classification if structured extraction failed
        if structured_intent is None:
            heuristic_intent = self.classify_intent(trimmed)
            structured_intent = StructuredIntent(
                agent=heuristic_intent,
                tool=None,
                arguments={},
                reasoning="Heuristic fallback"
            )

        intent = structured_intent.agent
        tool_name = structured_intent.tool
        tool_args = structured_intent.arguments

        # -------------------------------------------------------------
        # Step 2.5: Combined / Multi-Agent Execution Pipeline (Fase 19)
        # -------------------------------------------------------------
        if intent == "combined" or (structured_intent and structured_intent.actions):
            actions = structured_intent.actions if (structured_intent and structured_intent.actions) else []
            if not actions:
                # Heuristic decomposition if no explicit sub-actions extracted
                actions = []
                clean_t = self.normalize_text(trimmed)
                if any(w in clean_t for w in ["tarea", "anota", "recordatorio", "recuerda", "agenda", "pendiente"]):
                    actions.append(SubIntentAction(agent="secretary", tool="create_task", arguments={"title": trimmed, "priority": "medium"}))
                elif any(w in clean_t for w in ["correo", "email", "buzon"]):
                    actions.append(SubIntentAction(agent="secretary", tool="list_unread_emails", arguments={"limit": 5}))

                if any(w in clean_t for w in ["saldo", "dinero", "flujo", "disponible", "quedan", "cuenta"]):
                    actions.append(SubIntentAction(agent="financial", tool="calculate_cash_flow", arguments={"period": "current_month"}))
                elif any(w in clean_t for w in ["gasto", "gaste", "compre", "transaccion", "movimiento"]):
                    actions.append(SubIntentAction(agent="financial", tool="list_transactions", arguments={"limit": 5}))
                elif any(w in clean_t for w in ["tarjeta", "credito"]):
                    actions.append(SubIntentAction(agent="financial", tool="list_credit_cards", arguments={}))
                elif any(w in clean_t for w in ["meta", "ahorro"]):
                    actions.append(SubIntentAction(agent="financial", tool="list_saving_goals", arguments={}))

            executed_tools = []
            tool_outputs = []
            for act in actions:
                if act.tool:
                    print(f"[ORCHESTRATOR-MULTI] Executing combined tool '{act.tool}' for agent '{act.agent}'...")
                    res = await self.dispatcher.dispatch(act.tool, act.arguments)
                    executed_tools.append(act.tool)
                    tool_outputs.append({
                        "agent": act.agent,
                        "tool": act.tool,
                        "message": res.message,
                        "data": res.data
                    })
                    if res.data and isinstance(res.data, dict) and res.data.get("requires_confirmation"):
                        self._pending_confirmation = res.data

            combined_summary = "\n".join([f"- [{out['agent'].capitalize()} - {out['tool']}]: {out['message']}" for out in tool_outputs])

            augmented_prompt = (
                f"Consulta del usuario: '{trimmed}'\n\n"
                f"Herramientas ejecutadas de múltiples agentes para resolver integralmente la solicitud:\n"
                f"{combined_summary}\n\n"
                f"Instrucción: Genera una respuesta coordinada, ejecutiva y clara en español, confirmando las acciones realizadas de ambos agentes."
            )
            system_prompt = (
                "Eres el Orquestador Central Multi-Agente del Asistente Personal Inteligente. "
                "Tu labor es unificar las acciones realizadas por los agentes de Secretaría y Finanzas en una respuesta clara, profesional y concisa."
            )

            try:
                llm = self.get_llm()
                resp = await llm.generate(prompt=augmented_prompt, system_prompt=system_prompt)
                final_text = resp.text
                llm_used = True
            except Exception as exc:
                print(f"[ORCHESTRATOR-MULTI] LLM synthesis failed ({exc}). Using direct tool summary fallback.")
                final_text = f"He coordinado y procesado tus solicitudes:\n{combined_summary}"
                llm_used = False

            return OrchestratorResponse(
                input_text=trimmed,
                intent="combined",
                agent="MultiAgent",
                response=final_text,
                llm_used=llm_used,
                tools_executed=executed_tools,
                structured_intent=structured_intent
            )

        # -------------------------------------------------------------
        # Step 3: Handle Pure Conversational Interaction (No Tool / General Agent)
        # -------------------------------------------------------------
        if intent == "general" or not tool_name:
            if intent == "financial":
                # If financial intent but no specific tool extracted, let financial agent handle
                agent_resp = await self.financial_agent.handle(trimmed)
                return OrchestratorResponse(
                    input_text=trimmed,
                    intent=intent,
                    agent=self.financial_agent.name,
                    response=agent_resp.final_response,
                    llm_used=agent_resp.llm_used,
                    tools_executed=agent_resp.tools_executed,
                    structured_intent=structured_intent
                )
            elif intent == "secretary":
                agent_resp = await self.secretary_agent.handle(trimmed)
                return OrchestratorResponse(
                    input_text=trimmed,
                    intent=intent,
                    agent=self.secretary_agent.name,
                    response=agent_resp.final_response,
                    llm_used=agent_resp.llm_used,
                    tools_executed=agent_resp.tools_executed,
                    structured_intent=structured_intent
                )
            else:
                # pure general interaction (jokes, greetings, questions)
                agent_resp = await self.general_agent.handle(trimmed)
                return OrchestratorResponse(
                    input_text=trimmed,
                    intent="general",
                    agent=self.general_agent.name,
                    response=agent_resp.final_response,
                    llm_used=agent_resp.llm_used,
                    tools_executed=[],
                    structured_intent=structured_intent
                )

        # -------------------------------------------------------------
        # Step 4 & 5: Tool Execution via ToolDispatcher
        # -------------------------------------------------------------
        tools_executed = [tool_name]
        print(f"[ORCHESTRATOR] Executing tool '{tool_name}' with args {tool_args}...")
        tool_result = await self.dispatcher.dispatch(tool_name, tool_args)
        safe_msg = str(tool_result.message).encode('ascii', 'replace').decode('ascii')
        print(f"[ORCHESTRATOR] Tool result: success={tool_result.success}, msg={safe_msg}")

        # Check if tool requires explicit human confirmation before proceeding
        if tool_result.data and isinstance(tool_result.data, dict) and tool_result.data.get("requires_confirmation"):
            self._pending_confirmation = tool_result.data
            print(f"[ORCHESTRATOR] Tool requires human confirmation: {tool_result.data}")
            return OrchestratorResponse(
                input_text=trimmed,
                intent=intent,
                agent=self.secretary_agent.name if intent == "secretary" else self.general_agent.name,
                response=tool_result.message,
                llm_used=True,
                tools_executed=[tool_name],
                structured_intent=structured_intent
            )

        # -------------------------------------------------------------
        # Step 6 & 7: Synthesis of Natural Response with LLM
        # -------------------------------------------------------------
        if intent == "financial":
            agent_name = self.financial_agent.name
            system_prompt = self.financial_agent.system_prompt
            instruction = (
                "Instrucción: Proporciona una respuesta ejecutiva, profesional y numérica basada estrictamente en los datos anteriores. "
                "Si no hay datos que respalden la consulta del usuario, acláralo honestamente sin conjeturar ni inventar cifras."
            )
        else:
            agent_name = self.secretary_agent.name
            system_prompt = self.secretary_agent.system_prompt
            instruction = (
                "Instrucción: Responde al usuario de manera clara, cortés y ejecutiva confirmando o informando los detalles de la acción realizada "
                "basándote estrictamente en los datos de la herramienta anterior."
            )

        augmented_prompt = (
            f"Consulta del usuario: '{trimmed}'\n\n"
            f"Herramienta ejecutada: '{tool_name}' con argumentos {tool_args}\n"
            f"Resultado de la herramienta:\n"
            f"- Mensaje: {tool_result.message}\n"
            f"- Datos estructurados: {tool_result.data}\n\n"
            f"{instruction}"
        )

        try:
            llm = self.get_llm()
            llm_resp = await llm.generate(prompt=augmented_prompt, system_prompt=system_prompt)
            final_text = llm_resp.text
            llm_used = True
        except Exception as exc:
            print(f"[ORCHESTRATOR] LLM synthesis failed ({exc}). Using direct tool message fallback.")
            final_text = tool_result.message
            llm_used = False

        return OrchestratorResponse(
            input_text=trimmed,
            intent=intent,
            agent=agent_name,
            response=final_text,
            llm_used=llm_used,
            tools_executed=tools_executed,
            structured_intent=structured_intent
        )


_orchestrator_instance: Optional[OrchestratorService] = None

def get_orchestrator_service() -> OrchestratorService:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = OrchestratorService()
    return _orchestrator_instance

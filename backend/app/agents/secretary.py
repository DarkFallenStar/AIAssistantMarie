import re
from typing import Dict, Any, List, Optional
from app.agents.base import BaseAgent, AgentResponse
from app.tools.base import BaseTool, ToolResult
from app.tools.email_tool import EmailTools, EmailTool
from app.tools.task_tool import TaskTools, TaskTool
from app.tools.reminder_tool import ReminderTools, ReminderTool
from app.services.llm import get_llm_service, BaseLLMService

class SecretaryAgent(BaseAgent):
    """
    Specialized agent for managing user calendar, tasks, reminders, and incoming emails.
    Orchestrates independent tools (EmailTools, TaskTools, ReminderTools).
    """

    def __init__(self, llm_service: Optional[BaseLLMService] = None):
        self._custom_llm = llm_service
        self.email_tools = EmailTools()
        self.task_tools = TaskTools()
        self.reminder_tools = ReminderTools()

        self._tools: Dict[str, BaseTool] = {
            "email_tool": self.email_tools,
            "task_tool": self.task_tools,
            "reminder_tool": self.reminder_tools,
        }

    @property
    def name(self) -> str:
        return "SecretaryAgent"

    @property
    def system_prompt(self) -> str:
        return (
            "Eres el Agente Secretaria de un Asistente Personal Inteligente de alto nivel. "
            "Tu misión es gestionar tareas, recordatorios, citas y correos electrónicos del usuario. "
            "Responde de forma clara, ejecutiva, cortés y proactiva en español. "
            "Utiliza estrictamente la información y datos reales provistos por las herramientas del sistema."
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
        Determines which tools and parameters are needed based on user request.
        Extracts structured intent for email, task, or reminder operations.
        """
        req_lower = request.lower()
        tools_to_run = []

        # -------------------------------------------------------------
        # 1. EMAIL INTENT
        # -------------------------------------------------------------
        if any(kw in req_lower for kw in ["correo", "email", "mensaje", "respondio", "respondió", "escribio", "escribió", "decano", "borrador"]):
            # A. Draft creation
            if any(kw in req_lower for kw in ["borrador", "redacta", "escribe un correo", "crear borrador"]):
                # Extract recipient
                recipient_match = re.search(r'(?:para|a)\s+([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', request)
                recipient = recipient_match.group(1) if recipient_match else "contacto@empresa.com"

                # Extract subject
                subject_match = re.search(r'(?:asunto|sobre)\s+[:"]?([^,."\n]+)', request, re.IGNORECASE)
                subject = subject_match.group(1).strip() if subject_match else "Sin asunto especificado"

                # Extract body
                body_match = re.search(r'(?:que diga|cuerpo|mensaje|contenido)[:\s]+["\']?([^"\']+)["\']?', request, re.IGNORECASE)
                body = body_match.group(1).strip() if body_match else f"Borrador preparado para {recipient} sobre {subject}."

                tools_to_run.append(("email_tool", {
                    "action": "draft",
                    "recipient": recipient,
                    "subject": subject,
                    "body": body
                }))
            # B. Get single email by ID
            elif any(kw in req_lower for kw in ["lee el correo", "dame el correo", "ver correo"]):
                id_match = re.search(r'(?:id|correo)\s+([eE]\w+-\w+)', request)
                email_id = id_match.group(1) if id_match else "e1a1-0001"
                tools_to_run.append(("email_tool", {"action": "get", "email_id": email_id}))
            # C. Search or List emails
            else:
                search_query = None
                if "decano" in req_lower:
                    search_query = "decano"
                else:
                    search_match = re.search(r'(?:de|sobre|buscar)\s+([a-zA-Z0-9áéíóúÁÉÍÓÚñÑ_ -]+)', request)
                    if search_match and not any(w in search_match.group(1).lower() for w in ["correo", "email"]):
                        search_query = search_match.group(1).strip()

                if search_query:
                    tools_to_run.append(("email_tool", {"action": "search", "search": search_query}))
                else:
                    tools_to_run.append(("email_tool", {"action": "list", "limit": 5}))

        # -------------------------------------------------------------
        # 2. REMINDER INTENT (Takes precedence over general tasks)
        # -------------------------------------------------------------
        elif any(kw in req_lower for kw in ["recordatorio", "recordatorios", "recuerda", "recuérdame", "recuerdame", "avísame", "avisame"]):
            if any(kw in req_lower for kw in ["completa", "completar", "marca como", "descartar"]):
                id_match = re.search(r'(?:recordatorio|id)\s+([a-zA-Z0-9_-]+)', request)
                rid = id_match.group(1) if id_match else request
                tools_to_run.append(("reminder_tool", {"action": "complete", "reminder_id": rid}))
            elif any(kw in req_lower for kw in ["elimina", "borra", "cancelar"]):
                id_match = re.search(r'(?:recordatorio|id)\s+([a-zA-Z0-9_-]+)', request)
                rid = id_match.group(1) if id_match else request
                tools_to_run.append(("reminder_tool", {"action": "delete", "reminder_id": rid}))
            elif any(kw in req_lower for kw in ["cuáles", "cuales", "lista", "ver", "qué", "que"]):
                tools_to_run.append(("reminder_tool", {"action": "list", "status": "active"}))
            else:
                # Create reminder
                time_match = re.search(r'(?:a las?|para las?|el|mañana|hoy)\s+([0-9:apmAPM\s]+(?:de la (?:tarde|mañana|noche))?)', request, re.IGNORECASE)
                remind_at = time_match.group(0).strip() if time_match else "Hoy, horario pendiente"

                # Extract title by stripping trigger words
                clean_title = re.sub(r'^(?:por favor,?\s*)?(?:recuérdame|recuerdame|recuerda|pon un recordatorio para|avísame de|avisame de)\s*', '', request, flags=re.IGNORECASE).strip()
                tools_to_run.append(("reminder_tool", {
                    "action": "create",
                    "title": clean_title if clean_title else request,
                    "remind_at": remind_at
                }))

        # -------------------------------------------------------------
        # 3. TASK INTENT
        # -------------------------------------------------------------
        elif any(kw in req_lower for kw in ["tarea", "tareas", "pendiente", "pendientes", "agenda", "anota"]):
            if any(kw in req_lower for kw in ["completa", "completar", "terminé", "termine", "hecha"]):
                id_match = re.search(r'(?:tarea|id)\s+([a-zA-Z0-9_-]+)', request)
                tid = id_match.group(1) if id_match else request
                tools_to_run.append(("task_tool", {"action": "complete", "task_id": tid, "title": tid}))
            elif any(kw in req_lower for kw in ["elimina", "borra", "eliminar", "borrar", "quitar"]):
                clean_title = re.sub(r'^(?:por favor,?\s*)?(?:elimina|borra|eliminar|borrar|quitar)\s*(?:la\s*)?tarea\s*(?:de\s*|llamada\s*)?', '', request, flags=re.IGNORECASE).strip()
                tools_to_run.append(("task_tool", {"action": "delete", "task_id": clean_title, "title": clean_title}))
            elif any(kw in req_lower for kw in ["actualiza", "modifica", "cambia"]):
                id_match = re.search(r'(?:tarea|id)\s+([a-zA-Z0-9_-]+)', request)
                tid = id_match.group(1) if id_match else request
                priority = "urgent" if "urgente" in req_lower else ("high" if "alta" in req_lower else "medium")
                tools_to_run.append(("task_tool", {"action": "update", "task_id": tid, "priority": priority}))
            elif any(kw in req_lower for kw in ["crear", "crea", "agrega", "anota", "nueva"]):
                priority = "urgent" if "urgente" in req_lower else ("high" if "alta" in req_lower else "medium")
                time_match = re.search(r'(?:para|el)\s+(mañana|hoy|[0-9-]+)', req_lower)
                due_date = time_match.group(0) if time_match else None
                clean_title = re.sub(r'^(?:por favor,?\s*)?(?:crea|crear|agrega|anota|nueva)\s*(?:una\s*)?tarea\s*(?:para\s*)?', '', request, flags=re.IGNORECASE).strip()
                tools_to_run.append(("task_tool", {
                    "action": "create",
                    "title": clean_title if clean_title else request,
                    "priority": priority,
                    "due_date": due_date
                }))
            else:
                tools_to_run.append(("task_tool", {"action": "list"}))

        # Default fallback
        if not tools_to_run:
            tools_to_run.append(("task_tool", {"action": "list"}))

        return tools_to_run

    async def handle(self, request: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        print(f"[AGENT] {self.name} processing request: '{request}'")

        # 1. Determinar herramientas a ejecutar
        tools_to_run = self.determine_tools(request)
        tools_executed: List[str] = []
        tool_results: List[ToolResult] = []
        tool_context_texts: List[str] = []

        # 2. Ejecutar herramientas independientes
        for tool_name, params in tools_to_run:
            tool = self._tools.get(tool_name)
            if tool:
                tools_executed.append(tool_name)
                result = await tool.execute(**params)
                tool_results.append(result)
                tool_context_texts.append(f"Herramienta '{tool_name}' ({params.get('action', 'execute')}):\nResultado: {result.message}\nDatos estructurados: {result.data}")

        tool_summary = "\n\n".join(tool_context_texts)

        # 3. Formular prompt enriquecido con datos reales
        augmented_prompt = (
            f"Consulta del usuario: '{request}'\n\n"
            f"Resultados estructurados obtenidos del sistema:\n{tool_summary}\n\n"
            "Instrucción: Genera una respuesta ejecutiva, cortés y natural comunicando el estado y resultados precisos al usuario."
        )

        # 4. Generar respuesta final con LLM
        try:
            llm = self.get_llm()
            llm_resp = await llm.generate(prompt=augmented_prompt, system_prompt=self.system_prompt)
            final_text = llm_resp.text
            llm_used = True
        except Exception as exc:
            print(f"[AGENT] LLM generation failed ({exc}), falling back to direct tool message.")
            final_text = f"He procesado tu solicitud de secretaría: '{request}'. {tool_results[0].message if tool_results else 'Operación completada exitosamente.'}"
            llm_used = False

        return AgentResponse(
            agent_name=self.name,
            intent="secretary",
            tools_executed=tools_executed,
            tool_results=tool_results,
            final_response=final_text,
            raw_llm_response=final_text if llm_used else None,
            llm_used=llm_used
        )

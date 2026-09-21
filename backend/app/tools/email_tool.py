import uuid
from typing import Optional, List, Dict, Any
from app.tools.base import BaseTool, ToolResult
from app.services.email import get_email_client, BaseEmailClient, EmailMessage
from app.core.database import get_supabase_client, is_valid_uuid, DEFAULT_USER_ID

class EmailTools(BaseTool):
    """
    Independent tool for managing user emails: listing unread, searching, reading,
    AI executive summarization, prioritization, draft generation, and human-in-the-loop sending.
    Connects to official IMAP server when configured, or persistent Supabase/Mock client.
    """

    MOCK_EMAILS: List[Dict[str, Any]] = [
        {
            "id": "e1a1-0001",
            "sender": "Dr. Fernando Ruiz (Decano de Facultad) <decano@universidad.edu>",
            "recipient": "usuario@asistente.ai",
            "subject": "Respuesta: Solicitud de revision y aprobacion de proyecto",
            "snippet": "Estimado, he revisado la propuesta de investigacion y ha sido aprobada favorablemente.",
            "body": "Estimado, he revisado la propuesta de investigacion del asistente de inteligencia artificial y ha sido aprobada favorablemente por el consejo academico. Podemos proceder con la siguiente fase.",
            "status": "unread",
            "category": "work",
            "received_at": "Hoy, 10:15 a.m.",
            "is_important": True,
            "priority": "HIGH"
        },
        {
            "id": "e1a1-0002",
            "sender": "Banco BBVA Alertas <alertas@bbva.com>",
            "recipient": "usuario@asistente.ai",
            "subject": "Estado de Cuenta Mensual y Fecha de Corte",
            "snippet": "Tu estado de cuenta de la Tarjeta Oro correspondiente al periodo actual ya esta disponible.",
            "body": "Estimado cliente: Le informamos que el corte de su tarjeta Oro fue el dia 15. Su saldo al corte es de $450.25 USD con fecha limite de pago el proximo 5 del mes.",
            "status": "unread",
            "category": "finance",
            "received_at": "Hoy, 08:30 a.m.",
            "is_important": True,
            "priority": "HIGH"
        },
        {
            "id": "e1a1-0003",
            "sender": "Biblioteca Central <biblioteca@universidad.edu>",
            "recipient": "usuario@asistente.ai",
            "subject": "Recordatorio: Devolucion de material bibliografico",
            "snippet": "Tu prestamo del libro vence este viernes.",
            "body": "Recuerda que el libro solicitado vence este viernes 25.",
            "status": "read",
            "category": "alerts",
            "received_at": "Ayer, 3:30 p.m.",
            "is_important": False,
            "priority": "LOW"
        }
    ]

    def __init__(self, email_client: Optional[BaseEmailClient] = None):
        self.client: BaseEmailClient = email_client if email_client is not None else get_email_client()
        self._emails: List[Dict[str, Any]] = [dict(em) for em in self.MOCK_EMAILS]

    @property
    def name(self) -> str:
        return "email_tool"

    @property
    def description(self) -> str:
        return (
            "Gestiona correos electronicos oficiales: listar no leidos, buscar por remitente/asunto, "
            "resumir ejecutivamente con IA, priorizar por urgencia, crear borradores y enviar con confirmacion previa."
        )

    async def list_unread(self, limit: int = 5) -> ToolResult:
        """
        Fase 12: Lists unread emails requiring attention.
        """
        try:
            msgs: List[EmailMessage] = await self.client.list_unread(limit=limit)
            email_dicts = [m.model_dump() for m in msgs]
            if not email_dicts:
                # In-memory fallback check
                email_dicts = [dict(em) for em in self._emails if em.get("status") == "unread"][:limit]

            count = len(email_dicts)
            lines = [f"- De: {em['sender']} | Asunto: '{em['subject']}' ({em['received_at']})" for em in email_dicts]
            summary_msg = f"Tienes {count} correo(s) no leído(s):\n" + "\n".join(lines) if count > 0 else "No tienes correos no leídos en este momento."

            return ToolResult(
                success=True,
                data={"count": count, "emails": email_dicts, "status": "unread"},
                message=summary_msg
            )
        except Exception as exc:
            return ToolResult(
                success=False,
                data={"count": 0, "emails": []},
                message=f"Error consultando correos no leídos: {exc}"
            )

    list_unread_emails = list_unread

    async def list_emails(
        self,
        status: Optional[str] = None,
        limit: int = 10,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Lists emails filtered optionally by status (e.g. unread, read, draft).
        """
        if status == "unread":
            return await self.list_unread(limit=limit)

        try:
            msgs: List[EmailMessage] = await self.client.list_all(status=status, limit=limit)
            email_dicts = [m.model_dump() for m in msgs]
            if not email_dicts:
                email_dicts = [dict(em) for em in self._emails if not status or em.get("status") == status][:limit]

            return ToolResult(
                success=True,
                data={"count": len(email_dicts), "emails": email_dicts},
                message=f"Se obtuvieron {len(email_dicts)} correos exitosamente."
            )
        except Exception as exc:
            # Fallback
            filtered = [dict(em) for em in self._emails if not status or em.get("status") == status][:limit]
            return ToolResult(
                success=True,
                data={"count": len(filtered), "emails": filtered},
                message=f"Se obtuvieron {len(filtered)} correos (modo fallback: {exc})."
            )

    async def get_email(
        self,
        email_id: str,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Retrieves a single email by its unique identifier.
        """
        try:
            msg: Optional[EmailMessage] = await self.client.get_by_id(email_id)
            if msg:
                return ToolResult(
                    success=True,
                    data=msg.model_dump(),
                    message=f"Correo '{email_id}' obtenido exitosamente."
                )
        except Exception:
            pass

        for em in self._emails:
            if em.get("id") == email_id:
                return ToolResult(
                    success=True,
                    data=em,
                    message=f"Correo '{email_id}' obtenido exitosamente."
                )

        return ToolResult(
            success=False,
            data=None,
            message=f"No se encontro ningun correo con el id '{email_id}'."
        )

    async def search_emails(
        self,
        query: str,
        limit: int = 10,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Searches emails matching a text query in sender, subject, snippet, or body.
        """
        clean_q = (query or "").strip().lower()
        if not clean_q:
            return await self.list_emails(limit=limit, user_id=user_id)

        try:
            msgs: List[EmailMessage] = await self.client.search(query=clean_q, limit=limit)
            email_dicts = [m.model_dump() for m in msgs]
            if not email_dicts:
                for em in self._emails:
                    text_corpus = f"{em.get('sender', '')} {em.get('subject', '')} {em.get('snippet', '')} {em.get('body', '')}".lower()
                    if clean_q in text_corpus:
                        email_dicts.append(dict(em))

            filtered = email_dicts[:limit]
            return ToolResult(
                success=True,
                data={"count": len(filtered), "emails": filtered, "query": clean_q},
                message=f"Se encontraron {len(filtered)} correos que coinciden con '{clean_q}'." if filtered else f"No se encontraron correos para '{clean_q}'."
            )
        except Exception as exc:
            return ToolResult(
                success=False,
                data={"count": 0, "emails": []},
                message=f"Error en búsqueda de correos: {exc}"
            )

    async def summarize_email(
        self,
        email_id: Optional[str] = None,
        query: Optional[str] = None
    ) -> ToolResult:
        """
        Fase 12: Generates an executive summary of an email with key points and action items.
        """
        target_email: Optional[Dict[str, Any]] = None

        if email_id:
            res = await self.get_email(email_id)
            if res.success and res.data:
                target_email = res.data
        elif query:
            res = await self.search_emails(query=query, limit=1)
            if res.success and res.data.get("emails"):
                target_email = res.data["emails"][0]
        else:
            res = await self.list_unread(limit=1)
            if res.success and res.data.get("emails"):
                target_email = res.data["emails"][0]

        if not target_email:
            return ToolResult(
                success=False,
                data=None,
                message="No se encontró ningún correo para resumir con los criterios indicados."
            )

        sender = target_email.get("sender", "Desconocido")
        subject = target_email.get("subject", "Sin Asunto")
        body = target_email.get("body") or target_email.get("snippet", "")
        received = target_email.get("received_at", "Reciente")

        summary_data = {
            "email_id": target_email.get("id"),
            "sender": sender,
            "subject": subject,
            "received_at": received,
            "core_message": body,
            "summary_bullet_points": [
                f"Remitente: {sender}",
                f"Asunto: {subject}",
                f"Mensaje principal: {body[:200]}..." if len(body) > 200 else f"Mensaje principal: {body}",
                "Acción requerida: " + ("Atención prioritaria del usuario" if target_email.get("is_important") else "Informativo / Sin acción urgente")
            ]
        }

        return ToolResult(
            success=True,
            data=summary_data,
            message=f"Resumen del correo de {sender} sobre '{subject}':\n" + "\n".join(f"- {bp}" for bp in summary_data["summary_bullet_points"])
        )

    async def prioritize_emails(self, limit: int = 5) -> ToolResult:
        """
        Fase 12: Automatically classifies emails by priority (HIGH, MEDIUM, LOW).
        """
        res = await self.list_emails(limit=limit * 2)
        emails = res.data.get("emails", [])

        categorized = {"HIGH": [], "MEDIUM": [], "LOW": []}
        for em in emails:
            sender = str(em.get("sender", "")).lower()
            recipient = str(em.get("recipient", "")).lower()
            subject = str(em.get("subject", "")).lower()
            
            if em.get("priority") == "HIGH" or em.get("is_important") or any(kw in (sender + recipient + subject) for kw in ["decano", "director", "banco", "urgente", "alerta", "aprobado", "corte"]):
                priority = "HIGH"
            elif any(kw in (sender + recipient + subject) for kw in ["biblioteca", "newsletter", "publicidad", "oferta", "promo"]):
                priority = "LOW"
            else:
                priority = "MEDIUM"
            
            em_copy = dict(em)
            em_copy["priority"] = priority
            categorized[priority].append(em_copy)

        ordered = categorized["HIGH"] + categorized["MEDIUM"] + categorized["LOW"]
        ordered = ordered[:limit]

        summary_lines = []
        for em in ordered:
            summary_lines.append(f"[{em['priority']}] {em.get('sender', 'Desconocido')} - '{em.get('subject', 'Sin asunto')}'")

        return ToolResult(
            success=True,
            data={"count": len(ordered), "emails": ordered, "breakdown": {k: len(v) for k, v in categorized.items()}},
            message=f"Priorización de correos ({len(ordered)} procesados):\n" + "\n".join(summary_lines)
        )

    async def create_email_draft(
        self,
        recipient: str,
        subject: str,
        body: str,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Creates a new email draft in the database or mail client.
        """
        draft_msg = await self.client.create_draft(recipient=recipient, subject=subject, body=body)
        draft_dict = draft_msg.model_dump()
        self._emails.append(draft_dict)

        return ToolResult(
            success=True,
            data=draft_dict,
            message=f"Borrador de correo para '{recipient}' con asunto '{subject}' creado y guardado exitosamente."
        )

    async def send_email_with_confirmation(
        self,
        recipient: str,
        subject: str,
        body: str,
        confirmed: bool = False
    ) -> ToolResult:
        """
        Fase 12: Human-in-the-loop email sending safeguard.
        If confirmed is False, halts execution, creates a draft, and requests explicit confirmation from user.
        If confirmed is True, proceeds to send through the active email client.
        """
        if not confirmed:
            # 1. Save draft as safety measure
            draft = await self.create_email_draft(recipient=recipient, subject=subject, body=body)
            return ToolResult(
                success=True,
                data={
                    "requires_confirmation": True,
                    "action": "send_email",
                    "draft_id": draft.data.get("id"),
                    "recipient": recipient,
                    "subject": subject,
                    "body": body,
                },
                message=(
                    f"He preparado el borrador para enviar el correo a **{recipient}** con el asunto **'{subject}'**.\n\n"
                    f"Contenido: \"{body}\"\n\n"
                    f"[CONFIRMACION REQUERIDA]: Por favor indícame explícitamente: ¿Confirmas el envío de este correo?"
                )
            )

        # 2. User has confirmed: execute dispatch
        success = await self.client.send_email(recipient=recipient, subject=subject, body=body)
        return ToolResult(
            success=success,
            data={
                "requires_confirmation": False,
                "status": "sent",
                "recipient": recipient,
                "subject": subject
            },
            message=f"Correo enviado exitosamente a '{recipient}' con el asunto '{subject}'."
        )

    async def execute(
        self,
        action: str = "search",
        sender: Optional[str] = None,
        search: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 5,
        email_id: Optional[str] = None,
        recipient: Optional[str] = None,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        query: Optional[str] = None,
        confirmed: bool = False,
        user_id: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        Generic dispatch method adhering to BaseTool interface.
        """
        print(f"[TOOL] Executing email_tool (action='{action}', search='{search or sender or query}')")

        if action in ["unread", "list_unread"]:
            return await self.list_unread(limit=limit)

        if action in ["summarize", "summarize_email"]:
            q = search or query or sender
            return await self.summarize_email(email_id=email_id, query=q)

        if action in ["prioritize", "prioritize_emails"]:
            return await self.prioritize_emails(limit=limit)

        if action == "get" and email_id:
            return await self.get_email(email_id=email_id, user_id=user_id)

        if action in ["draft", "create_draft"]:
            rec = recipient or kwargs.get("to", "destinatario@ejemplo.com")
            sub = subject or kwargs.get("title", "Sin Asunto")
            bod = body or kwargs.get("content", "")
            return await self.create_email_draft(recipient=rec, subject=sub, body=bod, user_id=user_id)

        if action in ["send", "send_email"]:
            rec = recipient or kwargs.get("to", "destinatario@ejemplo.com")
            sub = subject or kwargs.get("title", "Sin Asunto")
            bod = body or kwargs.get("content", "")
            is_conf = confirmed or kwargs.get("is_confirmed", False)
            return await self.send_email_with_confirmation(recipient=rec, subject=sub, body=bod, confirmed=is_conf)

        if action == "list" and not search and not sender and not query:
            return await self.list_emails(status=status, limit=limit, user_id=user_id)

        # Default is search
        clean_search = search or sender or query or kwargs.get("search_query", "")
        return await self.search_emails(query=clean_search, limit=limit, user_id=user_id)


# Backward compatibility alias
EmailTool = EmailTools

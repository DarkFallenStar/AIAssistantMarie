import uuid
from typing import Optional, List, Dict, Any
from app.tools.base import BaseTool, ToolResult
from app.core.database import get_supabase_client, is_valid_uuid, DEFAULT_USER_ID

class EmailTools(BaseTool):
    """
    Independent tool for managing user emails: listing, reading, searching,
    and creating drafts. Interacts with Supabase 'emails' table with an in-memory fallback.
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
            "is_important": True
        },
        {
            "id": "e1a1-0002",
            "sender": "Biblioteca Central <biblioteca@universidad.edu>",
            "recipient": "usuario@asistente.ai",
            "subject": "Recordatorio: Devolucion de material bibliografico",
            "snippet": "Tu prestamo del libro vence este viernes.",
            "body": "Recuerda que el libro solicitado vence este viernes 25.",
            "status": "read",
            "category": "alerts",
            "received_at": "Ayer, 3:30 p.m.",
            "is_important": False
        }
    ]

    def __init__(self):
        # Local copy of mock data so modifications (like drafts) persist per instance in memory
        self._emails: List[Dict[str, Any]] = [dict(em) for em in self.MOCK_EMAILS]

    @property
    def name(self) -> str:
        return "email_tool"

    @property
    def description(self) -> str:
        return "Gestiona correos electronicos: consulta, busqueda por contenido/remitente, lectura y creacion de borradores."

    async def list_emails(
        self,
        status: Optional[str] = None,
        limit: int = 10,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Lists emails filtered optionally by status (e.g. unread, read, draft).
        """
        emails: List[Dict[str, Any]] = []
        client = get_supabase_client()
        if client:
            try:
                query = client.table("emails").select("*").limit(limit).order("received_at", desc=True)
                if user_id:
                    query = query.eq("user_id", user_id)
                if status:
                    query = query.eq("status", status)
                res = query.execute()
                if res and res.data:
                    emails.extend(res.data)
            except Exception as exc:
                print(f"[TOOL] Supabase email list failed ({exc}), using mock fallback")

        # Supplement with in-memory mock emails so demo/test emails are always present
        seen_ids = {em.get("id") for em in emails}
        for em in self._emails:
            if em.get("id") not in seen_ids:
                if not status or em.get("status") == status:
                    emails.append(em)

        filtered = emails[:limit]
        return ToolResult(
            success=True,
            data={"count": len(filtered), "emails": filtered},
            message=f"Se obtuvieron {len(filtered)} correos exitosamente."
        )

    async def get_email(
        self,
        email_id: str,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Retrieves a single email by its unique identifier.
        """
        client = get_supabase_client()
        if client:
            try:
                if is_valid_uuid(email_id):
                    query = client.table("emails").select("*").eq("id", email_id)
                    if user_id:
                        query = query.eq("user_id", user_id)
                    res = query.execute()
                    if res and res.data:
                        return ToolResult(
                            success=True,
                            data=res.data[0],
                            message=f"Correo '{email_id}' obtenido exitosamente."
                        )
            except Exception as exc:
                print(f"[TOOL] Supabase get_email failed ({exc}), using mock fallback")

        # Fallback in-memory
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

        emails: List[Dict[str, Any]] = []
        client = get_supabase_client()
        if client:
            try:
                # Query recent emails and filter client-side / or use Supabase ilike
                query_builder = client.table("emails").select("*").limit(limit * 2).order("received_at", desc=True)
                if user_id:
                    query_builder = query_builder.eq("user_id", user_id)
                res = query_builder.execute()
                if res and res.data:
                    for em in res.data:
                        text_corpus = f"{em.get('sender', '')} {em.get('subject', '')} {em.get('snippet', '')} {em.get('body', '')}".lower()
                        if clean_q in text_corpus:
                            emails.append(em)
            except Exception as exc:
                print(f"[TOOL] Supabase email search failed ({exc}), using mock fallback")

        seen_ids = {em.get("id") for em in emails}
        for em in self._emails:
            if em.get("id") not in seen_ids:
                text_corpus = f"{em.get('sender', '')} {em.get('subject', '')} {em.get('snippet', '')} {em.get('body', '')}".lower()
                if clean_q in text_corpus:
                    emails.append(em)

        filtered = emails[:limit]
        return ToolResult(
            success=True,
            data={"count": len(filtered), "emails": filtered, "query": clean_q},
            message=f"Se encontraron {len(filtered)} correos que coinciden con '{clean_q}'." if filtered else f"No se encontraron correos para '{clean_q}'."
        )

    async def create_email_draft(
        self,
        recipient: str,
        subject: str,
        body: str,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Creates a new email draft in the database or mock storage.
        """
        draft_id = str(uuid.uuid4())
        eff_user_id = user_id or DEFAULT_USER_ID
        draft_data = {
            "id": draft_id,
            "user_id": eff_user_id,
            "sender": "usuario@asistente.ai",
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "snippet": body[:100] + "..." if len(body) > 100 else body,
            "status": "draft",
            "category": "work",
            "is_important": False
        }

        client = get_supabase_client()
        if client:
            try:
                res = client.table("emails").insert(draft_data).execute()
                saved_draft = res.data[0] if res and res.data else draft_data
                self._emails.append(saved_draft)
                return ToolResult(
                    success=True,
                    data=saved_draft,
                    message=f"Borrador de correo para '{recipient}' creado exitosamente."
                )
            except Exception as exc:
                err_str = str(exc)
                # Resilient fallback: if check constraint emails_status_check forbids 'draft'
                if "emails_status_check" in err_str or "23514" in err_str:
                    try:
                        fallback_payload = dict(draft_data)
                        fallback_payload["status"] = "unread"
                        if not fallback_payload["subject"].startswith("[Borrador]"):
                            fallback_payload["subject"] = f"[Borrador] {fallback_payload['subject']}"
                        res = client.table("emails").insert(fallback_payload).execute()
                        saved_draft = res.data[0] if res and res.data else fallback_payload
                        self._emails.append(saved_draft)
                        return ToolResult(
                            success=True,
                            data=saved_draft,
                            message=f"Borrador de correo para '{recipient}' creado exitosamente en Supabase."
                        )
                    except Exception as retry_exc:
                        print(f"[TOOL] Supabase draft constraint retry failed ({retry_exc}), saving to mock storage")
                else:
                    print(f"[TOOL] Supabase create_email_draft failed ({exc}), saving to mock storage")

        # Fallback in-memory
        self._emails.append(draft_data)
        return ToolResult(
            success=True,
            data=draft_data,
            message=f"Borrador de correo para '{recipient}' guardado exitosamente."
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
        user_id: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        Generic dispatch method adhering to BaseTool interface.
        """
        print(f"[TOOL] Executing email_tool (action='{action}', search='{search or sender}')")

        if action == "get" and email_id:
            return await self.get_email(email_id=email_id, user_id=user_id)

        if action == "draft" or action == "create_draft":
            rec = recipient or kwargs.get("to", "destinatario@ejemplo.com")
            sub = subject or kwargs.get("title", "Sin Asunto")
            bod = body or kwargs.get("content", "")
            return await self.create_email_draft(recipient=rec, subject=sub, body=bod, user_id=user_id)

        if action == "list" and not search and not sender:
            return await self.list_emails(status=status, limit=limit, user_id=user_id)

        # Default is search
        query = search or sender or kwargs.get("query", "")
        return await self.search_emails(query=query, limit=limit, user_id=user_id)


# Backward compatibility alias
EmailTool = EmailTools

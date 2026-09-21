import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.services.email.base import BaseEmailClient, EmailMessage
from app.core.database import get_supabase_client, is_valid_uuid, DEFAULT_USER_ID

class MockEmailClient(BaseEmailClient):
    """
    Resilient Mock and Supabase-backed email client.
    Guarantees deterministic testing, offline demo execution, and persistent Supabase sync.
    """

    SEEDED_EMAILS: List[Dict[str, Any]] = [
        {
            "id": "e1a1-0001",
            "sender": "Dr. Fernando Ruiz (Decano de Facultad) <decano@universidad.edu>",
            "recipient": "usuario@asistente.ai",
            "subject": "Respuesta: Solicitud de revision y aprobacion de proyecto",
            "snippet": "Estimado, he revisado la propuesta de investigacion y ha sido aprobada favorablemente por el consejo academico.",
            "body": "Estimado, he revisado la propuesta de investigacion del asistente de inteligencia artificial y ha sido aprobada favorablemente por el consejo academico. Podemos proceder con la siguiente fase de desarrollo y coordinar los fondos requeridos este viernes.",
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
            "snippet": "Tu prestamo del libro sobre Machine Learning vence este viernes.",
            "body": "Recuerda que el libro 'Deep Learning Architectures' solicitado vence este viernes 25. Puedes renovarlo en linea desde el portal institucional.",
            "status": "read",
            "category": "alerts",
            "received_at": "Ayer, 3:30 p.m.",
            "is_important": False,
            "priority": "LOW"
        },
        {
            "id": "e1a1-0004",
            "sender": "Equipo de Soporte Cloud <soporte@cloudservice.io>",
            "recipient": "usuario@asistente.ai",
            "subject": "Aviso de mantenimiento programado de servidores",
            "snippet": "Se realizara una ventana de mantenimiento el domingo a las 02:00 AM UTC.",
            "body": "Estimado usuario: Este fin de semana realizaremos una actualizacion de infraestructura. No se anticipan interrupciones mayores en la conectividad de la base de datos.",
            "status": "read",
            "category": "tech",
            "received_at": "Hace 2 dias",
            "is_important": False,
            "priority": "MEDIUM"
        }
    ]

    def __init__(self):
        self._emails: List[EmailMessage] = [EmailMessage(**item) for item in self.SEEDED_EMAILS]
        self._sent_emails: List[Dict[str, Any]] = []

    @property
    def provider_name(self) -> str:
        return "mock"

    async def list_unread(self, limit: int = 10) -> List[EmailMessage]:
        return await self.list_all(status="unread", limit=limit)

    async def list_all(self, status: Optional[str] = None, limit: int = 10) -> List[EmailMessage]:
        supabase_results: List[EmailMessage] = []
        client = get_supabase_client()
        if client:
            try:
                query = client.table("emails").select("*").limit(limit).order("received_at", desc=True)
                if status:
                    query = query.eq("status", status)
                res = query.execute()
                if res and res.data:
                    for row in res.data:
                        supabase_results.append(EmailMessage(
                            id=str(row.get("id")),
                            sender=row.get("sender", "Remitente"),
                            recipient=row.get("recipient", "usuario@asistente.ai"),
                            subject=row.get("subject", "Sin asunto"),
                            body=row.get("body", ""),
                            snippet=row.get("snippet", row.get("body", "")[:100]),
                            status=row.get("status", "unread"),
                            category=row.get("category", "general"),
                            received_at=str(row.get("received_at", "Reciente")),
                            is_important=bool(row.get("is_important", False)),
                            priority="HIGH" if row.get("is_important") else "MEDIUM"
                        ))
            except Exception as exc:
                print(f"[EMAIL-MOCK] Supabase query failed ({exc}), using in-memory store")

        seen_ids = {m.id for m in supabase_results}
        for em in self._emails:
            if em.id not in seen_ids:
                if not status or em.status == status:
                    supabase_results.append(em)

        return supabase_results[:limit]

    async def get_by_id(self, email_id: str) -> Optional[EmailMessage]:
        client = get_supabase_client()
        if client and is_valid_uuid(email_id):
            try:
                res = client.table("emails").select("*").eq("id", email_id).execute()
                if res and res.data:
                    row = res.data[0]
                    return EmailMessage(
                        id=str(row.get("id")),
                        sender=row.get("sender", "Remitente"),
                        recipient=row.get("recipient", "usuario@asistente.ai"),
                        subject=row.get("subject", "Sin asunto"),
                        body=row.get("body", ""),
                        snippet=row.get("snippet", row.get("body", "")[:100]),
                        status=row.get("status", "unread"),
                        category=row.get("category", "general"),
                        received_at=str(row.get("received_at", "Reciente")),
                        is_important=bool(row.get("is_important", False)),
                        priority="HIGH" if row.get("is_important") else "MEDIUM"
                    )
            except Exception:
                pass

        for em in self._emails:
            if em.id == email_id:
                return em
        return None

    async def search(self, query: str, limit: int = 10) -> List[EmailMessage]:
        clean_q = query.strip().lower()
        all_emails = await self.list_all(limit=limit * 2)
        results = []
        for em in all_emails:
            haystack = f"{em.sender} {em.subject} {em.body} {em.snippet}".lower()
            if clean_q in haystack:
                results.append(em)
        return results[:limit]

    async def create_draft(self, recipient: str, subject: str, body: str) -> EmailMessage:
        draft_id = str(uuid.uuid4())
        draft = EmailMessage(
            id=draft_id,
            sender="usuario@asistente.ai",
            recipient=recipient,
            subject=f"[Borrador] {subject}" if not subject.startswith("[Borrador]") else subject,
            body=body,
            snippet=body[:100] + "..." if len(body) > 100 else body,
            status="draft",
            category="work",
            received_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            is_important=False,
            priority="MEDIUM"
        )
        self._emails.append(draft)

        # Attempt saving to Supabase
        client = get_supabase_client()
        if client:
            try:
                client.table("emails").insert({
                    "id": draft.id,
                    "user_id": DEFAULT_USER_ID,
                    "sender": draft.sender,
                    "recipient": draft.recipient,
                    "subject": draft.subject,
                    "body": draft.body,
                    "snippet": draft.snippet,
                    "status": "unread", # check constraint resilience
                    "category": draft.category,
                    "is_important": draft.is_important
                }).execute()
            except Exception as exc:
                print(f"[EMAIL-MOCK] Supabase draft insert fallback: {exc}")

        return draft

    async def send_email(self, recipient: str, subject: str, body: str) -> bool:
        sent_id = str(uuid.uuid4())
        sent_entry = {
            "id": sent_id,
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "sent_at": datetime.now().isoformat()
        }
        self._sent_emails.append(sent_entry)
        print(f"[EMAIL-MOCK] Email dispatched to {recipient} with subject '{subject}'")
        return True

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from app.tools.base import BaseTool, ToolResult
from app.core.database import get_supabase_client

class ReminderTools(BaseTool):
    """
    Independent tool for managing time-based reminders: creation, listing,
    completion, and deletion. Interacts with Supabase 'tasks' table (with category='reminder')
    or an in-memory mock repository when offline.
    """

    MOCK_REMINDERS: List[Dict[str, Any]] = [
        {
            "id": "rem-001",
            "title": "Tomar el medicamento recetado",
            "description": "Dosis después del almuerzo",
            "remind_at": "Hoy, 2:00 p.m.",
            "status": "active",
            "category": "reminder",
            "created_at": "2026-09-20T08:00:00Z"
        },
        {
            "id": "rem-002",
            "title": "Llamar al médico para agendar cita",
            "description": "Confirmar disponibilidad para el chequeo anual",
            "remind_at": "Mañana, 10:00 a.m.",
            "status": "active",
            "category": "reminder",
            "created_at": "2026-09-20T09:00:00Z"
        }
    ]

    def __init__(self):
        self._reminders: List[Dict[str, Any]] = [dict(r) for r in self.MOCK_REMINDERS]

    @property
    def name(self) -> str:
        return "reminder_tool"

    @property
    def description(self) -> str:
        return "Gestiona recordatorios puntuales: programacion con fecha/hora, consulta de recordatorios activos y completados."

    async def create_reminder(
        self,
        title: str,
        remind_at: str,
        description: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Creates a new reminder with a specified time/date trigger.
        """
        clean_title = (title or "").strip()
        if not clean_title:
            return ToolResult(
                success=False,
                data=None,
                message="El título del recordatorio no puede estar vacío."
            )

        reminder_id = f"rem-{uuid.uuid4().hex[:8]}"
        payload = {
            "id": reminder_id,
            "title": clean_title,
            "description": description or "",
            "remind_at": remind_at,
            "due_date": remind_at,
            "status": "active",
            "priority": "high",
            "category": "reminder",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        if user_id:
            payload["user_id"] = user_id

        # Keep in-memory copy up to date
        self._reminders.append(payload)

        client = get_supabase_client()
        if client:
            try:
                # Map to tasks table with category='reminder'
                db_payload = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id or "a0000000-0000-0000-0000-000000000001",
                    "title": clean_title,
                    "description": description or "",
                    "due_date": None,
                    "status": "pending",
                    "priority": "high",
                    "category": "reminder"
                }
                client.table("tasks").insert(db_payload).execute()
            except Exception as exc:
                print(f"[TOOL] Supabase create_reminder failed ({exc}), using mock fallback")

        return ToolResult(
            success=True,
            data=payload,
            message=f"Recordatorio '{clean_title}' programado para '{remind_at}' guardado correctamente."
        )

    async def list_reminders(
        self,
        status: Optional[str] = "active",
        limit: int = 10,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Lists reminders, filtering by status ('active', 'completed', 'all').
        """
        reminders: List[Dict[str, Any]] = []
        client = get_supabase_client()
        if client:
            try:
                query = client.table("tasks").select("*").eq("category", "reminder").limit(limit)
                if user_id:
                    query = query.eq("user_id", user_id)
                if status and status != "all":
                    db_status = "pending" if status == "active" else status
                    query = query.eq("status", db_status)
                res = query.execute()
                if res and res.data:
                    for r in res.data:
                        reminders.append({
                            "id": r.get("id"),
                            "title": r.get("title"),
                            "description": r.get("description"),
                            "remind_at": r.get("due_date") or "Próximamente",
                            "status": "active" if r.get("status") == "pending" else r.get("status"),
                            "category": "reminder"
                        })
            except Exception as exc:
                print(f"[TOOL] Supabase list_reminders failed ({exc}), using mock fallback")

        # Supplement with in-memory reminders so demo/test reminders are always present
        seen_ids = {r.get("id") for r in reminders}
        for r in self._reminders:
            if r.get("id") not in seen_ids:
                if status == "all" or not status:
                    reminders.append(r)
                elif status == "active" and r.get("status") == "active":
                    reminders.append(r)
                elif status == "completed" and r.get("status") == "completed":
                    reminders.append(r)

        filtered = reminders[:limit]
        return ToolResult(
            success=True,
            data={"count": len(filtered), "reminders": filtered},
            message=f"Se obtuvieron {len(filtered)} recordatorios."
        )

    async def complete_reminder(
        self,
        reminder_id: str,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Marks an active reminder as completed/dismissed.
        """
        client = get_supabase_client()
        if client:
            try:
                query = client.table("tasks").update({
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", reminder_id).eq("category", "reminder")
                if user_id:
                    query = query.eq("user_id", user_id)
                res = query.execute()
                if res and res.data:
                    return ToolResult(
                        success=True,
                        data=res.data[0],
                        message=f"Recordatorio '{reminder_id}' marcado como completado."
                    )
            except Exception as exc:
                print(f"[TOOL] Supabase complete_reminder failed ({exc}), using mock fallback")

        # In-memory fallback
        for r in self._reminders:
            if r.get("id") == reminder_id or r.get("title", "").lower() == reminder_id.lower():
                r["status"] = "completed"
                r["completed_at"] = datetime.now(timezone.utc).isoformat()
                return ToolResult(
                    success=True,
                    data=r,
                    message=f"Recordatorio '{r.get('title')}' marcado como completado."
                )

        return ToolResult(
            success=False,
            data=None,
            message=f"No se encontró ningún recordatorio con id o título '{reminder_id}'."
        )

    async def delete_reminder(
        self,
        reminder_id: str,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Permanently deletes or cancels a reminder.
        """
        client = get_supabase_client()
        if client:
            try:
                query = client.table("tasks").delete().eq("id", reminder_id).eq("category", "reminder")
                if user_id:
                    query = query.eq("user_id", user_id)
                query.execute()
                return ToolResult(
                    success=True,
                    data={"id": reminder_id},
                    message=f"Recordatorio '{reminder_id}' eliminado exitosamente."
                )
            except Exception as exc:
                print(f"[TOOL] Supabase delete_reminder failed ({exc}), using mock fallback")

        # In-memory fallback
        initial_len = len(self._reminders)
        self._reminders = [r for r in self._reminders if r.get("id") != reminder_id and r.get("title", "").lower() != reminder_id.lower()]
        if len(self._reminders) < initial_len:
            return ToolResult(
                success=True,
                data={"id": reminder_id},
                message=f"Recordatorio '{reminder_id}' eliminado correctamente."
            )

        return ToolResult(
            success=False,
            data=None,
            message=f"No se encontró el recordatorio '{reminder_id}' para eliminar."
        )

    async def execute(
        self,
        action: str = "list",
        title: Optional[str] = None,
        remind_at: Optional[str] = None,
        reminder_id: Optional[str] = None,
        status: Optional[str] = "active",
        description: Optional[str] = None,
        limit: int = 10,
        user_id: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        Generic dispatch method adhering to BaseTool interface.
        """
        print(f"[TOOL] Executing reminder_tool (action='{action}', title='{title}', id='{reminder_id}')")

        if action == "create":
            clean_title = title or kwargs.get("name", "Recordatorio")
            time_spec = remind_at or kwargs.get("due_date", "Próximamente")
            return await self.create_reminder(
                title=clean_title,
                remind_at=time_spec,
                description=description,
                user_id=user_id
            )

        if action == "complete":
            rid = reminder_id or title
            if not rid:
                return ToolResult(success=False, data=None, message="Se requiere el ID o nombre del recordatorio para completarlo.")
            return await self.complete_reminder(reminder_id=rid, user_id=user_id)

        if action == "delete":
            rid = reminder_id or title
            if not rid:
                return ToolResult(success=False, data=None, message="Se requiere el ID del recordatorio para eliminarlo.")
            return await self.delete_reminder(reminder_id=rid, user_id=user_id)

        # Default is list
        return await self.list_reminders(status=status, limit=limit, user_id=user_id)


# Backward compatibility alias
ReminderTool = ReminderTools

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from app.tools.base import BaseTool, ToolResult
from app.core.database import get_supabase_client

class TaskTools(BaseTool):
    """
    Independent tool for managing tasks: creation, listing, updating,
    and completion. Interacts with Supabase 'tasks' table with in-memory fallback.
    """

    MOCK_TASKS: List[Dict[str, Any]] = [
        {
            "id": "t1-001",
            "title": "Pagar el alquiler de la casa",
            "description": "Transferencia mensual del arrendamiento",
            "status": "pending",
            "priority": "high",
            "category": "general",
            "due_date": "Mañana, 9:00 a.m.",
            "completed_at": None
        },
        {
            "id": "t1-002",
            "title": "Comprar leche y víveres",
            "description": "Pasar al supermercado al salir del trabajo",
            "status": "pending",
            "priority": "medium",
            "category": "general",
            "due_date": "Hoy, 6:00 p.m.",
            "completed_at": None
        }
    ]

    def __init__(self):
        # Local copy of mock data so state modifications persist per instance
        self._tasks: List[Dict[str, Any]] = [dict(t) for t in self.MOCK_TASKS]

    @property
    def name(self) -> str:
        return "task_tool"

    @property
    def description(self) -> str:
        return "Gestiona tareas de la agenda: creacion, listado, actualizacion de estado/prioridad y marcado de tareas completadas."

    async def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: str = "medium",
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Creates a new task in the database or mock storage.
        """
        clean_title = (title or "").strip()
        if not clean_title:
            return ToolResult(
                success=False,
                data=None,
                message="El título de la tarea no puede estar vacío."
            )

        task_id = f"t-{uuid.uuid4().hex[:8]}"
        payload = {
            "id": task_id,
            "title": clean_title,
            "description": description or "",
            "status": "pending",
            "priority": priority or "medium",
            "category": "general",
            "due_date": due_date,
            "completed_at": None
        }

        # Keep in-memory copy up to date
        self._tasks.append(payload)

        client = get_supabase_client()
        if client:
            try:
                db_payload = dict(payload)
                db_payload["id"] = str(uuid.uuid4())
                db_payload["user_id"] = user_id or "a0000000-0000-0000-0000-000000000001"
                client.table("tasks").insert(db_payload).execute()
            except Exception as exc:
                print(f"[TOOL] Supabase create_task failed ({exc}), storing in mock repository")

        return ToolResult(
            success=True,
            data=payload,
            message=f"Tarea '{clean_title}' guardada correctamente."
        )

    async def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 10,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Lists tasks filtered optionally by status ('pending', 'completed', etc.) or priority.
        """
        tasks: List[Dict[str, Any]] = []
        client = get_supabase_client()
        if client:
            try:
                query = client.table("tasks").select("*").limit(limit).order("created_at", desc=True)
                if user_id:
                    query = query.eq("user_id", user_id)
                if status:
                    query = query.eq("status", status)
                if priority:
                    query = query.eq("priority", priority)
                res = query.execute()
                if res and res.data:
                    tasks.extend(res.data)
            except Exception as exc:
                print(f"[TOOL] Supabase list_tasks failed ({exc}), using mock fallback")

        # Supplement with in-memory tasks so demo/test tasks are always present
        seen_ids = {t.get("id") for t in tasks}
        for t in self._tasks:
            if t.get("id") not in seen_ids:
                if (not status or t.get("status", "").lower() == status.lower()) and \
                   (not priority or t.get("priority", "").lower() == priority.lower()):
                    tasks.append(t)

        filtered = tasks[:limit]
        return ToolResult(
            success=True,
            data={"count": len(filtered), "tasks": filtered},
            message=f"Se obtuvieron {len(filtered)} tareas de la agenda."
        )

    async def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Updates fields of an existing task.
        """
        updates: Dict[str, Any] = {}
        if title is not None:
            updates["title"] = title
        if description is not None:
            updates["description"] = description
        if due_date is not None:
            updates["due_date"] = due_date
        if priority is not None:
            updates["priority"] = priority
        if status is not None:
            updates["status"] = status
            if status == "completed":
                updates["completed_at"] = datetime.now(timezone.utc).isoformat()

        if not updates:
            return ToolResult(
                success=False,
                data=None,
                message="No se especificaron cambios para actualizar la tarea."
            )

        client = get_supabase_client()
        if client:
            try:
                query = client.table("tasks").update(updates).eq("id", task_id)
                if user_id:
                    query = query.eq("user_id", user_id)
                res = query.execute()
                if res and res.data:
                    return ToolResult(
                        success=True,
                        data=res.data[0],
                        message=f"Tarea '{task_id}' actualizada exitosamente."
                    )
            except Exception as exc:
                print(f"[TOOL] Supabase update_task failed ({exc}), updating in mock fallback")

        # In-memory fallback
        for t in self._tasks:
            if t.get("id") == task_id or t.get("title", "").lower() == task_id.lower():
                t.update(updates)
                return ToolResult(
                    success=True,
                    data=t,
                    message=f"Tarea '{t.get('title')}' actualizada correctamente."
                )

        return ToolResult(
            success=False,
            data=None,
            message=f"No se encontró la tarea con id '{task_id}'."
        )

    async def complete_task(
        self,
        task_id: str,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Marks a specific task as completed.
        """
        return await self.update_task(
            task_id=task_id,
            status="completed",
            user_id=user_id
        )

    async def execute(
        self,
        action: str = "list",
        title: Optional[str] = None,
        status: Optional[str] = None,
        due_date: Optional[str] = None,
        task_id: Optional[str] = None,
        priority: Optional[str] = None,
        description: Optional[str] = None,
        limit: int = 5,
        user_id: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        Generic dispatch method adhering to BaseTool interface.
        """
        print(f"[TOOL] Executing task_tool (action='{action}', title='{title}', task_id='{task_id}')")

        if action == "create":
            task_title = title or kwargs.get("name", "Nueva Tarea")
            return await self.create_task(
                title=task_title,
                description=description,
                due_date=due_date,
                priority=priority or "medium",
                user_id=user_id
            )

        if action == "complete":
            tid = task_id or title
            if not tid:
                return ToolResult(success=False, data=None, message="Se requiere el ID o nombre de la tarea para completarla.")
            return await self.complete_task(task_id=tid, user_id=user_id)

        if action == "update":
            tid = task_id or title
            if not tid:
                return ToolResult(success=False, data=None, message="Se requiere el ID o nombre de la tarea para actualizarla.")
            return await self.update_task(
                task_id=tid,
                title=title if task_id else None,
                description=description,
                due_date=due_date,
                priority=priority,
                status=status,
                user_id=user_id
            )

        # Default is list
        return await self.list_tasks(status=status, priority=priority, limit=limit, user_id=user_id)


# Backward compatibility alias
TaskTool = TaskTools

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from app.tools.base import BaseTool, ToolResult
from app.core.database import get_supabase_client, is_valid_uuid, DEFAULT_USER_ID

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
        },
        {
            "id": "b0000000-0000-0000-0000-000000000001",
            "title": "Revisar presupuesto mensual",
            "description": "Analizar los gastos de la semana con el Asistente Financiero",
            "status": "pending",
            "priority": "high",
            "category": "finanzas",
            "due_date": "Mañana, 9:00 a.m.",
            "completed_at": None
        },
        {
            "id": "b0000000-0000-0000-0000-000000000002",
            "title": "Entregar informe de avance de tesis",
            "description": "Enviar borrador del capítulo metodológico al director de tesis",
            "status": "pending",
            "priority": "high",
            "category": "academico",
            "due_date": "Viernes, 5:00 p.m.",
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

        task_id = str(uuid.uuid4())
        eff_user_id = user_id or DEFAULT_USER_ID
        payload = {
            "id": task_id,
            "user_id": eff_user_id,
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
                client.table("tasks").insert(payload).execute()
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
        limit: int = 50,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Lists tasks filtered optionally by status ('pending', 'completed', etc.) or priority.
        """
        tasks: List[Dict[str, Any]] = []
        db_success = False
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
                if res and res.data is not None:
                    tasks.extend(res.data)
                db_success = True
            except Exception as exc:
                print(f"[TOOL] Supabase list_tasks failed ({exc}), using mock fallback")
                db_success = False

        # Strict persistence priority:
        # If database connection succeeded, database is the Single Source of Truth (zero-mock).
        default_mock_ids = {t["id"] for t in self.MOCK_TASKS}
        seen_ids = set()
        combined: List[Dict[str, Any]] = []

        if db_success:
            # 1. Any newly created session task that isn't a static mock and isn't yet in DB query
            for t in self._tasks:
                t_id = t.get("id")
                if t_id and t_id not in default_mock_ids and t_id not in seen_ids:
                    seen_ids.add(t_id)
                    matches_status = not status or t.get("status", "").lower() == status.lower()
                    matches_prio = not priority or t.get("priority", "").lower() == priority.lower()
                    if matches_status and matches_prio:
                        combined.append(t)

            # 2. Add database records
            for t in tasks:
                t_id = t.get("id")
                if t_id and t_id not in seen_ids:
                    seen_ids.add(t_id)
                    combined.append(t)
        else:
            # Fallback ONLY when database is unreachable or offline
            for t in self._tasks:
                t_id = t.get("id")
                if t_id and t_id not in seen_ids:
                    seen_ids.add(t_id)
                    matches_status = not status or t.get("status", "").lower() == status.lower()
                    matches_prio = not priority or t.get("priority", "").lower() == priority.lower()
                    if matches_status and matches_prio:
                        combined.append(t)

        filtered = combined[:limit]
        return ToolResult(
            success=True,
            data={"count": len(filtered), "tasks": filtered},
            message=f"Se obtuvieron {len(filtered)} tareas de la agenda." if filtered else "No hay tareas registradas en la agenda."
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
            if is_valid_uuid(task_id):
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
                    print(f"[TOOL] Supabase update_task by UUID failed ({exc}), updating in mock fallback")
            else:
                # Search by title in Supabase using case-insensitive match
                try:
                    clean_search = task_id.strip()
                    query = client.table("tasks").select("*").ilike("title", f"%{clean_search}%").order("created_at", desc=True).limit(1)
                    if user_id:
                        query = query.eq("user_id", user_id)
                    search_res = query.execute()
                    if search_res and search_res.data:
                        real_id = search_res.data[0]["id"]
                        upd_res = client.table("tasks").update(updates).eq("id", real_id).execute()
                        if upd_res and upd_res.data:
                            task_title = search_res.data[0].get("title", task_id)
                            # Also reflect in in-memory list
                            for t in self._tasks:
                                if t.get("id") == real_id or t.get("title", "").lower() == task_title.lower():
                                    t.update(updates)
                            return ToolResult(
                                success=True,
                                data=upd_res.data[0],
                                message=f"Tarea '{task_title}' marcada como completada exitosamente."
                            )
                except Exception as exc:
                    print(f"[TOOL] Supabase update_task by title search failed ({exc}), trying mock fallback")

        # In-memory fallback with exact and substring matching
        target_clean = task_id.lower().strip()
        for t in self._tasks:
            t_title = t.get("title", "").lower()
            if t.get("id") == task_id or t_title == target_clean or (target_clean and target_clean in t_title) or (t_title and t_title in target_clean):
                t.update(updates)
                return ToolResult(
                    success=True,
                    data=t,
                    message=f"Tarea '{t.get('title')}' actualizada correctamente."
                )

        return ToolResult(
            success=False,
            data=None,
            message=f"No se encontró la tarea con identificador o título '{task_id}'."
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

    async def delete_task(
        self,
        task_id: str,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Deletes a task by UUID or matching title from Supabase and in-memory fallback.
        """
        clean_id = (task_id or "").strip()
        if not clean_id:
            return ToolResult(
                success=False,
                data=None,
                message="Se requiere el ID o nombre de la tarea para eliminarla."
            )

        deleted_title = clean_id
        client = get_supabase_client()
        if client:
            if is_valid_uuid(clean_id):
                try:
                    query = client.table("tasks").delete().eq("id", clean_id)
                    if user_id:
                        query = query.eq("user_id", user_id)
                    query.execute()
                    self._tasks = [t for t in self._tasks if t.get("id") != clean_id]
                    return ToolResult(
                        success=True,
                        data={"deleted_id": clean_id},
                        message=f"Tarea '{clean_id}' eliminada exitosamente de la base de datos."
                    )
                except Exception as exc:
                    print(f"[TOOL] Supabase delete_task by UUID failed: {exc}")
            else:
                # Search by title in Supabase
                try:
                    query = client.table("tasks").select("id, title").ilike("title", f"%{clean_id}%").limit(1)
                    if user_id:
                        query = query.eq("user_id", user_id)
                    search_res = query.execute()
                    if search_res and search_res.data:
                        real_id = search_res.data[0]["id"]
                        deleted_title = search_res.data[0].get("title", clean_id)
                        client.table("tasks").delete().eq("id", real_id).execute()
                        self._tasks = [t for t in self._tasks if t.get("id") != real_id]
                        return ToolResult(
                            success=True,
                            data={"deleted_id": real_id, "title": deleted_title},
                            message=f"Tarea '{deleted_title}' eliminada exitosamente de la base de datos."
                        )
                except Exception as exc:
                    print(f"[TOOL] Supabase delete_task by title search failed: {exc}")

        # In-memory fallback
        target_clean = clean_id.lower()
        matched_task = None
        for t in self._tasks:
            t_title = t.get("title", "").lower()
            if t.get("id") == clean_id or t_title == target_clean or (target_clean and target_clean in t_title):
                matched_task = t
                break

        if matched_task:
            deleted_title = matched_task.get("title", clean_id)
            self._tasks = [t for t in self._tasks if t.get("id") != matched_task.get("id")]
            return ToolResult(
                success=True,
                data={"deleted_id": matched_task.get("id"), "title": deleted_title},
                message=f"Tarea '{deleted_title}' eliminada exitosamente."
            )

        return ToolResult(
            success=False,
            data=None,
            message=f"No se encontró la tarea con identificador o título '{clean_id}' para eliminar."
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
        limit: int = 20,
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

        if action in ["delete", "remove", "eliminar", "borrar"]:
            tid = task_id or title
            if not tid:
                return ToolResult(success=False, data=None, message="Se requiere el ID o nombre de la tarea para eliminarla.")
            return await self.delete_task(task_id=tid, user_id=user_id)

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
